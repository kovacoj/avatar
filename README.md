# Phonagnosia

> Phonagnosia is an inability to discern the identity of a speaker by their voice.

This application is a proof of concept. A (streaming) chat bot that can take input in a form of audio stream and respond with an audio in the same language.

```bash
uv run --with mcp src/server.py # start the mcp server
uv run python -m streamlit run src/app.py # start the streamlit app
```

**TODO**:
- [ ] Add custom MCP server to generate audio only when the user requests it
- [ ] STT is from code.siemens and it isn't capable of language detection, another choice is elevenlabs
- [ ] current STT also doesn't support streaming
