from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class BaseConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TextConfig(BaseConfigModel):
    api_key: str | None = None
    base_url: str
    model: str
    mcp_url: str | None = None


class EmbeddingConfig(BaseConfigModel):
    api_key: str | None = None
    model: str


class MCPConfig(BaseConfigModel):
    api_key: str | None = None
    base_url: str


class SpeakerConfig(BaseConfigModel):
    name: str
    id: str
    language: str
    gender: str | None = None


class TTSConfig(BaseConfigModel):
    api_key: str | None = None
    model_id: str
    output_format: str = "mp3_22050_32"
    threads: int = Field(default=4, ge=1)
    speakers: list[SpeakerConfig] = Field(min_length=1)


class STTConfig(BaseConfigModel):
    api_key: str | None = None
    base_url: str
    model: str


class AppConfig(BaseConfigModel):
    title: str | None = None
    description: str | None = None
    text: TextConfig
    embedding: EmbeddingConfig
    mcp: MCPConfig
    tts: TTSConfig
    stt: STTConfig
    config_path: Path | None = None
