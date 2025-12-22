"""Data models for Exact Online MCP server.

This module contains dataclasses representing the core entities used throughout
the application: Division, Token, Endpoint, and ExplorationResult.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Division:
    """Represents an Exact Online division (administratie).

    Args:
        code: Unique numeric division identifier (e.g., 7095).
        name: Display name of the division.
        is_current: Whether this is the user's default/current division.
    """

    code: int
    name: str
    is_current: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "code": self.code,
            "name": self.name,
            "is_current": self.is_current,
        }


@dataclass
class Token:
    """OAuth2 token pair for API authentication.

    Args:
        access_token: Bearer token for API calls (10 min lifetime).
        refresh_token: Token for obtaining new access token (30 day lifetime).
        obtained_at: Timestamp when tokens were obtained.
        expires_in: Seconds until access token expires (usually 600).
    """

    access_token: str
    refresh_token: str
    obtained_at: datetime
    expires_in: int = 600

    def is_expired(self, buffer_seconds: int = 30) -> bool:
        """Check if the access token is expired or about to expire.

        Args:
            buffer_seconds: Number of seconds before actual expiry to consider
                as expired (default 30 seconds for safety margin).

        Returns:
            True if token is expired or will expire within buffer_seconds.
        """
        elapsed = (datetime.now() - self.obtained_at).total_seconds()
        return elapsed >= (self.expires_in - buffer_seconds)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage (excluding sensitive display)."""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "obtained_at": self.obtained_at.isoformat(),
            "expires_in": self.expires_in,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Token":
        """Create Token from dictionary (e.g., from storage).

        Args:
            data: Dictionary containing token fields.

        Returns:
            Token instance.
        """
        obtained_at = data.get("obtained_at")
        if isinstance(obtained_at, str):
            obtained_at = datetime.fromisoformat(obtained_at)
        elif obtained_at is None:
            obtained_at = datetime.now()

        return cls(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            obtained_at=obtained_at,
            expires_in=int(data.get("expires_in", 600)),
        )


@dataclass
class Endpoint:
    """A known Exact Online API endpoint in the catalog.

    Args:
        path: API path (e.g., "crm/Accounts").
        category: Grouping category (crm, sales, financial, project, logistics).
        description: Human-readable description of the endpoint.
        typical_use: Example use case for this endpoint.
    """

    path: str
    category: str
    description: str
    typical_use: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "path": self.path,
            "category": self.category,
            "description": self.description,
            "typical_use": self.typical_use,
        }


@dataclass
class ExplorationResult:
    """Result of exploring an API endpoint.

    Args:
        endpoint: The requested endpoint path.
        division: Division code used for the query.
        count: Number of records returned.
        data: Sample records from the endpoint.
        available_fields: Field names found in the response.
    """

    endpoint: str
    division: int
    count: int
    data: list[dict[str, Any]] = field(default_factory=list)
    available_fields: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "endpoint": self.endpoint,
            "division": self.division,
            "count": self.count,
            "data": self.data,
            "available_fields": self.available_fields,
        }
