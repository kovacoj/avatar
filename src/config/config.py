import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import ValidationError
import yaml

from .models import AppConfig


class ConfigError(RuntimeError):
    pass


class Config:
    @classmethod
    def load(cls, config_path: Path | None = None) -> AppConfig:
        config_path = config_path or Path(__file__).parents[2] / "config"
        config_file = config_path / "config.yaml"

        with open(config_file, encoding="utf-8") as file:
            settings = yaml.safe_load(file) or {}

        if not isinstance(settings, dict):
            raise ConfigError(f"Invalid config root in {config_file}")

        load_dotenv(config_path / ".env")

        settings["config_path"] = config_path
        cls._set_api_keys(settings)

        text_settings = settings.setdefault("text", {})
        mcp_settings = settings.get("mcp") or {}
        text_settings["mcp_url"] = os.getenv("MCP_BASE_URL", mcp_settings.get("base_url"))

        try:
            return AppConfig.model_validate(settings)
        except ValidationError as exc:
            raise ConfigError(cls._format_validation_error(exc)) from exc

    @staticmethod
    def _format_validation_error(exc: ValidationError) -> str:
        errors = []
        for error in exc.errors():
            location = ".".join(str(part) for part in error["loc"])
            errors.append(f"{location}: {error['msg']}")
        return "Invalid config: " + "; ".join(errors)

    @staticmethod
    def _set_api_keys(settings: dict) -> None:
        siemens_api_key = os.getenv("SIEMENS_API_KEY")
        elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")

        settings.setdefault("text", {})["api_key"] = siemens_api_key
        settings.setdefault("stt", {})["api_key"] = siemens_api_key
        settings.setdefault("embedding", {})["api_key"] = siemens_api_key
        settings.setdefault("mcp", {})["api_key"] = siemens_api_key
        settings.setdefault("tts", {})["api_key"] = elevenlabs_api_key
