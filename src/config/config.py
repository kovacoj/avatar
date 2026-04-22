from pathlib import Path
import os
from dotenv import load_dotenv
import yaml


class Config:
    @classmethod
    def load(cls) -> dict:
        config_path = Path(__file__).parents[2] / "config"

        with open(config_path / "config.yaml", encoding="utf-8") as file:
            settings = yaml.safe_load(file)

        load_dotenv(config_path / ".env")

        settings["config_path"] = config_path
        settings["text"]["api_key"] = os.getenv("SIEMENS_API_KEY")
        settings["stt"]["api_key"] = os.getenv("SIEMENS_API_KEY")
        settings["embedding"]["api_key"] = os.getenv("SIEMENS_API_KEY")
        settings["mcp"]["api_key"] = os.getenv("SIEMENS_API_KEY")
        settings["tts"]["api_key"] = os.getenv("ELEVENLABS_API_KEY")
        settings["text"]["mcp_url"] = os.getenv("MCP_BASE_URL", settings["mcp"]["base_url"])

        return settings
