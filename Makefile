
.PHONY: start
start:
	@uv run --with mcp src/server.py &
	uv run python -m streamlit run src/app.py
