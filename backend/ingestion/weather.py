"""Weather data source using OpenWeatherMap API.

Temperature affects cooling costs at data centers, which affects
electricity demand, which affects spot pricing.
"""

import httpx
from datetime import datetime, timezone
from typing import Any
import weave

from ingestion.base_source import BaseSignalSource
from core.redis_client import get_redis
from config import get_settings

# Data center locations (approximate)
DC_LOCATIONS = {
    "us_east": {"lat": 39.0458, "lon": -77.4874, "name": "Ashburn, VA"},  # us-east-1
    "us_west": {"lat": 45.5945, "lon": -122.1562, "name": "Portland, OR"},  # us-west-2
}

OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


class WeatherSource(BaseSignalSource):
    source_id = "weather"
    source_name = "OpenWeatherMap"

    @weave.op()
    async def fetch_latest(self) -> list[dict[str, Any]]:
        """Fetch current weather for data center locations."""
        settings = get_settings()
        api_key = settings.openweather_api_key
        results = []
        now = datetime.now(timezone.utc)

        if not api_key:
            # Return realistic fallback data for demo
            return self._fallback_data(now)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                for region_id, loc in DC_LOCATIONS.items():
                    resp = await client.get(OPENWEATHER_URL, params={
                        "lat": loc["lat"],
                        "lon": loc["lon"],
                        "appid": api_key,
                        "units": "imperial",
                    })
                    resp.raise_for_status()
                    data = resp.json()

                    temp = data["main"]["temp"]
                    humidity = data["main"]["humidity"]

                    results.append({
                        "source": self.source_id,
                        "name": f"temperature_{region_id}",
                        "value": round(temp, 1),
                        "unit": "F",
                        "timestamp": now.isoformat(),
                        "region": region_id,
                        "location": loc["name"],
                    })
                    results.append({
                        "source": self.source_id,
                        "name": f"humidity_{region_id}",
                        "value": humidity,
                        "unit": "%",
                        "timestamp": now.isoformat(),
                        "region": region_id,
                        "location": loc["name"],
                    })
        except Exception as e:
            print(f"Weather API error: {e}")
            return self._fallback_data(now)

        return results

    def _fallback_data(self, now: datetime) -> list[dict[str, Any]]:
        """Generate realistic weather data for demo."""
        hour = now.hour
        # Winter temps in January
        base_temp_east = 35 + (hour - 12) * 0.5 if hour < 18 else 35 - (hour - 18) * 0.3
        base_temp_west = 42 + (hour - 12) * 0.3 if hour < 18 else 42 - (hour - 18) * 0.2

        return [
            {
                "source": self.source_id,
                "name": "temperature_us_east",
                "value": round(base_temp_east, 1),
                "unit": "F",
                "timestamp": now.isoformat(),
                "region": "us_east",
                "location": "Ashburn, VA",
            },
            {
                "source": self.source_id,
                "name": "temperature_us_west",
                "value": round(base_temp_west, 1),
                "unit": "F",
                "timestamp": now.isoformat(),
                "region": "us_west",
                "location": "Portland, OR",
            },
        ]

    async def fetch_history(self, start: datetime, end: datetime) -> list[dict[str, Any]]:
        """Generate synthetic weather history for replay."""
        import random
        random.seed(123)
        from datetime import timedelta

        results = []
        current = start
        while current < end:
            hour = current.hour
            day_of_year = current.timetuple().tm_yday

            for region_id in DC_LOCATIONS:
                # Seasonal + daily temperature pattern
                base = 35 if region_id == "us_east" else 42
                seasonal = -10 * ((day_of_year - 180) / 180) ** 2 + 10  # warmer in summer
                daily = 5 * ((hour - 14) / 12) if hour < 20 else -3  # warmer afternoon
                noise = random.gauss(0, 2)

                temp = round(base + seasonal + daily + noise, 1)
                results.append({
                    "source": self.source_id,
                    "name": f"temperature_{region_id}",
                    "value": temp,
                    "unit": "F",
                    "timestamp": current.isoformat(),
                    "region": region_id,
                })

            current += timedelta(hours=1)

        return results

    async def store(self, data: list[dict[str, Any]]) -> None:
        r = await get_redis()
        for item in data:
            key = f"signal:{self.source_id}:{item['name']}"
            ts_ms = int(datetime.fromisoformat(item["timestamp"]).timestamp() * 1000)
            try:
                await r.execute_command(
                    "TS.ADD", key, ts_ms, item["value"],
                    "RETENTION", 2592000000,
                    "LABELS", "source", self.source_id,
                    "name", item["name"],
                    "region", item.get("region", ""),
                )
            except Exception:
                try:
                    await r.execute_command("TS.ADD", key, ts_ms, item["value"])
                except Exception:
                    pass
