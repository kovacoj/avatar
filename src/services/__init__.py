from src.config import config

from .text_to_speech import Client as TextToSpeechClient
from .speech_to_text import Client as SpeechToTextClient
from .text import Client as TextClient


text_to_speech = TextToSpeechClient(config.get('tts'))
speech_to_text = SpeechToTextClient(config.get('stt'))
text = TextClient(config.get('text'))


__all__ = [
    "text_to_speech",
    "speech_to_text",
    "text"
]
