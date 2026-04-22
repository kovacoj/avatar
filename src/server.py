from mcp.server.fastmcp import FastMCP

from src.resources import FPS_CONTEXT

mcp = FastMCP("phonagnosia-tools")

@mcp.tool()
def get_intro() -> str:
    return " ".join(FPS_CONTEXT["overview"])


@mcp.tool()
def list_capabilities(category: str = "capabilities") -> list[str]:
    if category not in FPS_CONTEXT:
        available = ", ".join(sorted(FPS_CONTEXT))
        raise ValueError(f"Unknown category '{category}'. Available: {available}")
    return FPS_CONTEXT[category]


@mcp.tool()
def search_capabilities(query: str) -> dict[str, list[str]]:
    query_lower = query.strip().lower()
    if not query_lower:
        raise ValueError("Query must not be empty")

    matches = {
        category: [item for item in values if query_lower in item.lower()]
        for category, values in FPS_CONTEXT.items()
    }
    return {category: values for category, values in matches.items() if values}

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
