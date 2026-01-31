import json
import redis.asyncio as aioredis
from datetime import datetime, timezone
from typing import Any
from config import get_settings

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        settings = get_settings()
        _redis = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
    return _redis


async def check_redis() -> bool:
    try:
        r = await get_redis()
        return await r.ping()
    except Exception:
        return False


async def close_redis():
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


# --- TimeSeries helpers ---

async def get_latest_signals() -> list[dict[str, Any]]:
    """Get the most recent value from all signal TimeSeries keys."""
    r = await get_redis()
    results = []

    try:
        # Get all TS keys with labels included
        raw = await r.execute_command(
            "TS.MGET", "WITHLABELS", "FILTER",
            "source=(aws_spot,eia_electricity,weather,gpu_pricing,news)",
        )
        for item in raw:
            key = item[0]
            # WITHLABELS returns [[k, v], [k, v], ...] format
            labels = {pair[0]: pair[1] for pair in item[1]}
            ts_ms, value = item[2]

            # Parse key: signal:{source}:{name}:{qualifier}
            parts = key.split(":")
            source = labels.get("source", parts[1] if len(parts) > 1 else "unknown")

            # Build a human-readable name from labels
            if source == "aws_spot":
                name = f"{labels.get('instance', '')} {labels.get('az', '')}"
                unit = "USD/hr"
            elif source == "eia_electricity":
                name = f"{labels.get('respondent', '')} {labels.get('metric', '')}"
                unit = "MWh"
            elif source == "weather":
                name = f"Temperature ({labels.get('location', '')})"
                unit = "F"
            else:
                name = key
                unit = ""

            results.append({
                "source": source,
                "name": name.strip(),
                "value": float(value),
                "unit": unit,
                "timestamp": datetime.fromtimestamp(
                    int(ts_ms) / 1000, tz=timezone.utc
                ).isoformat(),
                "change_pct": None,  # Will be calculated if we have history
            })
    except Exception as e:
        print(f"Error fetching latest signals: {e}")

    return results


async def get_signal_history(
    source: str, name: str, hours: int = 168
) -> list[dict[str, Any]]:
    """Get time-series history for a specific signal."""
    r = await get_redis()
    results = []

    try:
        # Find matching keys
        filter_parts = [f"source={source}"]
        if source == "aws_spot":
            # name like "p3.2xlarge us-east-1a"
            parts = name.split()
            if len(parts) >= 1:
                filter_parts.append(f"instance={parts[0]}")
            if len(parts) >= 2:
                filter_parts.append(f"az={parts[1]}")

        elif source == "eia_electricity":
            parts = name.split()
            if len(parts) >= 1:
                filter_parts.append(f"respondent={parts[0]}")

        # Query with filter
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        start_ms = now_ms - (hours * 3600 * 1000)

        raw = await r.execute_command(
            "TS.MRANGE", start_ms, now_ms,
            "FILTER", *filter_parts,
        )

        for item in raw:
            for ts_ms, value in item[2]:
                results.append({
                    "timestamp": datetime.fromtimestamp(
                        int(ts_ms) / 1000, tz=timezone.utc
                    ).isoformat(),
                    "value": float(value),
                })

    except Exception as e:
        print(f"Error fetching signal history: {e}")

    return sorted(results, key=lambda x: x["timestamp"])


# --- JSON helpers ---

async def store_json(key: str, data: dict[str, Any]) -> None:
    r = await get_redis()
    await r.execute_command("JSON.SET", key, "$", json.dumps(data))


async def get_json(key: str) -> dict[str, Any] | None:
    r = await get_redis()
    try:
        raw = await r.execute_command("JSON.GET", key)
        if raw:
            return json.loads(raw)
    except Exception:
        pass
    return None


async def push_to_list(key: str, data: dict[str, Any], max_len: int = 1000) -> None:
    r = await get_redis()
    await r.lpush(key, json.dumps(data))
    await r.ltrim(key, 0, max_len - 1)


async def get_list(key: str, limit: int = 50) -> list[dict[str, Any]]:
    r = await get_redis()
    raw = await r.lrange(key, 0, limit - 1)
    return [json.loads(item) for item in raw]
