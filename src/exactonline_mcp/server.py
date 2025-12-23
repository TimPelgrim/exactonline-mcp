"""MCP server for Exact Online API discovery and revenue tools.

This module defines the FastMCP server instance and the tools:
- list_divisions: List accessible Exact Online divisions
- explore_endpoint: Explore any API endpoint with sample data
- list_endpoints: Browse known API endpoints by category
- get_revenue_by_period: Revenue totals by time period with YoY comparison
- get_revenue_by_customer: Customer revenue rankings
- get_revenue_by_project: Project-based revenue with hours
"""

import logging
from datetime import date, timedelta
from typing import Any

from mcp.server.fastmcp import FastMCP

from exactonline_mcp.client import ExactOnlineClient
from exactonline_mcp.endpoints import KNOWN_ENDPOINTS, get_endpoints_by_category
from exactonline_mcp.exceptions import ExactOnlineError
from exactonline_mcp.models import RevenuePeriod

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


# =============================================================================
# Revenue Tools (Feature 002-revenue-tools)
# =============================================================================


@mcp.tool()
async def get_revenue_by_period(
    start_date: str,
    end_date: str,
    group_by: str = "month",
    division: int | None = None,
) -> dict[str, Any]:
    """Get revenue totals grouped by time period with year-over-year comparison.

    Returns revenue for each period within the date range, along with comparison
    to the same period in the previous year. Revenue is calculated from processed
    (finalized) sales invoices only.

    Args:
        start_date: Start date in ISO format (YYYY-MM-DD).
        end_date: End date in ISO format (YYYY-MM-DD).
        group_by: Period grouping - 'month', 'quarter', or 'year' (default 'month').
        division: Division code. If not specified, uses current division.

    Returns:
        Dictionary with division, date range, totals, and period breakdown.

    Example:
        >>> await get_revenue_by_period("2024-01-01", "2024-12-31", group_by="quarter")
        {
            "division": 7095,
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "group_by": "quarter",
            "total_revenue": 150000.00,
            "total_invoices": 245,
            "periods": [
                {
                    "period_key": "2024-Q1",
                    "revenue": 35000.00,
                    "invoice_count": 58,
                    "previous_revenue": 32000.00,
                    "change_percentage": 9.38
                },
                ...
            ]
        }
    """
    # Validate date range
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        if start > end:
            return {
                "error": "invalid_date_range",
                "message": "start_date must be before or equal to end_date",
                "action": "Provide valid date range in ISO format (YYYY-MM-DD)",
            }
    except ValueError as e:
        return {
            "error": "invalid_date_format",
            "message": f"Invalid date format: {e}",
            "action": "Use ISO format: YYYY-MM-DD",
        }

    # Validate group_by
    if group_by not in ("month", "quarter", "year"):
        return {
            "error": "invalid_group_by",
            "message": f"Invalid group_by value: {group_by}",
            "action": "Use 'month', 'quarter', or 'year'",
        }

    try:
        client = get_client()

        # Get division if not specified
        if division is None:
            division = await client.get_current_division()

        # Get period boundaries
        periods = client.get_period_boundaries(start_date, end_date, group_by)

        # Fetch invoices for current period
        invoices = await client.fetch_invoices_for_date_range(
            division, start_date, end_date
        )

        # Group invoices by period
        grouped = client.group_invoices_by_period(invoices, periods)

        # Calculate previous year date range for comparison
        prev_start = (start - timedelta(days=365)).isoformat()
        prev_end = (end - timedelta(days=365)).isoformat()
        prev_periods = client.get_period_boundaries(prev_start, prev_end, group_by)

        # Fetch previous year invoices
        prev_invoices = await client.fetch_invoices_for_date_range(
            division, prev_start, prev_end
        )
        prev_grouped = client.group_invoices_by_period(prev_invoices, prev_periods)

        # Build period results with YoY comparison
        period_results: list[RevenuePeriod] = []
        total_revenue = 0.0
        total_invoices = 0

        for period_key, period_start, period_end in periods:
            revenue, count = client.calculate_period_revenue(grouped.get(period_key, []))
            total_revenue += revenue
            total_invoices += count

            # Find previous year period for comparison
            prev_key = _get_previous_year_period_key(period_key, group_by)
            prev_revenue, _ = client.calculate_period_revenue(
                prev_grouped.get(prev_key, [])
            )

            # Calculate change percentage
            change_pct = None
            if prev_revenue and prev_revenue != 0:
                change_pct = round((revenue - prev_revenue) / prev_revenue * 100, 2)

            period_results.append(RevenuePeriod(
                period_key=period_key,
                start_date=period_start,
                end_date=period_end,
                revenue=revenue,
                invoice_count=count,
                previous_revenue=prev_revenue if prev_revenue else None,
                change_percentage=change_pct,
            ))

        return {
            "division": division,
            "start_date": start_date,
            "end_date": end_date,
            "group_by": group_by,
            "total_revenue": round(total_revenue, 2),
            "total_invoices": total_invoices,
            "periods": [p.to_dict() for p in period_results],
        }

    except ExactOnlineError as e:
        logger.error(f"Error getting revenue by period: {e.message}")
        return e.to_dict()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"error": str(e), "action": "Check server logs for details"}


