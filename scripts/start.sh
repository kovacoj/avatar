#!/usr/bin/env bash

set -euo pipefail

uv run python src/server.py &
MCP_PID=$!

cleanup() {
  kill "$MCP_PID" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

exec uv run python -m streamlit run src/app.py --server.address=0.0.0.0 --server.port=8501
