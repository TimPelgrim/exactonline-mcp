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

### Discovery Tools
- **list_divisions** - List accessible Exact Online divisions
- **explore_endpoint** - Explore any API endpoint with sample data
- **list_endpoints** - Browse known API endpoints by category

### Revenue Tools
- **get_revenue_by_period** - Revenue totals by month/quarter/year with year-over-year comparison
- **get_revenue_by_customer** - Customer revenue rankings with invoice counts
- **get_revenue_by_project** - Project-based revenue with optional hours tracking

### Financial Reporting Tools
- **get_profit_loss_overview** - P&L summary with year-over-year comparison
- **get_gl_account_balance** - Balance for a specific GL account (grootboekrekening)
- **get_balance_sheet_summary** - Balance sheet totals by category (assets, liabilities, equity)
- **list_gl_account_balances** - List accounts with balances, filterable by type
- **get_aging_receivables** - Outstanding customer invoices by age (0-30, 31-60, 61-90, >90 days)
- **get_aging_payables** - Outstanding supplier invoices by age
- **get_gl_account_transactions** - Drill down into individual transactions for an account

## Example Prompts

```
"Show me revenue by quarter for 2024"
"Who are our top 5 customers?"
"What's the revenue per project this year?"
"Compare Q1 revenue to last year"
"Show me the profit and loss overview"
"What's the balance on account 1300 (Debiteuren)?"
"Show me the balance sheet summary"
"List all P&L accounts with balances"
"Show aging receivables - who owes us money?"
"What transactions were made to account 8000 this year?"
```

## License

MIT
