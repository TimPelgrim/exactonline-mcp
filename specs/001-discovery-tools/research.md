# Research: Discovery Tools

**Date**: 2025-12-22
**Feature**: 001-discovery-tools

## OAuth2 Authentication Flow

### Decision
Implement OAuth2 Authorization Code Flow with region-aware endpoints and automatic
token refresh mechanism.

### Rationale
- Exact Online requires Authorization Code flow for security
- Tokens have very short lifetimes (10 min access, 30 day refresh)
- Region-specific endpoints required (`.nl`, `.co.uk`, etc.)

### Implementation Details

**Flow Steps:**
1. User runs `uv run python -m exactonline_mcp.auth`
2. Browser opens to Exact Online login (region-specific)
3. User authorizes application access
4. Callback captures authorization code (valid 3 minutes, one-time use)
5. Backend exchanges code for access and refresh tokens
6. Tokens stored securely in system keyring or encrypted file

**Endpoint Structure:**
- Auth endpoint: `{base_url}/api/oauth2/auth`
- Token endpoint: `{base_url}/api/oauth2/token`
- API base: `{base_url}/api/v1/{division}/{resource}`

**Region Base URLs:**
- Netherlands: `https://start.exactonline.nl`
- United Kingdom: `https://start.exactonline.co.uk`
- Default to Netherlands for YipYip

### Alternatives Considered
- **Implicit Flow**: Not suitable; Exact Online recommends Authorization Code
- **Client Credentials**: Not applicable; requires user-delegated access
- **PKCE**: Not required for server-side MCP application

---

## Token Management

### Decision
Implement pre-emptive lazy token refresh before each API call with immediate
storage of new tokens.

### Rationale
- Access tokens expire in 10 minutes (very short!)
- Refresh tokens expire in 30 days
- When refresh is used, a NEW refresh token is returned (must store immediately)
- Re-using old refresh token invalidates ALL tokens

### Implementation Details

```python
# Before each API call:
if current_time >= (token_obtained_time + 9.5 minutes):
    refresh_tokens()
    store_new_tokens()
proceed_with_api_call()
```

**Storage:**
- Primary: System keyring (macOS Keychain, Windows Credential Manager, Linux Secret Service)
- Fallback: Encrypted JSON file in `~/.exactonline_mcp/`
- Store: access_token, refresh_token, obtained_at timestamp

### Alternatives Considered
- **On-Demand Refresh**: React to 401 errors; adds latency
- **Background Refresh**: Excessive complexity for MCP context
- **Token Caching Library**: Authlib possible, but manual implementation simpler

---

## API Client Architecture

### Decision
Use single shared `httpx.AsyncClient` instance with request queue and rate limiting.

### Rationale
- Connection pooling for efficiency
- Centralized rate limit tracking
- Consistent timeout handling (30 seconds)
- Proper resource cleanup

### Implementation Details

**Rate Limiting:**
- 60 calls/minute limit
- Track sliding window of request timestamps
- Sleep if approaching limit
- Exponential backoff on 429 responses

**Key Endpoints:**
- `GET /api/v1/current/Me?$select=CurrentDivision` - Get current division
- `GET /api/v1/{division}/hrm/Divisions` - List all accessible divisions
- `GET /api/v1/{division}/{category}/{resource}` - Any OData endpoint

### Alternatives Considered
- **Thread Pool with Rate Limiter**: Overkill; asyncio sufficient
- **Fixed Delays**: Inefficient; wastes time
- **No Rate Limiting**: Would hit 429 errors constantly

---

## MCP SDK Integration

### Decision
Use FastMCP high-level API with `@mcp.tool()` decorator for tool definitions.

### Rationale
- Official recommended approach from Anthropic
- Type annotations automatically generate JSON Schema
- Native async support for I/O operations
- Clean separation of concerns

### Implementation Details

**Server Structure:**
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="exactonline_mcp")

@mcp.tool()
async def list_divisions() -> list[dict]:
    """List all accessible divisions."""
    pass

@mcp.tool()
async def explore_endpoint(
    endpoint: str,
    division: int | None = None,
    top: int = 5
) -> dict:
    """Explore any endpoint with sample data."""
    pass

@mcp.tool()
def list_endpoints(category: str | None = None) -> list[dict]:
    """List known endpoints by category."""
    pass

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

**Critical Notes:**
- Use `transport="stdio"` for Claude Desktop integration
- Never write to stdout (corrupts JSON-RPC)
- Log to stderr or file only

### Alternatives Considered
- **Low-Level Server API**: More control but more boilerplate
- **Custom RPC Implementation**: Unnecessary; SDK handles protocol

---

## Error Handling Strategy

### Decision
Return structured error responses with user-friendly messages; never expose
tokens or raw exceptions.

### Rationale
- Constitution requires graceful failures
- Users need actionable error messages
- Security: no tokens in logs or responses

### Implementation Details

**Exception Hierarchy:**
```python
class ExactOnlineError(Exception):
    """Base exception"""

class AuthenticationError(ExactOnlineError):
    """Token expired or invalid"""

class RateLimitError(ExactOnlineError):
    """60 calls/minute exceeded"""

class DivisionNotAccessibleError(ExactOnlineError):
    """User lacks permission"""
```

**Error Response Pattern:**
```python
{
    "error": "Authentication expired",
    "action": "Run 'uv run python -m exactonline_mcp.auth' to re-authenticate"
}
```

### Alternatives Considered
- **Raw Exception Propagation**: Insecure; may expose sensitive data
- **HTTP Status Codes Only**: Not descriptive enough for users

---

## Known Endpoint Catalog

### Decision
Maintain static catalog of commonly-used Exact Online endpoints grouped by category.

### Rationale
- Improves discoverability for users
- No API call needed for `list_endpoints`
- Can expand based on discovery findings

### Categories and Initial Endpoints

| Category | Endpoints |
|----------|-----------|
| crm | Accounts, Contacts |
| sales | SalesInvoices, SalesOrders |
| financial | GLAccounts, Receivables, ReportingBalance |
| project | Projects, TimeTransactions |
| logistics | Items |
| system | Divisions, Me |

### Alternatives Considered
- **Dynamic Discovery from $metadata**: Complex; OData metadata parsing required
- **Empty Catalog**: Poor user experience; no starting point

---

## Summary

| Area | Decision | Key Detail |
|------|----------|------------|
| OAuth2 | Authorization Code Flow | Region-aware, 10-min access tokens |
| Token Storage | Keyring + encrypted fallback | Refresh before expiry |
| HTTP Client | Single httpx.AsyncClient | 30s timeout, rate limiting |
| MCP SDK | FastMCP with @mcp.tool() | STDIO transport |
| Errors | Structured responses | No tokens in messages |
| Endpoints | Static catalog | 5 categories, expandable |
