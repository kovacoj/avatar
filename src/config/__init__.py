import functools
from .config import Config, ConfigError
from .models import AppConfig

@functools.lru_cache(maxsize=1)
def get_config() -> AppConfig:
    return Config.load()

config = get_config()

__all__ = ["AppConfig", "ConfigError", "config", "get_config"]
