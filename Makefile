
.PHONY: run-mcp run-app start test test-stt docker-build docker-run

run-mcp:
	uv run --with mcp src/server.py

run-app:
	uv run python -m streamlit run src/app.py

start:
	@uv run --with mcp src/server.py & MCP_PID=$$!; trap 'kill $$MCP_PID' EXIT; uv run python -m streamlit run src/app.py

test:
	uv run --group dev pytest

test-stt:
	bash test.sh

docker-build:
	docker build -t phonagnosia:local .

docker-run:
	docker run --rm -it -p 8501:8501 --env-file config/.env phonagnosia:local
