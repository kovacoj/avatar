from src.config.models import TextConfig
from src.services.text import Client, PendingToolCall


def build_text_client() -> Client:
    return Client(
        TextConfig(
            api_key="test-key",
            base_url="https://api.example.com",
            model="gpt-test",
            mcp_url="http://localhost:8000/mcp",
        )
    )


def test_parse_tool_arguments_repairs_malformed_json():
    client = build_text_client()

    parsed = client._parse_tool_arguments('{"x": 1, "label": "demo",}')

    assert parsed == {"x": 1, "label": "demo"}


def test_complete_tool_calls_skips_incomplete_entries():
    client = build_text_client()
    tool_calls = {
        0: PendingToolCall(id="tool-1", name="sin", arguments='{"x": 1}'),
        1: PendingToolCall(id="tool-2", name=None, arguments=""),
    }

    complete = client._complete_tool_calls(tool_calls)

    assert len(complete) == 1
    assert complete[0].name == "sin"
