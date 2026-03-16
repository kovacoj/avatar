from openai import OpenAI


# Speech to text service using Siemens API (whisper)
class Client:
    def __init__(self, config):
        self.config = config

        self.client = OpenAI(
            api_key=self.config["api_key"],
            base_url=self.config["base_url"],
        )

    def __call__(self, audio_file, language="en"):
        # TODO: if needed, we need to contact code.siemens.io to enable language detection
        return self.client.audio.transcriptions.create(
            model=self.config.get("model"),
            file=audio_file,
            response_format="verbose_json",
            prompt=None,
            temperature=0.0,
            language=language,
        ).text


if __name__ == "__main__":
    from src.config import config
    
    client = Client(config["stt"])

    with open("./output/audio/anet.wav", "rb") as audio_file:
        response = client(audio_file)
        print(response)
