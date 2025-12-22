"""Custom exceptions for Exact Online MCP server.

This module defines the exception hierarchy for handling various error conditions
when interacting with the Exact Online API.
"""


class ExactOnlineError(Exception):
    """Base exception for all Exact Online API errors.

    All custom exceptions in this module inherit from this class, allowing
    for broad exception handling when needed.
    """

    def __init__(self, message: str, action: str | None = None) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            action: Optional suggested action to resolve the error.
        """
        super().__init__(message)
        self.message = message
        self.action = action

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary for structured error responses."""
        result = {"error": self.message}
        if self.action:
            result["action"] = self.action
        return result


class AuthenticationError(ExactOnlineError):
    """Raised when authentication fails or tokens are invalid/expired.

    This error indicates that the user needs to re-authenticate, either because:
    - No tokens are stored
    - Access token is expired and refresh failed
    - Refresh token has expired (after 30 days of non-use)
    - Credentials are invalid
    """

    def __init__(
        self,
        message: str = "Authentication required",
        action: str = "Run 'uv run python -m exactonline_mcp.auth' to authenticate",
    ) -> None:
        """Initialize authentication error with default action."""
        super().__init__(message, action)


class RateLimitError(ExactOnlineError):
    """Raised when the Exact Online API rate limit is exceeded.

    The Exact Online API allows 60 calls per minute. This error is raised
    when that limit is exceeded and retry attempts have been exhausted.
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
    ) -> None:
        """Initialize rate limit error.

        Args:
            message: Error message.
            retry_after: Optional seconds to wait before retrying.
        """
        action = "Please wait before making more requests"
        if retry_after:
            action = f"Please wait {retry_after} seconds before retrying"
        super().__init__(message, action)
        self.retry_after = retry_after

    def to_dict(self) -> dict[str, str | int]:
        """Convert to dictionary including retry_after if available."""
        result = super().to_dict()
        if self.retry_after:
            result["retry_after"] = self.retry_after
        return result


class DivisionNotAccessibleError(ExactOnlineError):
    """Raised when user lacks permission for a specific division.

    This can occur when:
    - The division code doesn't exist
    - The user's account doesn't have access to the division
    - The division has been deactivated
    """

    def __init__(
        self,
        division: int,
        message: str | None = None,
    ) -> None:
        """Initialize division access error.

        Args:
            division: The division code that couldn't be accessed.
            message: Optional custom message.
        """
        if message is None:
            message = f"Division {division} is not accessible"
        action = "Use list_divisions to see available divisions"
        super().__init__(message, action)
        self.division = division


class EndpointNotFoundError(ExactOnlineError):
    """Raised when an API endpoint doesn't exist or is invalid.

    This error is raised when:
    - The endpoint path is malformed
    - The endpoint doesn't exist in Exact Online API
    - The endpoint exists but returns 404
    """

    def __init__(
        self,
        endpoint: str,
        message: str | None = None,
    ) -> None:
        """Initialize endpoint not found error.

        Args:
            endpoint: The endpoint path that wasn't found.
            message: Optional custom message.
        """
        if message is None:
            message = f"Endpoint '{endpoint}' not found"
        action = "Use list_endpoints to see available endpoints"
        super().__init__(message, action)
        self.endpoint = endpoint


class NetworkError(ExactOnlineError):
    """Raised when network connectivity issues occur.

    This error indicates transient network problems that may resolve
    with a retry. It wraps underlying httpx or connection errors.
    """

    def __init__(
        self,
        message: str = "Network error occurred",
        original_error: Exception | None = None,
    ) -> None:
        """Initialize network error.

        Args:
            message: Error message.
            original_error: The underlying exception that caused this error.
        """
        action = "Check your network connection and try again"
        super().__init__(message, action)
        self.original_error = original_error
