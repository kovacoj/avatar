from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import queue
import threading
from typing import Generator

from elevenlabs.client import ElevenLabs

from src.config.models import TTSConfig


_SENTINEL = object()


class Client:
    def __init__(self, config: TTSConfig):
        self.config = config
        self._validate_config()
        self.output_format = self.config.output_format

        speaker_id = {
            speaker.language: speaker.id
            for speaker in self.config.speakers
        }
        self.speaker_id = defaultdict(lambda: speaker_id.get("en"), speaker_id)

        self.client = ElevenLabs(
            api_key=self.config.api_key
        )

        self.executor = ThreadPoolExecutor(
            max_workers=self.config.threads
        )

    def _worker(self, curr_text: str, prev_text: str, next_text: str, chunk_queue: queue.Queue, language: str):
        try:
            audio_stream = self.client.text_to_speech.stream(
                text=curr_text,
                previous_text=prev_text or None,
                next_text=next_text or None,
                voice_id=self.speaker_id[language],
                model_id=self.config.model_id,
                language_code=language,
                output_format=self.output_format,
            )

            for chunk in audio_stream:
                if isinstance(chunk, (bytes, bytearray)) and chunk:
                    chunk_queue.put(chunk)
        except Exception as exc:
            chunk_queue.put(exc)
        finally:
            chunk_queue.put(_SENTINEL)

    def __call__(
        self, sentence_stream: Generator[str, None, None], language="en"
    ) -> Generator[Generator[bytes, None, None], None, None]:
        ordered_queues = queue.Queue()

        def producer_thread():
            iterator = iter(sentence_stream)

            try:
                prev_text = ""
                curr_text = next(iterator)
            except StopIteration:
                ordered_queues.put(_SENTINEL)
                return

            while True:
                try:
                    next_text = next(iterator)
                except StopIteration:
                    next_text = None

                sentence_queue = queue.Queue()
                self.executor.submit(
                    self._worker,
                    curr_text,
                    prev_text,
                    next_text,
                    sentence_queue,
                    language,
                )
                ordered_queues.put(sentence_queue)

                if next_text is None:
                    break

                prev_text, curr_text = curr_text, next_text

            ordered_queues.put(_SENTINEL)

        threading.Thread(target=producer_thread, daemon=True).start()

        while True:
            current_sentence_queue = ordered_queues.get()

            if current_sentence_queue is _SENTINEL:
                break

            def yield_sentence_chunks(sentence_queue=current_sentence_queue):
                while True:
                    item = sentence_queue.get()
                    if item is _SENTINEL:
                        break
                    if isinstance(item, Exception):
                        raise item
                    yield item

            yield yield_sentence_chunks()

    def _validate_config(self) -> None:
        missing = []
        if not self.config.api_key:
            missing.append("api_key")
        if not self.config.model_id:
            missing.append("model_id")
        if not self.config.speakers:
            missing.append("speakers")
        if missing:
            raise ValueError(f"TTS config missing: {', '.join(missing)}")
