# Repo Notes

- Use `uv`, not plain `pip`. Lockfile is `uv.lock`; `pyproject.toml` requires Python `>=3.13`.
- Main local run path: `make start`. This backgrounds `uv run --with mcp src/server.py` and then starts Streamlit with `uv run python -m streamlit run src/app.py`.
- App depends on MCP server reachable at `config.config.yaml` `mcp.base_url`, defaulting to local `http://localhost:8000/mcp`. `src/config/config.py` also allows `MCP_BASE_URL` override from `config/.env`.

# Config

- Runtime config comes from repo-root `config/config.yaml` plus `config/.env` via `src.config.get_config()`.
- Config is cached with `functools.lru_cache(maxsize=1)`. Restart process after changing `config.yaml` or `.env`.
- Required secrets: `SIEMENS_API_KEY` feeds text/STT/embedding/MCP config; `ELEVENLABS_API_KEY` feeds TTS config.

# Entry Points

- `src/app.py`: Streamlit chat UI. Imports singleton service clients from `src/services/__init__.py`, so config/env load happens at import time.
- `src/server.py`: local FastMCP server. Current tool surface is only `sin`.
- `src/services/text.py`: async LLM client. Detects `en`/`cs`/`de`, streams response chunks, executes MCP tool calls against local server.
- `src/services/speech_to_text.py`: Siemens Whisper transcription client.
- `src/services/text_to_speech.py`: ElevenLabs streaming TTS, sentence by sentence via thread pool.
- Prompt templates live under `src/resources/templates/` and are loaded directly by `src/resources/__init__.py`.

# Verification

- No repo-configured `pytest`, lint, typecheck, or formatter targets found.
- Only explicit verification helper is `bash test.sh`. It sources `./config/.env` and posts `output/audio/anet.wav` to Siemens STT endpoint.
- Generated audio in `output/**/*.mp3` and `output/**/*.wav` is gitignored.
