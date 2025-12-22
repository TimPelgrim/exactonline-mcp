"""Exact Online MCP Server.

A Model Context Protocol server providing read-only access to Exact Online
accounting data for exploration and discovery purposes.
"""

__version__ = "0.1.0"

from exactonline_mcp.server import mcp

__all__ = ["mcp", "__version__"]
