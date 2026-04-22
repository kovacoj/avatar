import functools
from dataclasses import dataclass

from .text_to_speech import Client as TextToSpeechClient
from .speech_to_text import Client as SpeechToTextClient
from .text import Client as TextClient
from src.config import AppConfig, get_config


@dataclass(frozen=True)
class Services:
    text_to_speech: TextToSpeechClient
    speech_to_text: SpeechToTextClient
    text: TextClient


@functools.lru_cache(maxsize=1)
def get_services(config: AppConfig | None = None) -> Services:
    app_config = config or get_config()
    return Services(
        text_to_speech=TextToSpeechClient(app_config.tts),
        speech_to_text=SpeechToTextClient(app_config.stt),
        text=TextClient(app_config.text),
    )


__all__ = [
    "Services",
    "get_services",
]
