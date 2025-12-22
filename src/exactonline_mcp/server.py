"""MCP server for Exact Online API discovery tools.

This module defines the FastMCP server instance and the discovery tools:
- list_divisions: List accessible Exact Online divisions
- explore_endpoint: Explore any API endpoint with sample data
- list_endpoints: Browse known API endpoints by category
"""

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from exactonline_mcp.client import ExactOnlineClient
from exactonline_mcp.endpoints import KNOWN_ENDPOINTS, get_endpoints_by_category
from exactonline_mcp.exceptions import ExactOnlineError

# Configure logging to stderr (not stdout - would corrupt MCP protocol)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    name="exactonline-mcp",
    instructions="Read-only access to Exact Online accounting data for discovery and exploration",
)

# Lazy-initialized client (created on first tool call)
_client: ExactOnlineClient | None = None


def get_client() -> ExactOnlineClient:
    """Get or create the ExactOnlineClient instance.

    Returns:
        Configured ExactOnlineClient.
    """
    global _client
    if _client is None:
        _client = ExactOnlineClient()
    return _client


@mcp.tool()
async def list_divisions() -> list[dict[str, Any]]:
    """List all accessible Exact Online divisions (administraties).

    Returns a list of divisions the user has access to, including their
    numeric code, display name, and whether it's the current/default division.

    Returns:
        List of division dictionaries with 'code', 'name', and 'is_current' fields.

    Example:
        >>> await list_divisions()
        [
            {"code": 7095, "name": "YipYip BV", "is_current": True},
            {"code": 7096, "name": "YipYip Test", "is_current": False}
        ]
    """
    try:
        client = get_client()
        divisions = await client.get_divisions()
        return [d.to_dict() for d in divisions]
    except ExactOnlineError as e:
        logger.error(f"Error listing divisions: {e.message}")
        return [e.to_dict()]
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return [{"error": str(e), "action": "Check server logs for details"}]


@mcp.tool()
async def explore_endpoint(
    endpoint: str,
    division: int | None = None,
    top: int = 5,
    select: str | None = None,
    filter: str | None = None,
) -> dict[str, Any]:
    """Explore any Exact Online API endpoint with sample data.

    Retrieves sample records from the specified endpoint, along with a list
    of available fields. Use this to understand what data is available in
    each endpoint before building specific queries.

    Args:
        endpoint: API endpoint path (e.g., 'crm/Accounts', 'sales/SalesInvoices').
        division: Division code to query. If not specified, uses first available.
        top: Maximum number of records to return (1-25, default 5).
        select: Comma-separated list of fields to return (OData $select).
        filter: OData filter expression (e.g., "Name eq 'Acme'").

    Returns:
        Dictionary with 'endpoint', 'division', 'count', 'data', and 'available_fields'.

    Example:
        >>> await explore_endpoint("crm/Accounts", top=3)
        {
            "endpoint": "crm/Accounts",
            "division": 7095,
            "count": 3,
            "data": [...],
            "available_fields": ["ID", "Name", "Email", ...]
        }
    """
    # Validate endpoint format
    if not endpoint or "/" not in endpoint:
        return {
            "error": "Invalid endpoint format",
            "action": "Endpoint must be in format 'category/Resource' (e.g., 'crm/Accounts')",
        }

    # Validate top parameter
    if top < 1:
        top = 1
    elif top > 25:
        top = 25

    try:
        client = get_client()
        result = await client.explore_endpoint(
            endpoint=endpoint,
            division=division,
            top=top,
            select=select,
            filter=filter,
        )
        return result.to_dict()
    except ExactOnlineError as e:
        logger.error(f"Error exploring endpoint {endpoint}: {e.message}")
        return e.to_dict()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"error": str(e), "action": "Check server logs for details"}


@mcp.tool()
def list_endpoints(category: str | None = None) -> dict[str, Any]:
    """List known Exact Online API endpoints grouped by category.

    Returns a curated list of commonly-used Exact Online API endpoints,
    organized by category. Use this to discover what endpoints are available
    for exploration.

    Args:
        category: Filter by category (crm, sales, financial, project, logistics).
            If not specified, returns all categories.

    Returns:
        Dictionary with 'categories' containing endpoint lists grouped by category.

    Example:
        >>> list_endpoints(category="crm")
        {
            "categories": {
                "crm": [
                    {
                        "path": "crm/Accounts",
                        "description": "Customer and supplier accounts",
                        "typical_use": "Look up customer details"
                    },
                    ...
                ]
            }
        }
    """
    if category:
        # Validate category
        valid_categories = ["crm", "sales", "financial", "project", "logistics"]
        if category.lower() not in valid_categories:
            return {
                "error": f"Invalid category: {category}",
                "action": f"Valid categories: {', '.join(valid_categories)}",
            }

        endpoints = get_endpoints_by_category(category.lower())
        return {
            "categories": {
                category.lower(): [e.to_dict() for e in endpoints]
            }
        }

    # Return all categories
    categories: dict[str, list[dict[str, Any]]] = {}
    for ep in KNOWN_ENDPOINTS:
        if ep.category not in categories:
            categories[ep.category] = []
        categories[ep.category].append(ep.to_dict())

    return {"categories": categories}
