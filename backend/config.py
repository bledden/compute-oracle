from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Redis
    redis_url: str = "redis://localhost:6379"

    # LLM (via W&B Inference — OpenAI-compatible API)
    # Uses wandb_api_key for authentication

    # AWS
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_default_region: str = "us-east-1"

    # EIA
    eia_api_key: str = ""

    # OpenWeatherMap
    openweather_api_key: str = ""

    # Browserbase
    browserbase_api_key: str = ""
    browserbase_project_id: str = ""

    # W&B
    wandb_api_key: str = ""

    # App
    app_env: str = "development"
    log_level: str = "INFO"

    model_config = {"env_file": "../.env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
