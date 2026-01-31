"""
GPU cloud pricing source — provides current pricing data from major
GPU cloud providers (Lambda Labs, Vast.ai, RunPod).

Uses hardcoded but realistic pricing data rather than live scraping,
since these providers don't have stable public APIs. The prices are
based on real listings as of early 2026 and serve as a reference
signal for the causal pricing model.
"""

import random
from datetime import datetime, timezone, timedelta
from typing import Any
import weave

from ingestion.base_source import BaseSignalSource
from core.redis_client import get_redis

# ---------------------------------------------------------------------------
# Current GPU cloud pricing — realistic data from provider listings
# Prices in USD/hr for on-demand instances
# ---------------------------------------------------------------------------

GPU_PRICING_DATA: list[dict[str, Any]] = [
    # Lambda Labs
    {
        "provider": "lambda",
        "provider_name": "Lambda Labs",
        "gpu": "A100-80GB",
        "gpu_count": 1,
        "price": 1.29,
        "vram_gb": 80,
    },
    {
        "provider": "lambda",
        "provider_name": "Lambda Labs",
        "gpu": "A100-80GB",
        "gpu_count": 8,
        "price": 10.32,
        "vram_gb": 640,
    },
    {
        "provider": "lambda",
        "provider_name": "Lambda Labs",
        "gpu": "H100-80GB",
        "gpu_count": 1,
        "price": 2.49,
        "vram_gb": 80,
    },
    {
        "provider": "lambda",
        "provider_name": "Lambda Labs",
        "gpu": "H100-80GB",
        "gpu_count": 8,
        "price": 19.92,
        "vram_gb": 640,
    },
    {
        "provider": "lambda",
        "provider_name": "Lambda Labs",
        "gpu": "H200-141GB",
        "gpu_count": 1,
        "price": 3.29,
        "vram_gb": 141,
    },
    {
        "provider": "lambda",
        "provider_name": "Lambda Labs",
        "gpu": "H200-141GB",
        "gpu_count": 8,
        "price": 26.32,
        "vram_gb": 1128,
    },
    # Vast.ai (community cloud — prices vary; these are typical medians)
    {
        "provider": "vastai",
        "provider_name": "Vast.ai",
        "gpu": "A100-80GB",
        "gpu_count": 1,
        "price": 0.85,
        "vram_gb": 80,
    },
    {
        "provider": "vastai",
        "provider_name": "Vast.ai",
        "gpu": "A100-80GB",
        "gpu_count": 8,
        "price": 6.80,
        "vram_gb": 640,
    },
    {
        "provider": "vastai",
        "provider_name": "Vast.ai",
        "gpu": "H100-80GB",
        "gpu_count": 1,
        "price": 1.89,
        "vram_gb": 80,
    },
    {
        "provider": "vastai",
        "provider_name": "Vast.ai",
        "gpu": "H100-80GB",
        "gpu_count": 8,
        "price": 15.12,
        "vram_gb": 640,
    },
    {
        "provider": "vastai",
        "provider_name": "Vast.ai",
        "gpu": "RTX 4090",
        "gpu_count": 1,
        "price": 0.37,
        "vram_gb": 24,
    },
    {
        "provider": "vastai",
        "provider_name": "Vast.ai",
        "gpu": "A6000",
        "gpu_count": 1,
        "price": 0.42,
        "vram_gb": 48,
    },
    # RunPod
    {
        "provider": "runpod",
        "provider_name": "RunPod",
        "gpu": "A100-80GB",
        "gpu_count": 1,
        "price": 1.19,
        "vram_gb": 80,
    },
    {
        "provider": "runpod",
        "provider_name": "RunPod",
        "gpu": "H100-80GB",
        "gpu_count": 1,
        "price": 2.39,
        "vram_gb": 80,
    },
    {
        "provider": "runpod",
        "provider_name": "RunPod",
        "gpu": "H100-80GB",
        "gpu_count": 8,
        "price": 19.12,
        "vram_gb": 640,
    },
    {
        "provider": "runpod",
        "provider_name": "RunPod",
        "gpu": "RTX 4090",
        "gpu_count": 1,
        "price": 0.44,
        "vram_gb": 24,
    },
    {
        "provider": "runpod",
        "provider_name": "RunPod",
        "gpu": "A6000",
        "gpu_count": 1,
        "price": 0.49,
        "vram_gb": 48,
    },
    {
        "provider": "runpod",
        "provider_name": "RunPod",
        "gpu": "RTX 3090",
        "gpu_count": 1,
        "price": 0.22,
        "vram_gb": 24,
    },
]


