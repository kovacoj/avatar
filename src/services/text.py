import asyncio
import json
import logging
import re
from typing import Literal

from pydantic import BaseModel
from fastmcp import Client as MCPClient
from openai import AsyncOpenAI

from src.resources import user_prompt, system_prompt


logger = logging.getLogger(__name__)

class ISOLanguageCode(BaseModel):
    language: Literal["en", "cs", "de"]

class Client:
    def __init__(self, config):
        self.config = config
        self.client = AsyncOpenAI(
            api_key=self.config.get("api_key"),
            base_url=self.config.get("base_url"),
        )
        self.mcp_url = self.config.get("mcp_url", "http://localhost:8000/mcp")

    async def __call__(self, prompt):
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

    async def _get_tools(self, mcp):
        mcp_tools = await mcp.list_tools()
        return [{
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema,
            },
        } for tool in mcp_tools]

    async def _detect_language(self, prompt):
        try:
            completion = await self.client.beta.chat.completions.parse(
                model=self.config.get("model"),
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

    async def _stream_with_tools(self, messages, tools, mcp):
        while True:
            response_stream = await self.client.chat.completions.create(
                model=self.config.get("model"),
                messages=messages,
                tools=tools if tools else None,
                stream=True,
            )

            tool_calls = {}
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
                        idx = tc_chunk.index
                        if idx not in tool_calls:
                            tool_calls[idx] = {
                                "id": tc_chunk.id,
                                "name": tc_chunk.function.name,
                                "arguments": "",
                            }
                        if tc_chunk.function.arguments:
                            tool_calls[idx]["arguments"] += tc_chunk.function.arguments

            if not tool_calls:
                break

            messages.append({
                "role": "assistant",
                "content": full_content or None,
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {"name": tc["name"], "arguments": tc["arguments"]},
                    }
                    for tc in tool_calls.values()
                ],
            })

            if mcp is None:
                logger.warning("Model requested tool call, but MCP client unavailable")
                break

            for tc in tool_calls.values():
                try:
                    args = json.loads(tc["arguments"])
                    result = await mcp.call_tool(tc["name"], args)

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": str(result),
                    })
                except Exception as exc:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": f"Error: {exc}",
                    })

    async def clean_stream(self, stream_gen):
        buffer = ""
        phrase_split_pattern = re.compile(r"(?<=[.?!,;:\n])\s+")

        async for delta in stream_gen:
            buffer += delta
            phrases = phrase_split_pattern.split(buffer)

            if len(phrases) > 1:
                for phrase in phrases[:-1]:
                    if phrase.strip():
                        yield f" {phrase.strip()}"
                buffer = phrases[-1]

        if buffer.strip():
            yield f" {buffer.strip()}"

async def main():
    from src.config import config

    ai_client = Client(config.get("text"))
    prompt = "Use available tools if helpful. What is sin(0.5)?"

    async for sentence, lang in ai_client(prompt):
        print(f"[{lang}] {sentence}")

if __name__ == "__main__":
    asyncio.run(main())