def _get_previous_year_period_key(period_key: str, group_by: str) -> str:
    """Get the period key for the same period in the previous year.

    Args:
        period_key: Current period key (e.g., "2024-Q1", "2024-01", "2024").
        group_by: Period grouping type.

    Returns:
        Previous year period key.
    """
    if group_by == "year":
        return str(int(period_key) - 1)
    elif group_by == "quarter":
        year, quarter = period_key.split("-")
        return f"{int(year) - 1}-{quarter}"
    else:  # month
        year, month = period_key.split("-")
        return f"{int(year) - 1}-{month}"


@mcp.tool()
async def get_revenue_by_customer(
    division: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    top: int = 10,
) -> dict[str, Any]:
    """Get customer revenue rankings with metrics.

    Returns customers sorted by revenue descending, with invoice count and
    percentage of total revenue. Revenue is calculated from processed invoices.

    Args:
        division: Division code. If not specified, uses current division.
        start_date: Optional start date filter (YYYY-MM-DD).
        end_date: Optional end date filter (YYYY-MM-DD).
        top: Number of top customers to return (1-100, default 10).

    Returns:
        Dictionary with totals and customer breakdown.

    Example:
        >>> await get_revenue_by_customer(top=5)
        {
            "division": 7095,
            "total_revenue": 150000.00,
            "total_invoices": 245,
            "customer_count": 42,
            "customers": [
                {
                    "customer_id": "abc123-...",
                    "customer_name": "Acme Corporation",
                    "revenue": 45000.00,
                    "invoice_count": 24,
                    "percentage_of_total": 30.00
                },
                ...
            ]
        }
    """
    # Validate top parameter
    if top < 1:
        top = 1
    elif top > 100:
        top = 100

    # Validate date range if provided
    if start_date and end_date:
        try:
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)
            if start > end:
                return {
                    "error": "invalid_date_range",
                    "message": "start_date must be before or equal to end_date",
                    "action": "Provide valid date range in ISO format",
                }
        except ValueError as e:
            return {
                "error": "invalid_date_format",
                "message": f"Invalid date format: {e}",
                "action": "Use ISO format: YYYY-MM-DD",
            }

    try:
        client = get_client()

        # Get division if not specified
        if division is None:
            division = await client.get_current_division()

        # Fetch invoices
        if start_date and end_date:
            invoices = await client.fetch_invoices_for_date_range(
                division, start_date, end_date
            )
        else:
            # Fetch all processed invoices
            invoices = await client.get_all_paginated(
                endpoint="salesinvoice/SalesInvoices",
                division=division,
                select="InvoiceID,InvoiceDate,AmountDC,InvoiceTo,InvoiceToName",
                filter="Status eq 50",
            )

        # Aggregate by customer
        customers = client.aggregate_by_customer(invoices)

        # Calculate totals
        total_revenue = sum(c.revenue for c in customers)
        total_invoices = sum(c.invoice_count for c in customers)

        # Limit to top N
        top_customers = customers[:top]

        return {
            "division": division,
            "start_date": start_date,
            "end_date": end_date,
            "total_revenue": round(total_revenue, 2),
            "total_invoices": total_invoices,
            "customer_count": len(customers),
            "customers": [c.to_dict() for c in top_customers],
        }

    except ExactOnlineError as e:
        logger.error(f"Error getting revenue by customer: {e.message}")
        return e.to_dict()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"error": str(e), "action": "Check server logs for details"}


