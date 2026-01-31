"""W&B Inference client — OpenAI-compatible API backed by CoreWeave GPUs.

Uses your existing W&B API key for authentication.
Available models: DeepSeek R1, Qwen3, Llama 4, etc.
See: https://docs.wandb.ai/guides/inference/models/
"""

from openai import AsyncOpenAI
from config import get_settings

WANDB_INFERENCE_BASE_URL = "https://api.inference.wandb.ai/v1"

# Model assignments
REASONER_MODEL = "deepseek-ai/DeepSeek-R1-0528"  # Strong analytical reasoning
PREDICTOR_MODEL = "Qwen/Qwen3-30B-A3B-Instruct-2507"  # Fast structured JSON

_client: AsyncOpenAI | None = None


def get_llm_client() -> AsyncOpenAI:
    """Get the W&B Inference client (OpenAI-compatible)."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncOpenAI(
            base_url=WANDB_INFERENCE_BASE_URL,
            api_key=settings.wandb_api_key,
        )
    return _client