class GPUPricingSource(BaseSignalSource):
    """
    Provides current GPU cloud instance pricing from Lambda Labs,
    Vast.ai, and RunPod as reference signals for the pricing model.
    """

    source_id = "gpu_pricing"
    source_name = "GPU Cloud Pricing"

    @weave.op()
    async def fetch_latest(self) -> list[dict[str, Any]]:
        """Return current GPU cloud pricing data."""
        now = datetime.now(timezone.utc)
        results = []

        for entry in GPU_PRICING_DATA:
            gpu_label = entry["gpu"]
            count = entry["gpu_count"]
            name = f"{entry['provider_name']} {gpu_label} x{count}"

            results.append({
                "source": self.source_id,
                "name": name,
                "provider": entry["provider"],
                "gpu": gpu_label,
                "gpu_count": count,
                "vram_gb": entry["vram_gb"],
                "value": entry["price"],
                "unit": "USD/hr",
                "timestamp": now.isoformat(),
            })

        return results

    @weave.op()
    async def fetch_history(
        self, start: datetime, end: datetime
    ) -> list[dict[str, Any]]:
        """
        Generate synthetic historical GPU pricing data.

        GPU cloud prices shift slowly (weekly/monthly), unlike spot
        instances. We simulate gradual trends with small random walks.
        """
        random.seed(42)
        results = []
        current = start

        # Step in 6-hour increments (prices don't change faster than that)
        step = timedelta(hours=6)

        # Track running price per (provider, gpu, count) tuple
        running_prices: dict[tuple[str, str, int], float] = {
            (e["provider"], e["gpu"], e["gpu_count"]): e["price"]
            for e in GPU_PRICING_DATA
        }

        while current < end:
            for entry in GPU_PRICING_DATA:
                pkey = (entry["provider"], entry["gpu"], entry["gpu_count"])
                base = running_prices[pkey]

                # Small random walk: +/- up to 2% per step
                drift = random.gauss(0, 0.005) * base
                new_price = max(0.05, base + drift)
                new_price = round(new_price, 2)
                running_prices[pkey] = new_price

                name = f"{entry['provider_name']} {entry['gpu']} x{entry['gpu_count']}"
                results.append({
                    "source": self.source_id,
                    "name": name,
                    "provider": entry["provider"],
                    "gpu": entry["gpu"],
                    "gpu_count": entry["gpu_count"],
                    "vram_gb": entry["vram_gb"],
                    "value": new_price,
                    "unit": "USD/hr",
                    "timestamp": current.isoformat(),
                })

            current += step

        return results

    async def store(self, data: list[dict[str, Any]]) -> None:
        """Store GPU pricing data to Redis TimeSeries."""
        r = await get_redis()

        for item in data:
            provider = item["provider"]
            gpu = item["gpu"].lower().replace(" ", "_").replace("-", "_")
            count = item["gpu_count"]
            key = f"signal:{self.source_id}:{provider}:{gpu}_x{count}"

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
                    "provider", provider,
                    "gpu", item["gpu"],
                    "gpu_count", str(count),
                )
            except Exception:
                try:
                    await r.execute_command("TS.ADD", key, ts_ms, item["value"])
                except Exception:
                    pass  # duplicate timestamp