@mcp.tool()
async def get_revenue_by_project(
    division: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    include_hours: bool = True,
) -> dict[str, Any]:
    """Get project-based revenue with optional hours tracking.

    Returns projects with revenue from invoice lines and optionally logged hours
    from time transactions. Requires the project module to be enabled.

    Args:
        division: Division code. If not specified, uses current division.
        start_date: Optional start date filter (YYYY-MM-DD).
        end_date: Optional end date filter (YYYY-MM-DD).
        include_hours: Whether to fetch hours from TimeTransactions (default True).

    Returns:
        Dictionary with totals and project breakdown.

    Example:
        >>> await get_revenue_by_project()
        {
            "division": 7095,
            "total_revenue": 85000.00,
            "total_invoices": 156,
            "project_count": 12,
            "hours_available": true,
            "projects": [
                {
                    "project_id": "proj123-...",
                    "project_code": "P2024-001",
                    "project_name": "Website Redesign",
                    "client_name": "Acme Corporation",
                    "revenue": 25000.00,
                    "invoice_count": 8,
                    "hours": 320.5
                },
                ...
            ]
        }
    """
    # Validate date range if provided
    if start_date and end_date:
        try:
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)
            if start > end:
                return {
                    "error": "invalid_date_range",
                    "message": "start_date must be before or equal to end_date",
                    "action": "Provide valid date range in ISO format",
                }
        except ValueError as e:
            return {
                "error": "invalid_date_format",
                "message": f"Invalid date format: {e}",
                "action": "Use ISO format: YYYY-MM-DD",
            }

    try:
        client = get_client()

        # Get division if not specified
        if division is None:
            division = await client.get_current_division()

        # Fetch invoice lines with projects
        # Note: Date filtering for invoice lines is not supported at API level
        invoice_lines = await client.fetch_invoice_lines_with_projects(division)

        # Handle case where no project data exists
        if not invoice_lines:
            return {
                "division": division,
                "start_date": start_date,
                "end_date": end_date,
                "total_revenue": 0.0,
                "total_invoices": 0,
                "project_count": 0,
                "hours_available": False,
                "projects": [],
            }

        # Fetch project metadata
        project_metadata = await client.fetch_projects(division)

        # Fetch hours if requested
        hours_data = None
        if include_hours:
            try:
                hours_data = await client.fetch_time_transactions(
                    division, start_date=start_date, end_date=end_date
                )
            except ExactOnlineError:
                # Time transactions might not be available
                logger.warning("Could not fetch time transactions")
                hours_data = None

        # Aggregate by project
        projects = client.aggregate_by_project(
            invoice_lines, project_metadata, hours_data
        )

        # Calculate totals
        total_revenue = sum(p.revenue for p in projects)
        total_invoices = sum(p.invoice_count for p in projects)

        return {
            "division": division,
            "start_date": start_date,
            "end_date": end_date,
            "total_revenue": round(total_revenue, 2),
            "total_invoices": total_invoices,
            "project_count": len(projects),
            "hours_available": hours_data is not None,
            "projects": [p.to_dict() for p in projects],
        }

    except ExactOnlineError as e:
        logger.error(f"Error getting revenue by project: {e.message}")
        return e.to_dict()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"error": str(e), "action": "Check server logs for details"}
