from elevenlabs.client import ElevenLabs

import queue
import threading
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

from typing import Generator


class Client:
    def __init__(self, config):
        self.config = config
        
        speaker_id = {
            speaker['language']: speaker.get('id')
            for speaker in self.config['speakers']
        }
        self.speaker_id = defaultdict(lambda: speaker_id.get("en"), speaker_id)

        self.client = ElevenLabs(
            api_key=self.config.get("api_key")
        )

        self.executor = ThreadPoolExecutor(
            max_workers=self.config.get("threads", 4)
        )

    def _worker(self, curr_text: str, prev_text: str, next_text: str, chunk_queue: queue.Queue, language: str):
        """
        Runs in background thread.
        Streams audio chunks directly into shared queue.
        """
        audio_stream = self.client.text_to_speech.stream(
            text=curr_text,
            previous_text=prev_text or None,
            next_text=next_text or None,
            voice_id=self.speaker_id.get(language),
            model_id=self.config.get("model_id"),
            language_code=language,
            output_format=self.config.get("output_format", "mp3_22050_32")
        )

        for chunk in audio_stream:
            if isinstance(chunk, (bytes, bytearray)) and chunk:
                chunk_queue.put(chunk)

        chunk_queue.put(None)
    
    def __call__(
            self, sentence_stream: Generator[str, None, None], language="en"
        ) -> Generator[Generator[bytes, None, None], None, None]:
            """
            Accepts a generator of sentences.
            Returns a generator of GENERATORS (one for each sentence's audio chunks).
            """
            ordered_queues = queue.Queue()

            def producer_thread():
                iterator = iter(sentence_stream)

                try:
                    prev_text = ""
                    curr_text = next(iterator)
                except StopIteration:
                    ordered_queues.put(None)
                    return

                while True:
                    try:
                        next_text = next(iterator)
                    except StopIteration:
                        next_text = None

                    sentence_queue = queue.Queue()
                    
                    # FIXED TYPO: self.exector -> self.executor
                    self.executor.submit(
                        self._worker, curr_text, prev_text, next_text, sentence_queue, language
                    )

                    ordered_queues.put(sentence_queue)

                    if next_text is None:
                        break

                    prev_text, curr_text = curr_text, next_text

                ordered_queues.put(None)

            threading.Thread(target=producer_thread, daemon=True).start()

            # The Main Consumer
            while True:
                current_sentence_queue = ordered_queues.get()
                
                if current_sentence_queue is None:
                    break 

                # Create a sub-generator strictly for this specific sentence
                def yield_sentence_chunks(q):
                    while True:
                        chunk = q.get()
                        if chunk is None:
                            break 
                        yield chunk

                # Yield the sub-generator so the main block can write it to a unique file
                yield yield_sentence_chunks(current_sentence_queue)

# TODO: Add testing block
