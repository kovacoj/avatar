import io
import re
from typing import AsyncGenerator

from src.services import Services


SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.?!,;:\n])\s+")


class ChatController:
    def __init__(self, services: Services):
        self.services = services

    def transcribe_audio(self, audio_file, language: str = "en") -> str:
        return self.services.speech_to_text(audio_file, language=language)

    async def stream_response(self, prompt: str) -> AsyncGenerator[tuple[str, str], None]:
        async for chunk, language in self.services.text(prompt):
            yield chunk, language

    def synthesize_speech(self, text: str, language: str) -> bytes | None:
        sentences = [sentence.strip() for sentence in SENTENCE_SPLIT_PATTERN.split(text) if sentence.strip()]
        if not sentences:
            return None

        audio_buffer = io.BytesIO()
        for phrase_stream in self.services.text_to_speech(iter(sentences), language=language):
            for chunk in phrase_stream:
                if isinstance(chunk, (bytes, bytearray)) and chunk:
                    audio_buffer.write(chunk)

        audio_bytes = audio_buffer.getvalue()
        return audio_bytes or None
