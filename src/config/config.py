from pathlib import Path
import yaml
from dotenv import load_dotenv
import os


class Config:
	@classmethod
	def load(cls) -> dict:
		config_path = Path(__file__).parents[2] / "config"

		with open(config_path / "config.yaml") as file:
			settings = yaml.safe_load(file)

		settings["config_path"] = config_path

		load_dotenv(config_path / ".env")
		settings["text"]["api_key"] = os.getenv("SIEMENS_API_KEY")
		settings["stt"]["api_key"] = os.getenv("SIEMENS_API_KEY")
		settings["embedding"]["api_key"] = os.getenv("SIEMENS_API_KEY")
		settings["mcp"]["api_key"] = os.getenv("SIEMENS_API_KEY")
		settings["tts"]["api_key"] = os.getenv("ELEVENLABS_API_KEY")

		return settings
