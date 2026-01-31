from fastapi import APIRouter, BackgroundTasks
from datetime import datetime, timezone
from schemas.signals import (
    Signal,
    SignalSource,
    SignalsLatestResponse,
    SignalHistoryResponse,
    DataPoint,
    SourcesResponse,
    SourceStatus,
)
from core.redis_client import get_latest_signals as redis_get_latest, get_signal_history as redis_get_history
from ingestion.aws_spot import AWSSpotSource
from ingestion.eia_electricity import EIAElectricitySource

router = APIRouter()

# Source registry
_sources = {
    "aws_spot": {"name": "AWS Spot Pricing", "class": AWSSpotSource},
    "eia_electricity": {"name": "EIA Electricity", "class": EIAElectricitySource},
    "weather": {"name": "OpenWeatherMap", "class": None},
    "gpu_pricing": {"name": "GPU Cloud Pricing", "class": None},
    "news": {"name": "News Events", "class": None},
}


@router.get("/latest", response_model=SignalsLatestResponse)
async def get_latest_signals():
    now = datetime.now(timezone.utc)
    signals_data = await redis_get_latest()

    if not signals_data:
        # Fallback stub when Redis has no TS data yet
        return SignalsLatestResponse(
            timestamp=now,
            signals=[
                Signal(source=SignalSource.AWS_SPOT, name="p3.2xlarge us-east-1a", value=0.918, unit="USD/hr", timestamp=now, change_pct=-2.3),
                Signal(source=SignalSource.EIA_ELECTRICITY, name="PJM demand", value=142500.0, unit="MWh", timestamp=now, change_pct=1.8),
            ],
        )

    signals = []
    for s in signals_data:
        try:
            signals.append(Signal(
                source=SignalSource(s["source"]),
                name=s["name"],
                value=s["value"],
                unit=s["unit"],
                timestamp=s["timestamp"],
                change_pct=s.get("change_pct"),
            ))
        except ValueError:
            continue

    return SignalsLatestResponse(timestamp=now, signals=signals)


@router.get("/history", response_model=SignalHistoryResponse)
async def get_signal_history(source: str = "aws_spot", name: str = "p3.2xlarge", hours: int = 168):
    data = await redis_get_history(source, name, hours)
    return SignalHistoryResponse(
        source=SignalSource(source),
        name=name,
        data_points=[DataPoint(timestamp=d["timestamp"], value=d["value"]) for d in data],
    )


@router.get("/sources", response_model=SourcesResponse)
async def get_sources():
    sources = []
    for src_id, info in _sources.items():
        sources.append(SourceStatus(
            id=src_id,
            name=info["name"],
            status="active" if info["class"] is not None else "inactive",
            last_update=datetime.now(timezone.utc) if info["class"] is not None else None,
        ))
    return SourcesResponse(sources=sources)


@router.post("/ingest")
async def trigger_ingestion(background_tasks: BackgroundTasks, source: str | None = None):
    """Manually trigger signal ingestion."""
    async def _ingest():
        sources_to_run = []
        if source:
            info = _sources.get(source)
            if info and info["class"]:
                sources_to_run.append(info["class"]())
        else:
            for info in _sources.values():
                if info["class"]:
                    sources_to_run.append(info["class"]())

        results = {}
        for src in sources_to_run:
            try:
                data = await src.ingest()
                results[src.source_id] = len(data)
            except Exception as e:
                results[src.source_id] = f"error: {e}"
        return results

    background_tasks.add_task(_ingest)
    return {"status": "ingestion_started", "source": source or "all"}
