"""Exact Online API client with rate limiting and retry logic.

This module provides the ExactOnlineClient class for making authenticated
requests to the Exact Online REST API.
"""

import asyncio
import logging
import os
import time
from collections import defaultdict
from datetime import date, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx
from dotenv import load_dotenv

from exactonline_mcp.auth import OAuth2Client, get_base_url
from exactonline_mcp.exceptions import (
    AuthenticationError,
    DivisionNotAccessibleError,
    EndpointNotFoundError,
    ExactOnlineError,
    NetworkError,
    RateLimitError,
)
from exactonline_mcp.models import (
    CustomerRevenue,
    Division,
    ExplorationResult,
    ProjectRevenue,
    Token,
)

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for Exact Online API (60 calls/minute)."""

    MAX_CALLS_PER_MINUTE = 60

    def __init__(self) -> None:
        """Initialize rate limiter."""
        self._call_times: list[float] = []
        self._lock = asyncio.Lock()

    async def wait_if_needed(self) -> None:
        """Wait if we're approaching the rate limit.

        This method tracks API calls within a sliding 60-second window
        and sleeps if necessary to stay under the limit.
        """
        async with self._lock:
            now = time.time()

            # Remove calls older than 60 seconds
            self._call_times = [t for t in self._call_times if now - t < 60]

            # If at limit, wait until oldest call expires
            if len(self._call_times) >= self.MAX_CALLS_PER_MINUTE:
                oldest = self._call_times[0]
                wait_time = 60 - (now - oldest) + 0.1  # Small buffer
                if wait_time > 0:
                    logger.debug(f"Rate limit reached, waiting {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)
                    # Recheck after sleep
                    now = time.time()
                    self._call_times = [t for t in self._call_times if now - t < 60]

            # Record this call
            self._call_times.append(now)


class ExactOnlineClient:
    """Async HTTP client for Exact Online API.

    This client handles:
    - OAuth2 token management with automatic refresh
    - Rate limiting (60 calls/minute)
    - Retry logic with exponential backoff
    - Request timeout (30 seconds)
    """

    TIMEOUT = 30.0  # seconds
    MAX_RETRIES = 3
    RETRY_BACKOFF_BASE = 2  # seconds

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        region: str | None = None,
    ) -> None:
        """Initialize the Exact Online client.

        Args:
            client_id: OAuth2 client ID (or from EXACT_ONLINE_CLIENT_ID env var).
            client_secret: OAuth2 client secret (or from EXACT_ONLINE_CLIENT_SECRET env var).
            region: Region code 'nl' or 'uk' (or from EXACT_ONLINE_REGION env var).
        """
        load_dotenv()

        self.client_id = client_id or os.getenv("EXACT_ONLINE_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("EXACT_ONLINE_CLIENT_SECRET", "")
        self.region = region or os.getenv("EXACT_ONLINE_REGION", "nl")

        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Missing EXACT_ONLINE_CLIENT_ID or EXACT_ONLINE_CLIENT_SECRET"
            )

        self.base_url = get_base_url(self.region)
        self.oauth_client = OAuth2Client(
            self.client_id, self.client_secret, self.region
        )
        self.rate_limiter = RateLimiter()
        self._http_client: httpx.AsyncClient | None = None
        self._current_token: Token | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client.

        Returns:
            Configured AsyncClient instance.
        """
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=self.TIMEOUT,
                limits=httpx.Limits(max_keepalive_connections=5),
            )
        return self._http_client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    async def _ensure_authenticated(self) -> str:
        """Ensure we have a valid access token.

        Returns:
            Valid access token.

        Raises:
            AuthenticationError: If authentication fails.
        """
        # Get token from storage if not cached, or if expired
        if self._current_token is None or self._current_token.is_expired():
            self._current_token = await self.oauth_client.get_valid_token()

        return self._current_token.access_token

    async def _request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make an authenticated HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.).
            url: Full URL to request.
            **kwargs: Additional arguments for httpx.request.

        Returns:
            HTTP response.

        Raises:
            ExactOnlineError: On API errors.
            NetworkError: On connection errors.
        """
        client = await self._get_client()

        for attempt in range(self.MAX_RETRIES):
            try:
                # Ensure rate limit compliance
                await self.rate_limiter.wait_if_needed()

                # Get fresh token
                access_token = await self._ensure_authenticated()

                # Set authorization header
                headers = kwargs.pop("headers", {})
                headers["Authorization"] = f"Bearer {access_token}"
                headers["Accept"] = "application/json"

                # Make request
                response = await client.request(method, url, headers=headers, **kwargs)

                # Handle rate limit
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    if attempt < self.MAX_RETRIES - 1:
                        logger.warning(
                            f"Rate limited, waiting {retry_after}s (attempt {attempt + 1})"
                        )
                        await asyncio.sleep(retry_after)
                        continue
                    raise RateLimitError(retry_after=retry_after)

                # Handle auth errors
                if response.status_code == 401:
                    # Token might have been revoked, clear and retry
                    self._current_token = None
                    if attempt < self.MAX_RETRIES - 1:
                        logger.warning("Auth error, refreshing token...")
                        continue
                    raise AuthenticationError()

                # Handle not found
                if response.status_code == 404:
                    raise EndpointNotFoundError(url.split("/api/v1/")[-1])

                # Handle forbidden (division access)
                if response.status_code == 403:
                    raise DivisionNotAccessibleError(
                        division=0,  # Will be set by caller
                        message="Access denied to this resource",
                    )

                # Handle other errors
                if response.status_code >= 400:
                    error_msg = f"API error: {response.status_code}"
                    try:
                        error_data = response.json()
                        if "error" in error_data:
                            error_msg = error_data["error"].get(
                                "message", {}).get("value", error_msg
                            )
                    except Exception:
                        pass
                    raise ExactOnlineError(error_msg)

                return response

            except httpx.TimeoutException as e:
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = self.RETRY_BACKOFF_BASE ** attempt
                    logger.warning(f"Timeout, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                raise NetworkError("Request timed out", e) from e

            except httpx.RequestError as e:
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = self.RETRY_BACKOFF_BASE ** attempt
                    logger.warning(f"Network error, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                raise NetworkError("Network connection failed", e) from e

        raise ExactOnlineError("Max retries exceeded")

    async def get_current_division(self) -> int:
        """Get the current user's default division.

        Returns:
            Division code.

        Raises:
            ExactOnlineError: On API errors.
        """
        url = f"{self.base_url}/api/v1/current/Me?$select=CurrentDivision"
        response = await self._request("GET", url)
        data = response.json()

        # Exact Online returns data in 'd.results' array
        results = data.get("d", {}).get("results", [])
        if results:
            return results[0].get("CurrentDivision")
        return None

    async def get_divisions(self) -> list[Division]:
        """Get all accessible divisions.

        Returns:
            List of Division objects sorted by name.

        Raises:
            ExactOnlineError: On API errors.
        """
        current_division = await self.get_current_division()

        url = f"{self.base_url}/api/v1/{current_division}/hrm/Divisions"
        url += "?$select=Code,Description,HID&$orderby=Description"

        response = await self._request("GET", url)
        data = response.json()

        results = data.get("d", {}).get("results", [])

        divisions = []
        for item in results:
            code = item.get("Code")
            if code is not None:
                divisions.append(
                    Division(
                        code=code,
                        name=item.get("Description", f"Division {code}"),
                        is_current=(code == current_division),
                    )
                )

        return sorted(divisions, key=lambda d: d.name)

    async def get(
        self,
        endpoint: str,
        division: int,
        select: str | None = None,
        filter: str | None = None,
        top: int | None = None,
        skip: int | None = None,
        orderby: str | None = None,
    ) -> dict[str, Any]:
        """Make a GET request to any Exact Online API endpoint.

        Args:
            endpoint: API endpoint path (e.g., "crm/Accounts").
            division: Division code.
            select: OData $select parameter.
            filter: OData $filter parameter.
            top: OData $top parameter (max records).
            skip: OData $skip parameter (pagination offset).
            orderby: OData $orderby parameter.

        Returns:
            API response data.

        Raises:
            ExactOnlineError: On API errors.
        """
        url = f"{self.base_url}/api/v1/{division}/{endpoint}"

        # Build query parameters
        params = {}
        if select:
            params["$select"] = select
        if filter:
            params["$filter"] = filter
        if top:
            params["$top"] = str(top)
        if skip:
            params["$skip"] = str(skip)
        if orderby:
            params["$orderby"] = orderby

        if params:
            url += "?" + urlencode(params)

        try:
            response = await self._request("GET", url)
            return response.json()
        except DivisionNotAccessibleError as e:
            raise DivisionNotAccessibleError(division) from e

    async def explore_endpoint(
        self,
        endpoint: str,
        division: int | None = None,
        top: int = 5,
        select: str | None = None,
        filter: str | None = None,
    ) -> ExplorationResult:
        """Explore an API endpoint and return sample data with field info.

        Args:
            endpoint: API endpoint path (e.g., "crm/Accounts").
            division: Division code (defaults to first available).
            top: Max records to return (capped at 25).
            select: OData $select parameter.
            filter: OData $filter parameter.

        Returns:
            ExplorationResult with sample data and available fields.

        Raises:
            ExactOnlineError: On API errors.
        """
        # Cap top at 25 for exploration
        top = min(top, 25)

        # Get default division if not specified
        if division is None:
            divisions = await self.get_divisions()
            if not divisions:
                raise ExactOnlineError("No accessible divisions found")
            division = divisions[0].code

        # Fetch data
        data = await self.get(
            endpoint=endpoint,
            division=division,
            select=select,
            filter=filter,
            top=top,
        )

        # Extract results - handle both d.results (system endpoints) and d as array (data endpoints)
        d = data.get("d", [])
        if isinstance(d, dict):
            results = d.get("results", [])
        else:
            results = d if isinstance(d, list) else []

        # Extract available fields from first record
        available_fields: list[str] = []
        if results:
            first_record = results[0]
            available_fields = [
                k for k in first_record
                if not k.startswith("__") and k != "__metadata"
            ]

        return ExplorationResult(
            endpoint=endpoint,
            division=division,
            count=len(results),
            data=results,
            available_fields=sorted(available_fields),
        )

    # =========================================================================
    # Revenue Helper Functions (Feature 002-revenue-tools)
    # =========================================================================

    async def get_all_paginated(
        self,
        endpoint: str,
        division: int,
        select: str | None = None,
        filter: str | None = None,
        orderby: str | None = None,
        page_size: int = 1000,
    ) -> list[dict[str, Any]]:
        """Fetch all records from an endpoint with automatic pagination.

        Args:
            endpoint: API endpoint path.
            division: Division code.
            select: OData $select parameter.
            filter: OData $filter parameter.
            orderby: OData $orderby parameter.
            page_size: Records per page (max 1000).

        Returns:
            List of all records from the endpoint.
        """
        all_results: list[dict[str, Any]] = []
        skip = 0

        while True:
            data = await self.get(
                endpoint=endpoint,
                division=division,
                select=select,
                filter=filter,
                top=page_size,
                skip=skip,
                orderby=orderby,
            )

            # Extract results
            d = data.get("d", [])
            if isinstance(d, dict):
                results = d.get("results", [])
            else:
                results = d if isinstance(d, list) else []

            if not results:
                break

            all_results.extend(results)

            # If we got fewer than page_size, we're done
            if len(results) < page_size:
                break

            skip += page_size

        return all_results

    def build_date_filter(
        self,
        start_date: str,
        end_date: str,
        date_field: str = "InvoiceDate",
    ) -> str:
        """Build OData filter for date range.

        Args:
            start_date: Start date in ISO format (YYYY-MM-DD).
            end_date: End date in ISO format (YYYY-MM-DD).
            date_field: Name of the date field to filter on.

        Returns:
            OData filter string.
        """
        return (
            f"{date_field} ge datetime'{start_date}' and "
            f"{date_field} le datetime'{end_date}'"
        )

    def get_period_boundaries(
        self,
        start_date: str,
        end_date: str,
        group_by: str,
    ) -> list[tuple[str, str, str]]:
        """Generate period boundaries for grouping.

        Args:
            start_date: Start date in ISO format (YYYY-MM-DD).
            end_date: End date in ISO format (YYYY-MM-DD).
            group_by: Grouping type - 'month', 'quarter', or 'year'.

        Returns:
            List of (period_key, period_start, period_end) tuples.
        """
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        periods: list[tuple[str, str, str]] = []

        if group_by == "year":
            current_year = start.year
            while current_year <= end.year:
                period_start = date(current_year, 1, 1)
                period_end = date(current_year, 12, 31)
                # Clamp to requested range
                period_start = max(period_start, start)
                period_end = min(period_end, end)
                periods.append((
                    str(current_year),
                    period_start.isoformat(),
                    period_end.isoformat(),
                ))
                current_year += 1

        elif group_by == "quarter":
            current = start
            while current <= end:
                quarter = (current.month - 1) // 3 + 1
                quarter_start_month = (quarter - 1) * 3 + 1
                quarter_end_month = quarter * 3
                period_start = date(current.year, quarter_start_month, 1)
                # Get last day of quarter
                if quarter_end_month == 12:
                    period_end = date(current.year, 12, 31)
                else:
                    period_end = date(current.year, quarter_end_month + 1, 1) - timedelta(days=1)
                # Clamp to requested range
                period_start = max(period_start, start)
                period_end = min(period_end, end)
                period_key = f"{current.year}-Q{quarter}"
                periods.append((
                    period_key,
                    period_start.isoformat(),
                    period_end.isoformat(),
                ))
                # Move to next quarter
                if quarter == 4:
                    current = date(current.year + 1, 1, 1)
                else:
                    current = date(current.year, quarter_end_month + 1, 1)

        else:  # month
            current = start
            while current <= end:
                period_start = date(current.year, current.month, 1)
                # Get last day of month
                if current.month == 12:
                    period_end = date(current.year, 12, 31)
                else:
                    period_end = date(current.year, current.month + 1, 1) - timedelta(days=1)
                # Clamp to requested range
                period_start = max(period_start, start)
                period_end = min(period_end, end)
                period_key = f"{current.year}-{current.month:02d}"
                periods.append((
                    period_key,
                    period_start.isoformat(),
                    period_end.isoformat(),
                ))
                # Move to next month
                if current.month == 12:
                    current = date(current.year + 1, 1, 1)
                else:
                    current = date(current.year, current.month + 1, 1)

        return periods

    async def fetch_invoices_for_date_range(
        self,
        division: int,
        start_date: str,
        end_date: str,
    ) -> list[dict[str, Any]]:
        """Fetch all processed invoices for a date range.

        Args:
            division: Division code.
            start_date: Start date in ISO format.
            end_date: End date in ISO format.

        Returns:
            List of invoice records with Status=50 (processed).
        """
        date_filter = self.build_date_filter(start_date, end_date)
        full_filter = f"Status eq 50 and {date_filter}"

        return await self.get_all_paginated(
            endpoint="salesinvoice/SalesInvoices",
            division=division,
            select="InvoiceID,InvoiceDate,AmountDC,InvoiceTo,InvoiceToName",
            filter=full_filter,
        )

    def group_invoices_by_period(
        self,
        invoices: list[dict[str, Any]],
        periods: list[tuple[str, str, str]],
    ) -> dict[str, list[dict[str, Any]]]:
        """Group invoices by period based on InvoiceDate.

        Args:
            invoices: List of invoice records.
            periods: List of (period_key, start, end) tuples.

        Returns:
            Dictionary mapping period_key to list of invoices.
        """
        grouped: dict[str, list[dict[str, Any]]] = {p[0]: [] for p in periods}

        for invoice in invoices:
            invoice_date_str = invoice.get("InvoiceDate", "")
            if not invoice_date_str:
                continue

            # Parse Exact Online date format: "/Date(timestamp)/"
            if invoice_date_str.startswith("/Date("):
                timestamp_ms = int(invoice_date_str[6:-2].split("+")[0].split("-")[0])
                invoice_date = date.fromtimestamp(timestamp_ms / 1000)
            else:
                invoice_date = date.fromisoformat(invoice_date_str[:10])

            # Find matching period
            for period_key, period_start, period_end in periods:
                start = date.fromisoformat(period_start)
                end = date.fromisoformat(period_end)
                if start <= invoice_date <= end:
                    grouped[period_key].append(invoice)
                    break

        return grouped

    def calculate_period_revenue(
        self,
        invoices: list[dict[str, Any]],
    ) -> tuple[float, int]:
        """Calculate total revenue and invoice count.

        Args:
            invoices: List of invoice records.

        Returns:
            Tuple of (total_revenue, invoice_count).
        """
        total = sum(float(inv.get("AmountDC", 0) or 0) for inv in invoices)
        return (round(total, 2), len(invoices))

    def aggregate_by_customer(
        self,
        invoices: list[dict[str, Any]],
    ) -> list[CustomerRevenue]:
        """Aggregate invoices by customer.

        Args:
            invoices: List of invoice records.

        Returns:
            List of CustomerRevenue sorted by revenue descending.
        """
        customer_data: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"name": "", "revenue": 0.0, "count": 0}
        )

        total_revenue = 0.0
        for inv in invoices:
            customer_id = inv.get("InvoiceTo") or "unknown"
            customer_name = inv.get("InvoiceToName") or "Unknown"
            amount = float(inv.get("AmountDC", 0) or 0)

            customer_data[customer_id]["name"] = customer_name
            customer_data[customer_id]["revenue"] += amount
            customer_data[customer_id]["count"] += 1
            total_revenue += amount

        # Create CustomerRevenue objects with percentage
        customers: list[CustomerRevenue] = []
        for cust_id, data in customer_data.items():
            pct = (data["revenue"] / total_revenue * 100) if total_revenue > 0 else 0
            customers.append(CustomerRevenue(
                customer_id=cust_id,
                customer_name=data["name"],
                revenue=round(data["revenue"], 2),
                invoice_count=data["count"],
                percentage_of_total=round(pct, 2),
            ))

        # Sort by revenue descending
        customers.sort(key=lambda c: c.revenue, reverse=True)
        return customers

    async def fetch_invoice_lines_with_projects(
        self,
        division: int,
    ) -> list[dict[str, Any]]:
        """Fetch invoice lines that have project references.

        Args:
            division: Division code.

        Returns:
            List of invoice line records with Project != null.

        Note:
            SalesInvoiceLines doesn't have direct date filter.
            Date filtering should be done client-side if needed.
        """
        return await self.get_all_paginated(
            endpoint="salesinvoice/SalesInvoiceLines",
            division=division,
            select="ID,InvoiceID,Project,AmountDC",
            filter="Project ne null",
        )

    async def fetch_projects(
        self,
        division: int,
    ) -> dict[str, dict[str, Any]]:
        """Fetch project metadata.

        Args:
            division: Division code.

        Returns:
            Dictionary mapping project ID to project data.
        """
        projects = await self.get_all_paginated(
            endpoint="project/Projects",
            division=division,
            select="ID,Code,Description,Account,AccountName",
        )

        project_map: dict[str, dict[str, Any]] = {}
        for proj in projects:
            proj_id = proj.get("ID")
            if proj_id:
                project_map[proj_id] = proj

        return project_map

    async def fetch_time_transactions(
        self,
        division: int,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, float]:
        """Fetch hours from TimeTransactions by project.

        Args:
            division: Division code.
            start_date: Optional start date filter.
            end_date: Optional end date filter.

        Returns:
            Dictionary mapping project ID to total hours.
        """
        filter_parts = []
        if start_date and end_date:
            filter_parts.append(self.build_date_filter(start_date, end_date, "Date"))

        transactions = await self.get_all_paginated(
            endpoint="project/TimeTransactions",
            division=division,
            select="ID,Project,Quantity",
            filter=" and ".join(filter_parts) if filter_parts else None,
        )

        hours_by_project: dict[str, float] = defaultdict(float)
        for tx in transactions:
            proj_id = tx.get("Project")
            quantity = tx.get("Quantity", 0) or 0
            if proj_id:
                hours_by_project[proj_id] += float(quantity)

        return dict(hours_by_project)

    def aggregate_by_project(
        self,
        invoice_lines: list[dict[str, Any]],
        project_metadata: dict[str, dict[str, Any]],
        hours_data: dict[str, float] | None = None,
    ) -> list[ProjectRevenue]:
        """Aggregate invoice lines by project.

        Args:
            invoice_lines: List of invoice line records.
            project_metadata: Dictionary of project data by ID.
            hours_data: Optional dictionary of hours by project ID.

        Returns:
            List of ProjectRevenue sorted by revenue descending.
        """
        project_data: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"revenue": 0.0, "count": 0}
        )

        for line in invoice_lines:
            proj_id = line.get("Project")
            if not proj_id:
                continue
            amount = float(line.get("AmountDC", 0) or 0)
            project_data[proj_id]["revenue"] += amount
            project_data[proj_id]["count"] += 1

        # Build ProjectRevenue objects
        projects: list[ProjectRevenue] = []
        for proj_id, data in project_data.items():
            metadata = project_metadata.get(proj_id, {})
            hours = hours_data.get(proj_id) if hours_data else None

            projects.append(ProjectRevenue(
                project_id=proj_id,
                project_code=metadata.get("Code", ""),
                project_name=metadata.get("Description", "Unknown Project"),
                client_id=metadata.get("Account"),
                client_name=metadata.get("AccountName"),
                revenue=round(data["revenue"], 2),
                invoice_count=data["count"],
                hours=round(hours, 2) if hours is not None else None,
            ))

        # Sort by revenue descending
        projects.sort(key=lambda p: p.revenue, reverse=True)
        return projects
