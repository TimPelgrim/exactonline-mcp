# exactonline-mcp

A Model Context Protocol (MCP) server providing read-only access to Exact Online accounting data.

## Installation

```bash
uv sync
```

## Authentication

Before using the server, authenticate with Exact Online:

```bash
uv run python -m exactonline_mcp.auth
```

This will:
1. Generate a self-signed SSL certificate for localhost (first run only)
2. Open a browser window for OAuth2 authentication
3. Store tokens securely in your system keyring

**Note**: Your browser may show a security warning for the self-signed certificate. Click "Advanced" and "Proceed to localhost" to continue.

**Exact Online App Setup**: Register your app with redirect URI `https://localhost:8080/callback`

## Configuration

Create a `.env` file with your Exact Online app credentials:

```env
EXACT_ONLINE_CLIENT_ID=your_client_id
EXACT_ONLINE_CLIENT_SECRET=your_client_secret
EXACT_ONLINE_REGION=nl  # or 'uk'
```

## Usage

### As MCP Server

Add to your Claude config:

```json
{
  "mcpServers": {
    "exactonline": {
      "command": "uv",
      "args": ["--directory", "/path/to/exactonline-mcp", "run", "python", "-m", "exactonline_mcp"],
      "env": {
        "EXACT_ONLINE_CLIENT_ID": "your_client_id",
        "EXACT_ONLINE_CLIENT_SECRET": "your_client_secret",
        "EXACT_ONLINE_REGION": "nl"
      }
    }
  }
}
```

## Available Tools

- **list_divisions** - List accessible Exact Online divisions
- **explore_endpoint** - Explore any API endpoint with sample data
- **list_endpoints** - Browse known API endpoints by category

## License

MIT
