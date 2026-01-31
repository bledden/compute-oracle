"""
News sentiment source — scrapes tech/energy headlines via Browserbase Stagehand
and classifies them as bullish/bearish/neutral for GPU compute pricing.

Uses the Stagehand Python SDK for AI-powered browser automation.
Falls back to hardcoded sample headlines when Browserbase credentials
are not configured, so the demo always works.
"""

import asyncio
import random
from datetime import datetime, timezone, timedelta
from typing import Any
import weave

from ingestion.base_source import BaseSignalSource
from core.redis_client import get_redis
from config import get_settings

# ---------------------------------------------------------------------------
# Keyword dictionaries for simple sentiment classification
# ---------------------------------------------------------------------------

BULLISH_KEYWORDS = [
    # Supply constraints / demand surges -> prices go UP
    "shortage", "supply chain", "constraint", "bottleneck", "sold out",
    "allocation", "limited supply", "backorder", "export ban", "tariff",
    "sanctions", "demand surge", "record demand", "capacity crunch",
    "power outage", "grid strain", "heat wave", "drought", "blackout",
    "data center boom", "hyperscaler", "ai demand", "gpu shortage",
    "chip shortage", "wafer shortage", "tsmc", "nvidia earnings beat",
    "price hike", "price increase", "rate hike", "energy crisis",
    "natural gas surge", "oil spike", "electricity price",
    "nuclear shutdown", "plant closure", "fab delay",
]

BEARISH_KEYWORDS = [
    # Supply expansion / demand drops -> prices go DOWN
    "new fab", "fab opening", "capacity expansion", "new data center",
    "price cut", "price drop", "surplus", "oversupply", "glut",
    "efficiency gain", "breakthrough", "renewable energy", "solar",
    "wind power", "cheap energy", "nuclear restart", "rate cut",
    "demand decline", "slowdown", "recession", "layoffs",
    "open source model", "smaller model", "efficiency", "distillation",
    "new gpu launch", "increased production", "inventory build",
    "cool weather", "mild winter", "gas prices fall",
]

# ---------------------------------------------------------------------------
# Target news sites — each entry is (url, extraction instruction)
# ---------------------------------------------------------------------------

NEWS_TARGETS = [
    (
        "https://www.reuters.com/technology/",
        "Extract all visible article headlines from the page. "
        "Return them as a JSON array of objects with 'title' (string) "
        "and 'source' (always 'Reuters').",
    ),
    (
        "https://techcrunch.com/category/cloud/",
        "Extract all visible article headlines from the page. "
        "Return them as a JSON array of objects with 'title' (string) "
        "and 'source' (always 'TechCrunch').",
    ),
    (
        "https://www.datacenterdynamics.com/en/news/",
        "Extract all visible article headlines from the page. "
        "Return them as a JSON array of objects with 'title' (string) "
        "and 'source' (always 'DatacenterDynamics').",
    ),
]

# Schema used for Stagehand extract() calls
HEADLINES_SCHEMA = {
    "type": "object",
    "properties": {
        "headlines": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "source": {"type": "string"},
                },
                "required": ["title", "source"],
            },
        }
    },
    "required": ["headlines"],
}

# ---------------------------------------------------------------------------
# Relevance filter — keep only headlines related to compute/energy
# ---------------------------------------------------------------------------

RELEVANCE_KEYWORDS = [
    "gpu", "nvidia", "amd", "intel", "chip", "semiconductor", "tsmc",
    "data center", "datacenter", "cloud", "aws", "azure", "gcp", "google cloud",
    "compute", "server", "ai ", "artificial intelligence", "machine learning",
    "energy", "electricity", "power grid", "natural gas", "nuclear",
    "solar", "renewable", "utility", "blackout", "heat wave",
    "supply chain", "shortage", "tariff", "export", "sanction",
    "spot price", "instance", "lambda labs", "vast.ai", "runpod",
    "openai", "anthropic", "meta ai", "training run", "inference",
]


def _is_relevant(title: str) -> bool:
    """Check if a headline is relevant to compute pricing signals."""
    lower = title.lower()
    return any(kw in lower for kw in RELEVANCE_KEYWORDS)


