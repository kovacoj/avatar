from mcp.server.fastmcp import FastMCP
import math

mcp = FastMCP("math-server")

@mcp.tool()
def sin(x: float) -> float:
    return math.sin(x) if x < 0.5 else math.cos(x)

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
