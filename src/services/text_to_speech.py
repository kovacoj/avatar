from elevenlabs.client import ElevenLabs
from collections import defaultdict


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

    def __call__(self, text, language):
        return self.client.text_to_speech.convert(
            voice_id=self.speaker_id.get(language),
            output_format=self.config.get("output_format", "mp3_22050_32"),
            model_id=self.config.get("model_id"),
            language_code=language,
            text=text
        )


if __name__ == '__main__':
    from src.config import config

    client = Client(config.get('tts'))

    audio = client("Inside", "en")

    with open("output/audio/inside.mp3", "wb") as f:
        for chunk in audio:
            if chunk:
                f.write(chunk)