def _classify_sentiment(title: str) -> tuple[str, float]:
    """
    Classify a headline as bullish / bearish / neutral for compute pricing.

    Returns (label, score) where score is in [-1.0, 1.0].
    Positive = bullish (prices likely to rise).
    Negative = bearish (prices likely to fall).
    """
    lower = title.lower()
    bull_hits = sum(1 for kw in BULLISH_KEYWORDS if kw in lower)
    bear_hits = sum(1 for kw in BEARISH_KEYWORDS if kw in lower)

    if bull_hits > bear_hits:
        score = min(1.0, 0.3 + 0.2 * bull_hits)
        return "bullish", round(score, 2)
    elif bear_hits > bull_hits:
        score = max(-1.0, -0.3 - 0.2 * bear_hits)
        return "bearish", round(score, 2)
    else:
        return "neutral", 0.0


# ---------------------------------------------------------------------------
# Fallback sample headlines — realistic examples so demos always work
# ---------------------------------------------------------------------------

FALLBACK_HEADLINES = [
    {"title": "NVIDIA reports record Q4 data center revenue amid surging AI demand", "source": "Reuters"},
    {"title": "AWS announces new GPU instance types with 40% better price-performance", "source": "TechCrunch"},
    {"title": "TSMC Arizona fab faces further delays, chip shortage concerns mount", "source": "Reuters"},
    {"title": "European energy prices spike as cold snap strains power grid", "source": "Reuters"},
    {"title": "Google Cloud cuts A100 GPU instance pricing by 15%", "source": "TechCrunch"},
    {"title": "US imposes new semiconductor export restrictions targeting China", "source": "Reuters"},
    {"title": "Meta plans $40B data center expansion to support AI training workloads", "source": "TechCrunch"},
    {"title": "Vast.ai reports 3x increase in GPU rental demand from AI startups", "source": "TechCrunch"},
    {"title": "Texas grid operator warns of potential summer blackouts near data center hubs", "source": "DatacenterDynamics"},
    {"title": "New nuclear reactor approved to power Virginia data center corridor", "source": "DatacenterDynamics"},
    {"title": "Lambda Labs launches H200 GPU cloud instances at competitive spot pricing", "source": "TechCrunch"},
    {"title": "AMD MI300X supply constraints ease as production ramps up", "source": "Reuters"},
    {"title": "RunPod introduces serverless GPU inference with pay-per-second billing", "source": "TechCrunch"},
    {"title": "Natural gas futures surge 12% on winter demand forecast", "source": "Reuters"},
    {"title": "Open source Llama 4 model reduces enterprise GPU compute requirements", "source": "TechCrunch"},
]


