import httpx
from datetime import datetime, timezone, timedelta
from typing import Any
import weave

from ingestion.base_source import BaseSignalSource
from core.redis_client import get_redis
from config import get_settings

# EIA API v2 base
EIA_BASE = "https://api.eia.gov/v2"

# Target balancing authorities (map to AWS regions)
RESPONDENTS = {
    "PJM": "PJM Interconnection (us-east-1 / Virginia)",
    "ERCO": "ERCOT (Texas)",
    "CISO": "CAISO (California)",
}


class EIAElectricitySource(BaseSignalSource):
    source_id = "eia_electricity"
    source_name = "EIA Electricity"

    def __init__(self):
        self.api_key = get_settings().eia_api_key

    @weave.op()
    async def fetch_latest(self) -> list[dict[str, Any]]:
        """Fetch recent electricity demand data."""
        end = datetime.now(timezone.utc)
        start = end - timedelta(hours=24)
        return await self._fetch_demand(start, end)

    @weave.op()
    async def fetch_history(
        self, start: datetime, end: datetime
    ) -> list[dict[str, Any]]:
        """Fetch historical electricity demand."""
        return await self._fetch_demand(start, end)

    async def _fetch_demand(
        self, start: datetime, end: datetime
    ) -> list[dict[str, Any]]:
        results = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for respondent, label in RESPONDENTS.items():
                try:
                    params = {
                        "api_key": self.api_key,
                        "frequency": "hourly",
                        "data[0]": "value",
                        "facets[respondent][]": respondent,
                        "facets[type][]": "D",  # D = Demand
                        "start": start.strftime("%Y-%m-%dT%H"),
                        "end": end.strftime("%Y-%m-%dT%H"),
                        "sort[0][column]": "period",
                        "sort[0][direction]": "desc",
                        "length": 100,
                    }

                    resp = await client.get(
                        f"{EIA_BASE}/electricity/rto/region-data/data/",
                        params=params,
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    for row in data.get("response", {}).get("data", []):
                        value = row.get("value")
                        if value is None:
                            continue
                        period = row.get("period", "")
                        results.append({
                            "source": self.source_id,
                            "name": f"{respondent} demand",
                            "respondent": respondent,
                            "metric": "demand",
                            "value": float(value),
                            "unit": "MWh",
                            "timestamp": f"{period}:00:00+00:00" if "T" in period else period,
                        })
                except Exception as e:
                    print(f"Error fetching EIA data for {respondent}: {e}")
                    continue

        return results

    async def store(self, data: list[dict[str, Any]]) -> None:
        r = await get_redis()
        for item in data:
            key = f"signal:{self.source_id}:{item['respondent']}:{item['metric']}"
            try:
                ts_str = item["timestamp"]
                ts = datetime.fromisoformat(ts_str)
                ts_ms = int(ts.timestamp() * 1000)
            except (ValueError, KeyError):
                continue

            try:
                await r.execute_command(
                    "TS.ADD", key, ts_ms, item["value"],
                    "RETENTION", 2592000000,
                    "LABELS", "source", self.source_id,
                    "respondent", item["respondent"],
                    "metric", item["metric"],
                )
            except Exception:
                try:
                    await r.execute_command("TS.ADD", key, ts_ms, item["value"])
                except Exception:
                    pass
