import io
import logging
import re
from typing import AsyncGenerator

from src.logging_utils import log_timing
from src.services import Services


SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.?!,;:\n])\s+")
logger = logging.getLogger(__name__)


class ChatController:
    def __init__(self, services: Services):
        self.services = services

    def transcribe_audio(self, audio_file, language: str = "en", request_id: str | None = None) -> str:
        with log_timing(logger, "stt.transcribe", request_id=request_id, language=language):
            return self.services.speech_to_text(audio_file, language=language)

    async def stream_response(self, prompt: str, request_id: str | None = None) -> AsyncGenerator[tuple[str, str], None]:
        with log_timing(logger, "chat.respond", request_id=request_id):
            async for chunk, language in self.services.text(prompt, request_id=request_id):
                yield chunk, language

    def synthesize_speech(self, text: str, language: str, request_id: str | None = None) -> bytes | None:
        sentences = [sentence.strip() for sentence in SENTENCE_SPLIT_PATTERN.split(text) if sentence.strip()]
        if not sentences:
            logger.info("tts.skip request_id=%s reason=empty_text", request_id)
            return None

        with log_timing(logger, "tts.synthesize", request_id=request_id, language=language, sentences=len(sentences)):
            audio_buffer = io.BytesIO()
            for phrase_stream in self.services.text_to_speech(iter(sentences), language=language, request_id=request_id):
                for chunk in phrase_stream:
                    if isinstance(chunk, (bytes, bytearray)) and chunk:
                        audio_buffer.write(chunk)

            audio_bytes = audio_buffer.getvalue()
            return audio_bytes or None