class NewsSource(BaseSignalSource):
    """
    Scrapes tech / energy news headlines via Browserbase Stagehand,
    classifies sentiment for GPU compute pricing, and stores to Redis.
    """

    source_id = "news"
    source_name = "News Sentiment"

    def __init__(self):
        settings = get_settings()
        self.bb_api_key = settings.browserbase_api_key
        self.bb_project_id = settings.browserbase_project_id
        self.model_api_key = settings.wandb_api_key  # reuse W&B key for LLM
        self._has_browserbase = bool(self.bb_api_key and self.bb_project_id)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @weave.op()
    async def fetch_latest(self) -> list[dict[str, Any]]:
        """Fetch and classify recent news headlines."""
        if self._has_browserbase:
            raw_headlines = await self._scrape_with_stagehand()
        else:
            raw_headlines = self._get_fallback_headlines()

        # Filter to relevant headlines and classify sentiment
        now = datetime.now(timezone.utc)
        results = []
        for item in raw_headlines:
            title = item.get("title", "")
            source = item.get("source", "unknown")

            if not _is_relevant(title):
                continue

            label, score = _classify_sentiment(title)
            results.append({
                "source": self.source_id,
                "name": title[:120],  # truncate long headlines
                "news_source": source,
                "sentiment": label,
                "value": score,
                "unit": "sentiment",
                "timestamp": now.isoformat(),
            })

        return results

    @weave.op()
    async def fetch_history(
        self, start: datetime, end: datetime
    ) -> list[dict[str, Any]]:
        """
        Generate synthetic historical sentiment data.

        Real historical scraping is not practical, so we simulate
        plausible sentiment over the requested range.
        """
        random.seed(42)
        results = []
        current = start

        while current < end:
            # 2-4 headlines per hour block
            n_headlines = random.randint(2, 4)
            for _ in range(n_headlines):
                headline = random.choice(FALLBACK_HEADLINES)
                title = headline["title"]
                label, score = _classify_sentiment(title)

                # Add some temporal noise
                noise = random.gauss(0, 0.1)
                score = max(-1.0, min(1.0, score + noise))
                score = round(score, 2)

                results.append({
                    "source": self.source_id,
                    "name": title[:120],
                    "news_source": headline["source"],
                    "sentiment": label,
                    "value": score,
                    "unit": "sentiment",
                    "timestamp": current.isoformat(),
                })

            current += timedelta(hours=1)

        return results

    async def store(self, data: list[dict[str, Any]]) -> None:
        """Store sentiment scores to Redis TimeSeries."""
        r = await get_redis()

        for item in data:
            # Aggregate key: one series per news source
            news_src = item.get("news_source", "unknown").lower().replace(" ", "_")
            key = f"signal:{self.source_id}:{news_src}:sentiment"

            try:
                ts_str = item["timestamp"]
                ts = datetime.fromisoformat(ts_str)
                ts_ms = int(ts.timestamp() * 1000)
            except (ValueError, KeyError):
                continue

            try:
                await r.execute_command(
                    "TS.ADD", key, ts_ms, item["value"],
                    "RETENTION", 2592000000,  # 30 days
                    "LABELS",
                    "source", self.source_id,
                    "news_source", news_src,
                    "metric", "sentiment",
                )
            except Exception:
                try:
                    await r.execute_command("TS.ADD", key, ts_ms, item["value"])
                except Exception:
                    pass  # duplicate timestamp

        # Also store the latest batch of headlines as a JSON list for the UI
        try:
            from core.redis_client import push_to_list
            for item in data:
                await push_to_list("news:headlines", item, max_len=200)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Stagehand browser scraping
    # ------------------------------------------------------------------

    @weave.op()
    async def _scrape_with_stagehand(self) -> list[dict[str, Any]]:
        """Use Browserbase Stagehand to scrape headlines from news sites."""
        from stagehand import AsyncStagehand

        all_headlines: list[dict[str, Any]] = []

        try:
            client = AsyncStagehand(
                browserbase_api_key=self.bb_api_key,
                browserbase_project_id=self.bb_project_id,
                model_api_key=self.model_api_key,
            )

            session = await client.sessions.start(
                model_name="openai/gpt-4o-mini",
            )

            try:
                for url, instruction in NEWS_TARGETS:
                    try:
                        await session.navigate(url=url)

                        # Give the page a moment to fully render
                        await asyncio.sleep(2)

                        result = await session.extract(
                            instruction=instruction,
                            schema=HEADLINES_SCHEMA,
                        )

                        # The extract result contains a data attribute
                        if result and hasattr(result, "data"):
                            extracted = result.data
                            if hasattr(extracted, "result"):
                                extracted = extracted.result
                            if isinstance(extracted, dict):
                                headlines = extracted.get("headlines", [])
                            elif isinstance(extracted, list):
                                headlines = extracted
                            else:
                                headlines = []

                            for h in headlines:
                                if isinstance(h, dict) and h.get("title"):
                                    all_headlines.append({
                                        "title": h["title"],
                                        "source": h.get("source", "unknown"),
                                    })
                    except Exception as e:
                        print(f"[NewsSource] Error scraping {url}: {e}")
                        continue
            finally:
                await session.end()

        except Exception as e:
            print(f"[NewsSource] Stagehand session error: {e}")
            # Fall back to sample headlines if scraping fails entirely
            if not all_headlines:
                all_headlines = self._get_fallback_headlines()

        return all_headlines

    # ------------------------------------------------------------------
    # Fallback
    # ------------------------------------------------------------------

    @staticmethod
    def _get_fallback_headlines() -> list[dict[str, Any]]:
        """Return hardcoded sample headlines for demo / offline mode."""
        # Shuffle slightly so repeated calls look different, but stay stable
        # within a single minute
        seed = int(datetime.now(timezone.utc).timestamp() // 60)
        rng = random.Random(seed)
        sample = list(FALLBACK_HEADLINES)
        rng.shuffle(sample)
        return sample[:10]
