"""MCP server for Exact Online API discovery, revenue, and financial reporting tools.

This module defines the FastMCP server instance and the tools:
- list_divisions: List accessible Exact Online divisions
- explore_endpoint: Explore any API endpoint with sample data
- list_endpoints: Browse known API endpoints by category
- get_revenue_by_period: Revenue totals by time period with YoY comparison
- get_revenue_by_customer: Customer revenue rankings
- get_revenue_by_project: Project-based revenue with hours
- get_profit_loss_overview: P&L summary with year-over-year comparison
- get_gl_account_balance: Balance for a specific GL account
- get_balance_sheet_summary: Balance sheet totals by category
- list_gl_account_balances: List accounts with balances, filterable
- get_aging_receivables: Outstanding customer invoices by age
- get_aging_payables: Outstanding supplier invoices by age
- get_gl_account_transactions: Drill down into individual transactions
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


# =============================================================================
# Financial Reporting Tools (Feature 001-balance-sheet-financial)
# =============================================================================


@mcp.tool()
async def get_profit_loss_overview(
    division: int | None = None,
) -> dict[str, Any]:
    """Get profit and loss overview with year-over-year comparison.

    Returns revenue, costs, and result for current year vs previous year.
    Also includes current period breakdown.

    Args:
        division: Division code. If not specified, uses current division.

    Returns:
        Dictionary with P&L data including year-over-year comparison.

    Example:
        >>> await get_profit_loss_overview()
        {
            "division": 1913290,
            "current_year": 2025,
            "previous_year": 2024,
            "currency_code": "EUR",
            "revenue_current_year": 971192.32,
            "revenue_previous_year": 942635.79,
            "costs_current_year": 835096.97,
            "costs_previous_year": 931079.75,
            "result_current_year": 136095.35,
            "result_previous_year": 11556.04
        }
    """
    try:
        client = get_client()

        # Get division if not specified
        if division is None:
            division = await client.get_current_division()

        overview = await client.fetch_profit_loss_overview(division)
        return overview.to_dict()

    except ExactOnlineError as e:
        logger.error(f"Error getting P&L overview: {e.message}")
        return e.to_dict()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"error": str(e), "action": "Check server logs for details"}


@mcp.tool()
async def get_gl_account_balance(
    account_code: str,
    year: int | None = None,
    period: int | None = None,
    division: int | None = None,
) -> dict[str, Any]:
    """Get the balance for a specific general ledger account (grootboekrekening).

    Returns amount, debit, credit for the specified period.

    Args:
        account_code: GL account code (e.g., '1300' for Debiteuren, '8000' for Omzet).
        year: Fiscal year. Defaults to current year.
        period: Reporting period (1-12). Defaults to current period.
        division: Division code. If not specified, uses current division.

    Returns:
        Dictionary with account balance information.

    Example:
        >>> await get_gl_account_balance("1300")
        {
            "gl_account_code": "1300",
            "gl_account_description": "Debiteuren",
            "amount": 138301.82,
            "amount_debit": 138301.82,
            "amount_credit": 0,
            "balance_type": "B",
            "account_type": 20,
            "account_type_description": "Accounts receivable",
            "reporting_year": 2024,
            "reporting_period": 12
        }
    """
    # Validate period if provided
    if period is not None and (period < 1 or period > 12):
        return {
            "error": "invalid_period",
            "message": f"Period must be between 1 and 12, got {period}",
            "action": "Provide a valid period number (1-12)",
        }

    try:
        client = get_client()

        # Get division if not specified
        if division is None:
            division = await client.get_current_division()

        # Look up GL account by code
        gl_account = await client.fetch_gl_account_by_code(division, account_code)
        if not gl_account:
            return {
                "error": "account_not_found",
                "message": f"GL account with code '{account_code}' not found",
                "action": "Verify the account code exists in this division",
            }

        gl_account_id = gl_account.get("ID")

        # Fetch reporting balance
        balance = await client.fetch_reporting_balance(
            division, gl_account_id, year=year, period=period
        )

        if not balance:
            return {
                "error": "no_balance_data",
                "message": f"No balance data found for account '{account_code}'",
                "action": "Check if the account has any transactions in the specified period",
                "gl_account_code": account_code,
                "gl_account_description": gl_account.get("Description", ""),
            }

        return {
            "gl_account_code": balance.get("GLAccountCode", account_code),
            "gl_account_description": balance.get("GLAccountDescription", ""),
            "amount": float(balance.get("Amount", 0) or 0),
            "amount_debit": float(balance.get("AmountDebit", 0) or 0),
            "amount_credit": float(balance.get("AmountCredit", 0) or 0),
            "balance_type": balance.get("BalanceType", ""),
            "account_type": balance.get("Type", 0),
            "account_type_description": balance.get("TypeDescription", ""),
            "reporting_year": balance.get("ReportingYear", 0),
            "reporting_period": balance.get("ReportingPeriod", 0),
        }

    except ExactOnlineError as e:
        logger.error(f"Error getting GL account balance: {e.message}")
        return e.to_dict()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"error": str(e), "action": "Check server logs for details"}


@mcp.tool()
async def get_balance_sheet_summary(
    year: int | None = None,
    period: int | None = None,
    division: int | None = None,
) -> dict[str, Any]:
    """Get balance sheet summary with assets, liabilities, and equity totals.

    Returns categorized totals grouped by account type.

    Args:
        year: Fiscal year. Defaults to current year.
        period: Reporting period (1-12). Defaults to current period.
        division: Division code. If not specified, uses current division.

    Returns:
        Dictionary with balance sheet categories and totals.

    Example:
        >>> await get_balance_sheet_summary()
        {
            "division": 1913290,
            "reporting_year": 2024,
            "reporting_period": 12,
            "currency_code": "EUR",
            "total_assets": 250000.00,
            "total_liabilities": 180000.00,
            "total_equity": 70000.00,
            "assets": [
                {"name": "Bank", "amount": 50000.00, "account_count": 3}
            ],
            "liabilities": [...],
            "equity": [...]
        }
    """
    # Validate period if provided
    if period is not None and (period < 1 or period > 12):
        return {
            "error": "invalid_period",
            "message": f"Period must be between 1 and 12, got {period}",
            "action": "Provide a valid period number (1-12)",
        }

    try:
        client = get_client()

        # Get division if not specified
        if division is None:
            division = await client.get_current_division()

        # Fetch all balance sheet balances
        balances = await client.fetch_all_balance_sheet_balances(
            division, year=year, period=period
        )

        if not balances:
            # Return empty summary with zeros
            from datetime import datetime as dt
            return {
                "division": division,
                "reporting_year": year or dt.now().year,
                "reporting_period": period or 1,
                "currency_code": "EUR",
                "total_assets": 0.0,
                "total_liabilities": 0.0,
                "total_equity": 0.0,
                "assets": [],
                "liabilities": [],
                "equity": [],
            }

        # Determine actual year/period from data
        actual_year = balances[0].get("ReportingYear", year or date.today().year)
        actual_period = balances[0].get("ReportingPeriod", period or 1)

        # Aggregate by category
        summary = client.aggregate_balances_by_category(
            balances, division, actual_year, actual_period
        )

        return summary.to_dict()

    except ExactOnlineError as e:
        logger.error(f"Error getting balance sheet summary: {e.message}")
        return e.to_dict()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"error": str(e), "action": "Check server logs for details"}


@mcp.tool()
async def list_gl_account_balances(
    balance_type: str | None = None,
    account_type: int | None = None,
    year: int | None = None,
    period: int | None = None,
    division: int | None = None,
) -> dict[str, Any]:
    """List all GL accounts with their balances, filterable by balance type or account type.

    Args:
        balance_type: Filter by balance type: 'B' for balance sheet, 'W' for P&L.
        account_type: Filter by account type code (e.g., 20 for receivables, 110 for revenue).
        year: Fiscal year. Defaults to current year.
        period: Reporting period (1-12). Defaults to current period.
        division: Division code. If not specified, uses current division.

    Returns:
        Dictionary with account list and totals.

    Example:
        >>> await list_gl_account_balances(balance_type="W")
        {
            "division": 1913290,
            "reporting_year": 2024,
            "reporting_period": 12,
            "total_accounts": 15,
            "accounts": [
                {
                    "gl_account_code": "8000",
                    "gl_account_description": "Omzet",
                    "amount": -86852.50,
                    "balance_type": "W",
                    "account_type": 110
                }
            ]
        }
    """
    # Validate balance_type if provided
    if balance_type is not None and balance_type not in ("B", "W"):
        return {
            "error": "invalid_balance_type",
            "message": f"balance_type must be 'B' or 'W', got '{balance_type}'",
            "action": "Use 'B' for balance sheet or 'W' for profit/loss accounts",
        }

    # Validate period if provided
    if period is not None and (period < 1 or period > 12):
        return {
            "error": "invalid_period",
            "message": f"Period must be between 1 and 12, got {period}",
            "action": "Provide a valid period number (1-12)",
        }

    try:
        client = get_client()

        # Get division if not specified
        if division is None:
            division = await client.get_current_division()

        # Fetch filtered balances
        accounts = await client.fetch_filtered_balances(
            division,
            balance_type=balance_type,
            account_type=account_type,
            year=year,
            period=period,
        )

        # Determine year/period from data or defaults
        actual_year = accounts[0].reporting_year if accounts else (year or date.today().year)
        actual_period = accounts[0].reporting_period if accounts else (period or 1)

        return {
            "division": division,
            "reporting_year": actual_year,
            "reporting_period": actual_period,
            "total_accounts": len(accounts),
            "accounts": [a.to_dict() for a in accounts],
        }

    except ExactOnlineError as e:
        logger.error(f"Error listing GL account balances: {e.message}")
        return e.to_dict()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"error": str(e), "action": "Check server logs for details"}


@mcp.tool()
async def get_aging_receivables(
    division: int | None = None,
) -> dict[str, Any]:
    """Get aging report for outstanding receivables (debiteuren).

    Shows amounts by aging bucket (0-30, 31-60, 61-90, >90 days).

    Args:
        division: Division code. If not specified, uses current division.

    Returns:
        Dictionary with aging totals and customer breakdown.

    Example:
        >>> await get_aging_receivables()
        {
            "division": 1913290,
            "currency_code": "EUR",
            "total_outstanding": 122603.26,
            "total_0_30": 108189.08,
            "total_31_60": 13213.20,
            "total_61_90": 0,
            "total_over_90": 1206.98,
            "customer_count": 5,
            "customers": [...]
        }
    """
    try:
        client = get_client()

        # Get division if not specified
        if division is None:
            division = await client.get_current_division()

        # Fetch aging receivables
        entries = await client.fetch_aging_receivables(division)

        # Calculate totals
        total_outstanding = sum(e.total_amount for e in entries)
        total_0_30 = sum(e.age_0_30 for e in entries)
        total_31_60 = sum(e.age_31_60 for e in entries)
        total_61_90 = sum(e.age_61_90 for e in entries)
        total_over_90 = sum(e.age_over_90 for e in entries)

        # Get currency from first entry or default
        currency_code = entries[0].currency_code if entries else "EUR"

        return {
            "division": division,
            "currency_code": currency_code,
            "total_outstanding": round(total_outstanding, 2),
            "total_0_30": round(total_0_30, 2),
            "total_31_60": round(total_31_60, 2),
            "total_61_90": round(total_61_90, 2),
            "total_over_90": round(total_over_90, 2),
            "customer_count": len(entries),
            "customers": [e.to_dict() for e in entries],
        }

    except ExactOnlineError as e:
        logger.error(f"Error getting aging receivables: {e.message}")
        return e.to_dict()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"error": str(e), "action": "Check server logs for details"}


@mcp.tool()
async def get_aging_payables(
    division: int | None = None,
) -> dict[str, Any]:
    """Get aging report for outstanding payables (crediteuren).

    Shows amounts by aging bucket (0-30, 31-60, 61-90, >90 days).

    Args:
        division: Division code. If not specified, uses current division.

    Returns:
        Dictionary with aging totals and supplier breakdown.

    Example:
        >>> await get_aging_payables()
        {
            "division": 1913290,
            "currency_code": "EUR",
            "total_outstanding": 30876.27,
            "total_0_30": 25000.00,
            "total_31_60": 5876.27,
            "total_61_90": 0,
            "total_over_90": 0,
            "supplier_count": 3,
            "suppliers": [...]
        }
    """
    try:
        client = get_client()

        # Get division if not specified
        if division is None:
            division = await client.get_current_division()

        # Fetch aging payables
        entries = await client.fetch_aging_payables(division)

        # Calculate totals
        total_outstanding = sum(e.total_amount for e in entries)
        total_0_30 = sum(e.age_0_30 for e in entries)
        total_31_60 = sum(e.age_31_60 for e in entries)
        total_61_90 = sum(e.age_61_90 for e in entries)
        total_over_90 = sum(e.age_over_90 for e in entries)

        # Get currency from first entry or default
        currency_code = entries[0].currency_code if entries else "EUR"

        return {
            "division": division,
            "currency_code": currency_code,
            "total_outstanding": round(total_outstanding, 2),
            "total_0_30": round(total_0_30, 2),
            "total_31_60": round(total_31_60, 2),
            "total_61_90": round(total_61_90, 2),
            "total_over_90": round(total_over_90, 2),
            "supplier_count": len(entries),
            "suppliers": [e.to_dict() for e in entries],
        }

    except ExactOnlineError as e:
        logger.error(f"Error getting aging payables: {e.message}")
        return e.to_dict()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"error": str(e), "action": "Check server logs for details"}


@mcp.tool()
async def get_gl_account_transactions(
    account_code: str,
    year: int | None = None,
    period: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 100,
    division: int | None = None,
) -> dict[str, Any]:
    """Get individual transactions for a specific GL account.

    Enables drill-down from account balance to transaction detail.

    Args:
        account_code: GL account code (e.g., '1300' for Debiteuren, '8000' for Omzet).
        year: Fiscal year filter. If not specified with period, uses date range or returns recent.
        period: Reporting period (1-12). Used with year parameter.
        start_date: Start date filter (YYYY-MM-DD). Alternative to year/period filtering.
        end_date: End date filter (YYYY-MM-DD). Used with start_date.
        limit: Maximum number of transactions to return (default 100, max 1000).
        division: Division code. If not specified, uses current division.

    Returns:
        Dictionary with account info and transaction list.

    Example:
        >>> await get_gl_account_transactions("1300", limit=50)
        {
            "division": 1913290,
            "gl_account_code": "1300",
            "gl_account_description": "Debiteuren",
            "total_transactions": 50,
            "transactions": [
                {
                    "id": "...",
                    "date": "2024-12-15",
                    "description": "Invoice #123",
                    "amount": 1500.00,
                    "entry_number": 2050294
                }
            ]
        }
    """
    # Validate limit
    if limit < 1:
        limit = 1
    elif limit > 1000:
        limit = 1000

    # Validate period if provided
    if period is not None and (period < 1 or period > 12):
        return {
            "error": "invalid_period",
            "message": f"Period must be between 1 and 12, got {period}",
            "action": "Provide a valid period number (1-12)",
        }

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

        # Look up GL account by code
        gl_account = await client.fetch_gl_account_by_code(division, account_code)
        if not gl_account:
            return {
                "error": "account_not_found",
                "message": f"GL account with code '{account_code}' not found",
                "action": "Verify the account code exists in this division",
            }

        gl_account_id = gl_account.get("ID")
        gl_account_description = gl_account.get("Description", "")

        # Fetch transaction lines
        transactions = await client.fetch_transaction_lines(
            division,
            gl_account_id,
            year=year,
            period=period,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

        return {
            "division": division,
            "gl_account_code": account_code,
            "gl_account_description": gl_account_description,
            "total_transactions": len(transactions),
            "transactions": [t.to_dict() for t in transactions],
        }

    except ExactOnlineError as e:
        logger.error(f"Error getting GL account transactions: {e.message}")
        return e.to_dict()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"error": str(e), "action": "Check server logs for details"}
