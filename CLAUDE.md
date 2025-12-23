# exactonline-mcp Development Guidelines

Auto-generated from feature plans. Last updated: 2025-12-22

## Active Technologies

- **Language**: Python 3.11+
- **Package Manager**: uv
- **Dependencies**: mcp (Anthropic SDK), httpx, python-dotenv, keyring
- **Storage**: Keyring (system) or encrypted JSON for OAuth tokens

## Project Structure

```text
src/exactonline_mcp/
├── __init__.py
├── __main__.py      # Entry point
├── server.py        # MCP server + tools
├── auth.py          # OAuth2 flow
├── client.py        # API client
├── models.py        # Data models
├── endpoints.py     # Endpoint catalog
└── exceptions.py    # Custom exceptions

tests/
├── conftest.py
├── test_auth.py
├── test_client.py
└── test_tools.py
```

## Commands

```bash
# Install dependencies
uv sync

# Run auth flow
uv run python -m exactonline_mcp.auth

# Run MCP server (for testing)
uv run python -m exactonline_mcp

# Run tests
uv run pytest

# Lint
uv run ruff check .
```

## Code Style

- Type hints on all functions
- Google-style docstrings
- Async/await for all I/O
- No bare `except:` - catch specific exceptions

## Constitution Rules

- **Read-Only**: Only GET requests to Exact Online API
- **Security**: Never log tokens or credentials
- **Discovery-First**: Prefix tools with `explore_` or `list_`
- **Fail Gracefully**: Retry with backoff, clear error messages

## Recent Changes

- 002-revenue-tools: Revenue analysis tools (get_revenue_by_period, get_revenue_by_customer, get_revenue_by_project)
- 001-discovery-tools: Initial MCP server with discovery tools

<!-- MANUAL ADDITIONS START -->
## Implementation Notes

- FastMCP uses `instructions` parameter (not `description`) for server description
- Token refresh uses 30-second buffer before expiry for safety margin
- Rate limiter uses sliding 60-second window tracking
- Exact Online API response formats vary: `d.results` array (system) vs `d` direct array (data)
- OAuth requires external HTTPS tunnel (ngrok) - localhost URIs rejected

## Revenue Tools API Notes

- Revenue from `salesinvoice/SalesInvoices` - filter `Status eq 50` for processed
- Credit notes have negative AmountDC values
- Project field is on SalesInvoiceLines, not SalesInvoices
- TimeTransactions.Quantity = hours (when linked to time-based Item)
- Year-over-year comparison: same period last year (Q1 2024 vs Q1 2023)
<!-- MANUAL ADDITIONS END -->
