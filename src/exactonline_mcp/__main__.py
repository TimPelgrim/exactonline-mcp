"""Entry point for running the Exact Online MCP server.

Run with: uv run python -m exactonline_mcp
Or use the mcp CLI: mcp run exactonline-mcp
"""

from exactonline_mcp.server import mcp


def main() -> None:
    """Run the MCP server with stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
