"""Exact Online API client with rate limiting and retry logic.

This module provides the ExactOnlineClient class for making authenticated
requests to the Exact Online REST API.
"""

import asyncio
import logging
import os
import time
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
from exactonline_mcp.models import Division, ExplorationResult, Token

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

        # Extract results
        results = data.get("d", {}).get("results", [])

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
