
.PHONY: run-mcp run-app start test-stt

run-mcp:
	uv run --with mcp src/server.py

run-app:
	uv run python -m streamlit run src/app.py

start:
	@uv run --with mcp src/server.py & MCP_PID=$$!; trap 'kill $$MCP_PID' EXIT; uv run python -m streamlit run src/app.py

test-stt:
	bash test.sh
