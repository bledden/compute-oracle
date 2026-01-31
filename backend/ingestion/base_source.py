from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
import weave


class BaseSignalSource(ABC):
    source_id: str
    source_name: str

    @weave.op()
    async def ingest(self) -> list[dict[str, Any]]:
        """Fetch latest data and store to Redis. Returns list of stored signals."""
        data = await self.fetch_latest()
        await self.store(data)
        return data

    @abstractmethod
    async def fetch_latest(self) -> list[dict[str, Any]]:
        """Fetch the most recent data from the source."""
        ...

    @abstractmethod
    async def fetch_history(
        self, start: datetime, end: datetime
    ) -> list[dict[str, Any]]:
        """Fetch historical data for a date range."""
        ...

    @abstractmethod
    async def store(self, data: list[dict[str, Any]]) -> None:
        """Store fetched data to Redis."""
        ...
