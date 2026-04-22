from dataclasses import dataclass

import pytest

from src.orchestration.chat import ChatController


@dataclass
class FakeServices:
    text_to_speech: object
    speech_to_text: object
    text: object


class FakeSpeechToText:
    def __call__(self, audio_file, language="en"):
        return f"transcribed:{language}:{audio_file}"


class FakeTextService:
    async def __call__(self, prompt):
        yield "Hello world.", "en"
        yield " Guten tag.", "de"


class FakeTextToSpeech:
    def __call__(self, sentence_stream, language="en"):
        for sentence in sentence_stream:
            yield iter([f"{language}:{sentence}".encode()])


def build_controller() -> ChatController:
    services = FakeServices(
        text_to_speech=FakeTextToSpeech(),
        speech_to_text=FakeSpeechToText(),
        text=FakeTextService(),
    )
    return ChatController(services)


def test_transcribe_audio_delegates_to_service():
    controller = build_controller()

    result = controller.transcribe_audio("sample.wav", language="de")

    assert result == "transcribed:de:sample.wav"


@pytest.mark.anyio
async def test_stream_response_yields_backend_chunks():
    controller = build_controller()

    result = [item async for item in controller.stream_response("hello")]

    assert result == [("Hello world.", "en"), (" Guten tag.", "de")]


def test_synthesize_speech_joins_sentence_audio():
    controller = build_controller()

    result = controller.synthesize_speech("First sentence. Second sentence!", "cs")

    assert result == b"cs:First sentence.cs:Second sentence!"


def test_synthesize_speech_returns_none_for_blank_text():
    controller = build_controller()

    result = controller.synthesize_speech("   \n  ", "en")

    assert result is None
