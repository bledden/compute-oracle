import weave
from config import get_settings


_initialized = False


def init_weave():
    global _initialized
    if _initialized:
        return
    settings = get_settings()
    if settings.wandb_api_key:
        weave.init("compute-oracle")
        _initialized = True
