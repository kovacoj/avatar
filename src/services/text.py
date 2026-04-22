import asyncio
from dataclasses import dataclass
import json
import logging
import re
from typing import AsyncGenerator, Literal

from pydantic import BaseModel
from fastmcp import Client as MCPClient
from json_repair import repair_json
from openai import AsyncOpenAI

from src.config.models import TextConfig
from src.resources import user_prompt, system_prompt


logger = logging.getLogger(__name__)
PHRASE_SPLIT_PATTERN = re.compile(r"(?<=[.?!,;:\n])\s+")


@dataclass
class PendingToolCall:
    id: str | None = None
    name: str | None = None
    arguments: str = ""

class ISOLanguageCode(BaseModel):
    language: Literal["en", "cs", "de"]

class Client:
    def __init__(self, config: TextConfig):
        self.config = config
        self._validate_config()
        self.client = AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
        )
        self.mcp_url = self.config.mcp_url or "http://localhost:8000/mcp"

    async def __call__(self, prompt: str) -> AsyncGenerator[tuple[str, str], None]:
        language = await self._detect_language(prompt)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt.format(message=prompt)},
        ]

        try:
            async with MCPClient(self.mcp_url) as mcp:
                tools = await self._get_tools(mcp)
                async for sentence in self.clean_stream(self._stream_with_tools(messages, tools, mcp)):
                    yield sentence, language
                return
        except Exception as exc:
            logger.warning("MCP unavailable at %s: %s", self.mcp_url, exc)

        async for sentence in self.clean_stream(self._stream_with_tools(messages, [], None)):
            yield sentence, language

    async def _get_tools(self, mcp) -> list[dict]:
        mcp_tools = await mcp.list_tools()
        return [{
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema,
            },
        } for tool in mcp_tools]

    async def _detect_language(self, prompt: str) -> str:
        try:
            completion = await self.client.beta.chat.completions.parse(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": "Infer language: 'en', 'cs', or 'de'. Respond in JSON."},
                    {"role": "user", "content": prompt},
                ],
                response_format=ISOLanguageCode,
            )
            return completion.choices[0].message.parsed.language
        except Exception as exc:
            logger.warning("Language detection failed: %s", exc)
            return "en"

    async def _stream_with_tools(self, messages: list[dict], tools: list[dict], mcp) -> AsyncGenerator[str, None]:
        while True:
            response_stream = await self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                tools=tools if tools else None,
                stream=True,
            )

            tool_calls: dict[int, PendingToolCall] = {}
            full_content = ""

            async for chunk in response_stream:
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta

                if delta.content:
                    full_content += delta.content
                    yield delta.content

                if delta.tool_calls:
                    for tc_chunk in delta.tool_calls:
                        self._merge_tool_call_chunk(tool_calls, tc_chunk)

            complete_tool_calls = self._complete_tool_calls(tool_calls)
            if not complete_tool_calls:
                break

            messages.append({
                "role": "assistant",
                "content": full_content or None,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.name, "arguments": tc.arguments},
                    }
                    for tc in complete_tool_calls
                ],
            })

            if mcp is None:
                logger.warning("Model requested tool call, but MCP client unavailable")
                break

            for tc in complete_tool_calls:
                try:
                    args = self._parse_tool_arguments(tc.arguments)
                    result = await mcp.call_tool(tc.name, args)

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": str(result),
                    })
                except Exception as exc:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": f"Error: {exc}",
                    })

    async def clean_stream(self, stream_gen: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
        buffer = ""

        async for delta in stream_gen:
            buffer += delta
            phrases = PHRASE_SPLIT_PATTERN.split(buffer)

            if len(phrases) > 1:
                for phrase in phrases[:-1]:
                    if phrase.strip():
                        yield f" {phrase.strip()}"
                buffer = phrases[-1]

        if buffer.strip():
            yield f" {buffer.strip()}"

    def _validate_config(self) -> None:
        missing = [
            key for key in ("api_key", "base_url", "model")
            if not getattr(self.config, key)
        ]
        if missing:
            raise ValueError(f"Text config missing: {', '.join(missing)}")

    @staticmethod
    def _merge_tool_call_chunk(tool_calls: dict[int, PendingToolCall], tc_chunk) -> None:
        tool_call = tool_calls.setdefault(tc_chunk.index, PendingToolCall())
        if tc_chunk.id:
            tool_call.id = tc_chunk.id

        function = getattr(tc_chunk, "function", None)
        if function is None:
            return

        if getattr(function, "name", None):
            tool_call.name = function.name
        if getattr(function, "arguments", None):
            tool_call.arguments += function.arguments

    def _complete_tool_calls(self, tool_calls: dict[int, PendingToolCall]) -> list[PendingToolCall]:
        complete_calls = []
        for tool_call in tool_calls.values():
            if not tool_call.id or not tool_call.name:
                logger.warning("Skipping incomplete tool call chunk: %s", tool_call)
                continue
            complete_calls.append(tool_call)
        return complete_calls

    @staticmethod
    def _parse_tool_arguments(raw_arguments: str) -> dict:
        if not raw_arguments.strip():
            return {}

        try:
            parsed = json.loads(raw_arguments)
        except json.JSONDecodeError:
            repaired = repair_json(raw_arguments)
            parsed = json.loads(repaired)

        if not isinstance(parsed, dict):
            raise ValueError("Tool arguments must decode to JSON object")

        return parsed

async def main():
    from src.config import config

    ai_client = Client(config.text)
    prompt = "Use available tools if helpful. What is sin(0.5)?"

    async for sentence, lang in ai_client(prompt):
        print(f"[{lang}] {sentence}")

if __name__ == "__main__":
    asyncio.run(main())
