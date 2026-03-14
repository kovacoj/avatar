from pydantic import BaseModel
from typing import Literal

import re
from openai import OpenAI

from src.resources import system_prompt, user_prompt


class ISOLanguageCode(BaseModel):
    language: Literal["en", "cs", "de"]

class Client:
    def __init__(self, config):
        self.config = config

        self.client = OpenAI(
            api_key=self.config["api_key"],
            base_url=self.config["base_url"],
        )

    def __call__(self, prompt):
        language = self.client.responses.parse(
            model=self.config.get('chat_model'),
            input=[
                {"role": "system", "content": "Infer what the language of the output should be based on the user's prompt. Respond ONLY with a JSON in the format {language: <language_code>} where <language_code> is a 2-letter ISO code (e.g. 'en' for English, 'cs' for Czech, 'de' for German). Do not include any other text. You can choose only those three. If you cannot infer the language, default to English."},
                {"role": "user", "content": prompt},
            ],
            text_format=ISOLanguageCode
        ).output[0].content[0].parsed.language

        response = self.client.chat.completions.create(
            model=self.config.get("chat_model"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt.format(message=prompt)},
            ],
            stream=True
        )

        return self.clean_stream(response), language

    def clean_stream(self, stream):
        """
        Convert token stream into sentence-level stream.
        Yields full sentences while preserving streaming behavior.
        """
        buffer = ""

        phrase_split_pattern = re.compile(r'(?<=[.?!,;:\n])\s+') # 

        for chunk in stream:
            if not chunk.choices:
                continue
                
            delta = chunk.choices[0].delta.content
            if not delta:
                continue

            buffer += delta

            phrases = phrase_split_pattern.split(buffer)

            if len(phrases) > 1:
                for phrase in phrases[:-1]:
                    yield phrase.strip()

                buffer = phrases[-1]

        if buffer.strip():
            yield buffer.strip()

if __name__ == "__main__":
    from src.config import config
    
    client = Client(config["text"])

    response, language = client("Introduce yourself in 2 sentences. Answer in german.")
    
    for chunk in response:
        print(chunk)
