# Phonagnosia

Voice-first multilingual assistant built for live expo demos.

Project streams LLM text into Streamlit chat, transcribes microphone input with Siemens STT, calls MCP tools when available, and synthesizes spoken responses with ElevenLabs in same detected language.

Concrete use case: expo visitor asks about Siemens GBS CEE FPS capabilities in English, Czech, or German, and assistant answers in same language as spoken holographic colleague.

## Why this repo exists

This started as fast-turnaround expo prototype for holographic AI assistant demo. Repo now cleaned up to show practical full-stack AI integration work: real-time UX, voice I/O, prompt design, tool calling, and external service orchestration.

## Demo flow

1. Visitor types or records message in Streamlit UI.
2. Audio input goes through Siemens Whisper transcription.
3. Text service detects language (`en`, `cs`, `de`) and streams response from Siemens-hosted LLM.
4. LLM can call local MCP tools over `streamable-http`.
5. Response is converted to speech with ElevenLabs and played back in UI.

## Stack

- Python 3.13+
- `uv` for environment and dependency management
- Streamlit for chat UI
- Siemens LLM/STT endpoints via OpenAI-compatible SDK
- FastMCP for local tool server
- ElevenLabs for text-to-speech

## Quick start

```bash
uv sync
cp config/.env.example config/.env
make start
```

Open Streamlit URL shown in terminal. `make start` launches local MCP server and app together.

## Required environment variables

Set these in `config/.env`:

```bash
SIEMENS_API_KEY=...
ELEVENLABS_API_KEY=...
```

Optional override:

```bash
MCP_BASE_URL=http://localhost:8000/mcp
```

## Useful commands

```bash
make run-mcp   # start local MCP server only
make run-app   # start Streamlit app only
make start     # start both for local development
make test-stt  # post sample wav file to Siemens STT endpoint
```

## Project structure

- `src/app.py`: Streamlit chat UI
- `src/server.py`: local MCP server
- `src/services/text.py`: language detection, LLM streaming, MCP tool calls
- `src/services/speech_to_text.py`: Siemens Whisper wrapper
- `src/services/text_to_speech.py`: ElevenLabs streaming TTS
- `src/resources/templates/`: system and persona prompts
- `config/config.yaml`: runtime config

## Current limitations

- Voice input transcription currently assumes English because Siemens STT endpoint in this setup does not auto-detect language.
- TTS is generated after full text response is produced; audio playback is not sentence-streamed yet.
- Default MCP setup is local demo server with small tool surface.

## Portfolio note

Repo intentionally keeps implementation small and readable. Goal is not framework complexity; goal is showing end-to-end integration between multimodal UI, LLM orchestration, and tool-augmented inference.
