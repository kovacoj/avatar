import asyncio
import json
import re
from typing import Literal
from pydantic import BaseModel
from openai import AsyncOpenAI
from fastmcp import Client as MCPClient

# Ensure these are imported from your project structure
from src.resources import user_prompt, system_prompt

class ISOLanguageCode(BaseModel):
    language: Literal["en", "cs", "de"]

class Client:
    def __init__(self, config):
        self.config = config
        self.client = AsyncOpenAI(
            api_key=self.config.get('api_key'),
            base_url=self.config.get('base_url')
        )
        self.mcp_url = "http://localhost:8000/mcp"

    async def __call__(self, prompt):
        # 1. Detect language (must be awaited)
        language = await self._detect_language(prompt)
    
        async with MCPClient(self.mcp_url) as mcp:
            # 2. Get tools from MCP
            mcp_tools = await mcp.list_tools()
            tools = [{
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.inputSchema
                }
            } for t in mcp_tools]

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt.format(message=prompt)}
            ]

            # 3. Stream processing
            async for sentence in self.clean_stream(self._stream_with_tools(messages, tools, mcp)):
                yield sentence, language

    async def _detect_language(self, prompt):
        """Standardized parsing for the latest OpenAI SDK versions."""
        try:
            # Using the modern beta.parse for Pydantic support
            completion = await self.client.beta.chat.completions.parse(
                model=self.config.get('model'),
                messages=[
                    {"role": "system", "content": "Infer the language: 'en', 'cs', or 'de'. Respond in JSON."},
                    {"role": "user", "content": prompt},
                ],
                response_format=ISOLanguageCode,
            )
            return completion.choices[0].message.parsed.language
        except Exception as e:
            print(f"DEBUG: Language detection failed: {e}")
            return "en"

    async def _stream_with_tools(self, messages, tools, mcp):
        """Iterative loop for handling tool calls in a stream."""
        while True:
            response_stream = await self.client.chat.completions.create(
                model=self.config.get('model'),
                messages=messages,
                tools=tools if tools else None,
                stream=True
            )

            tool_calls = {}
            full_content = ""

            async for chunk in response_stream:
                if not chunk.choices:
                    continue
                
                delta = chunk.choices[0].delta

                # Text stream
                if delta.content:
                    full_content += delta.content
                    yield delta.content

                # Tool stream
                if delta.tool_calls:
                    for tc_chunk in delta.tool_calls:
                        idx = tc_chunk.index
                        if idx not in tool_calls:
                            tool_calls[idx] = {
                                "id": tc_chunk.id,
                                "name": tc_chunk.function.name,
                                "arguments": ""
                            }
                        if tc_chunk.function.arguments:
                            tool_calls[idx]["arguments"] += tc_chunk.function.arguments

            # Exit loop if no tools were called
            if not tool_calls:
                break

            # Append the assistant's request to call tools to history
            messages.append({
                "role": "assistant",
                "content": full_content or None,
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {"name": tc["name"], "arguments": tc["arguments"]}
                    } for tc in tool_calls.values()
                ]
            })

            # Execute tools locally
            for tc in tool_calls.values():
                try:
                    args = json.loads(tc["arguments"])
                    result = await mcp.call_tool(tc["name"], args)
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": str(result)
                    })
                except Exception as e:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": f"Error: {str(e)}"
                    })
            
            # The 'while True' loop will now call OpenAI again with the tool results

    async def clean_stream(self, stream_gen):
        """Sentence-level buffering."""
        buffer = ""
        phrase_split_pattern = re.compile(r'(?<=[.?!,;:\n])\s+')

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
    ai_client = Client(config.get('text'))
    
    prompt = "There's an MCP server that contains sin(x) function. Try to figure out what is wrong with its implementation. Make thorough analysis of its behaviour before answering! Use inputs in the range [0, 1]."
    
    async for sentence, lang in ai_client(prompt):
        print(f"[{lang}] {sentence}")

if __name__ == "__main__":
    asyncio.run(main())
