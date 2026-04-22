from textwrap import dedent

import pytest

from src.config import ConfigError
from src.config.config import Config


def write_config(tmp_path, content: str):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "config.yaml").write_text(dedent(content), encoding="utf-8")
    return config_dir


def test_load_config_returns_typed_model(monkeypatch, tmp_path):
    monkeypatch.setenv("SIEMENS_API_KEY", "siemens-key")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "elevenlabs-key")
    monkeypatch.setenv("MCP_BASE_URL", "http://override.local/mcp")

    config_dir = write_config(
        tmp_path,
        """
        title: Demo
        description: Demo config
        text:
          base_url: https://api.example.com
          model: gpt-test
        embedding:
          model: embed-test
        mcp:
          base_url: http://localhost:8000/mcp
        tts:
          model_id: eleven_v3
          speakers:
            - name: Katarina
              id: speaker-en
              language: en
        stt:
          base_url: https://api.example.com
          model: whisper-test
        """,
    )

    config = Config.load(config_dir)

    assert config.title == "Demo"
    assert config.text.api_key == "siemens-key"
    assert config.tts.api_key == "elevenlabs-key"
    assert config.text.mcp_url == "http://override.local/mcp"
    assert config.tts.speakers[0].language == "en"
    assert config.config_path == config_dir


def test_load_config_rejects_missing_required_values(tmp_path):
    config_dir = write_config(
        tmp_path,
        """
        text:
          base_url: https://api.example.com
          model: gpt-test
        embedding:
          model: embed-test
        mcp:
          base_url: http://localhost:8000/mcp
        tts:
          model_id: eleven_v3
          speakers: []
        stt:
          base_url: https://api.example.com
        """,
    )

    with pytest.raises(ConfigError, match=r"tts\.speakers|stt\.model"):
        Config.load(config_dir)
