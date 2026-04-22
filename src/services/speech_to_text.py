from openai import OpenAI

from src.config.models import STTConfig


class Client:
    def __init__(self, config: STTConfig):
        self.config = config
        self._validate_config()

        self.client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
        )

    def __call__(self, audio_file, language: str = "en") -> str:
        file_payload = self._prepare_audio_file(audio_file)
        return self.client.audio.transcriptions.create(
            model=self.config.model,
            file=file_payload,
            response_format="verbose_json",
            prompt=None,
            temperature=0.0,
            language=language,
        ).text

    @staticmethod
    def _prepare_audio_file(audio_file):
        if hasattr(audio_file, "read"):
            audio_file.seek(0)
            if hasattr(audio_file, "name"):
                return audio_file

            content = audio_file.read()
            audio_file.seek(0)
            return ("audio.wav", content, "audio/wav")

        if isinstance(audio_file, (bytes, bytearray)):
            return ("audio.wav", bytes(audio_file), "audio/wav")

        return audio_file

    def _validate_config(self) -> None:
        missing = [
            key for key in ("api_key", "base_url", "model")
            if not getattr(self.config, key)
        ]
        if missing:
            raise ValueError(f"STT config missing: {', '.join(missing)}")


if __name__ == "__main__":
    from src.config import config
    
    client = Client(config.stt)

    with open("./output/audio/anet.wav", "rb") as audio_file:
        response = client(audio_file)
        print(response)
