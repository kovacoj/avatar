import pytest

from src.config.models import SpeakerConfig, TTSConfig
from src.services.text_to_speech import Client


def build_tts_client() -> Client:
    return Client(
        TTSConfig(
            api_key="test-key",
            model_id="eleven_v3",
            speakers=[
                SpeakerConfig(name="Katarina", id="speaker-en", language="en"),
            ],
            threads=1,
        )
    )


def test_tts_streams_audio_chunks(monkeypatch):
    client = build_tts_client()

    def fake_stream(**_kwargs):
        yield b"hello"
        yield b"world"

    monkeypatch.setattr(client.client.text_to_speech, "stream", fake_stream)

    phrase_streams = list(client(iter(["Hello world"]), language="en"))

    assert len(phrase_streams) == 1
    assert b"".join(phrase_streams[0]) == b"helloworld"


def test_tts_propagates_worker_failures(monkeypatch):
    client = build_tts_client()

    def fake_stream(**_kwargs):
        raise RuntimeError("elevenlabs unavailable")

    monkeypatch.setattr(client.client.text_to_speech, "stream", fake_stream)

    phrase_streams = client(iter(["Hello world"]), language="en")
    phrase_stream = next(phrase_streams)

    with pytest.raises(RuntimeError, match="elevenlabs unavailable"):
        list(phrase_stream)
