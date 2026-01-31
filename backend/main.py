from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv("../.env")

from core.redis_client import check_redis, close_redis
from core.weave_setup import init_weave
from api.router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_weave()
    yield
    await close_redis()


app = FastAPI(
    title="Compute Oracle",
    description="Self-improving agent that predicts compute cost fluctuations",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
async def health():
    redis_ok = await check_redis()
    return {
        "status": "ok",
        "redis": "connected" if redis_ok else "disconnected",
    }


@app.get("/meta")
async def meta():
    return {
        "version": "0.1.0",
        "project": "compute-oracle",
        "data_sources": ["aws_spot", "eia_electricity", "weather", "gpu_pricing", "news"],
    }
