# Quickstart: Discovery Tools

## Prerequisites

1. **Python 3.11+** installed
2. **uv** package manager installed
3. **Exact Online developer account** with:
   - Client ID (OAuth2 app)
   - Client Secret
   - Redirect URI configured: `https://localhost:8080/callback`

## Setup

### 1. Clone and Install

```bash
cd exactonline-mcp
uv sync
```

### 2. Configure Environment

Create `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
EXACT_ONLINE_CLIENT_ID=your_client_id
EXACT_ONLINE_CLIENT_SECRET=your_client_secret
EXACT_ONLINE_REGION=nl  # or 'uk'
```

### 3. Authenticate

Run the OAuth2 authentication flow:

```bash
uv run python -m exactonline_mcp.auth
```

This will:
1. Generate a self-signed SSL certificate for localhost (first run only)
2. Open your browser to Exact Online login
3. After you authorize, capture the HTTPS callback
4. Store tokens securely in your system keyring

**Note**: Your browser may show a security warning for the self-signed certificate.
Click "Advanced" and "Proceed to localhost" to continue.

## Usage with Claude Desktop

### Configure Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "exactonline": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/exactonline-mcp",
        "run",
        "python",
        "-m",
        "exactonline_mcp"
      ]
    }
  }
}
```

**Important**: Use absolute path, not relative.

### Restart Claude Desktop

Completely quit and reopen Claude Desktop (not just close window).

## Available Tools

### list_divisions

List all accessible Exact Online divisions:

```
Use the list_divisions tool to see available administraties.
```

**Returns**: List of divisions with code, name, and current status.

### explore_endpoint

Explore any API endpoint with sample data:

```
Use explore_endpoint with endpoint "crm/Accounts" to see customer data.
```

**Parameters**:
- `endpoint` (required): API path like "crm/Accounts"
- `division`: Division code (optional, defaults to first)
- `top`: Number of records (1-25, default 5)
- `select`: Fields to return (comma-separated)
- `filter`: OData filter expression

### list_endpoints

Browse known endpoints by category:

```
Use list_endpoints to see available API endpoints.
Use list_endpoints with category "financial" for accounting endpoints.
```

**Categories**: crm, sales, financial, project, logistics

## Example Conversation

```
You: What divisions do I have access to?
Claude: [Uses list_divisions] You have access to 2 divisions:
- 7095: YipYip BV (current)
- 7096: YipYip Test

You: Show me some customer accounts
Claude: [Uses explore_endpoint with "crm/Accounts"] Here are 5 sample accounts:
- Acme Corp (ID: abc123)
- Beta Inc (ID: def456)
...

You: What financial endpoints are available?
Claude: [Uses list_endpoints with category "financial"]
- financial/GLAccounts: General ledger accounts
- cashflow/Receivables: Outstanding receivables
- financialtransaction/TransactionLines: Transaction lines (journal entries)
```

## Troubleshooting

### Browser shows "Your connection is not private"

This is expected! The auth flow uses a self-signed certificate. Click:
1. "Advanced" (or "Show Details")
2. "Proceed to localhost (unsafe)" or "visit this website"

### "Authentication required" error

Run the auth command again:

```bash
uv run python -m exactonline_mcp.auth
```

### "Rate limit exceeded" error

Wait 60 seconds before retrying. The API allows 60 calls per minute.

### Server not appearing in Claude

1. Check the config JSON syntax
2. Use absolute paths
3. Completely restart Claude Desktop (quit, not just close)
4. Check `~/Library/Logs/Claude/mcp*.log` for errors

### Token storage issues

If keyring is unavailable, tokens are stored encrypted in:
`~/.exactonline_mcp/tokens.json.enc`

SSL certificate is stored in:
`~/.exactonline_mcp/localhost.crt`

## Next Steps

After exploring the API with these discovery tools:

1. Identify which endpoints contain the data you need
2. Note the field names and data structures
3. Request specific business tools to be built (e.g., `get_outstanding_invoices`)
