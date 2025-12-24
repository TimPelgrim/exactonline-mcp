# exactonline-mcp Development Guidelines

Auto-generated from feature plans. Last updated: 2025-12-24

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
└── test_sanitization.py  # OData input sanitization tests
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

## Versioning & Releases

This project uses git tags for versioning (semver format: `vX.Y.Z`).

```bash
# Check current version
git describe --tags --always

# View all tags
git tag -l

# View changelog since last release
git log --oneline v0.1.0..HEAD
```

### Creating a new release

1. Update version in `pyproject.toml`
2. Commit all changes
3. Create annotated tag:
   ```bash
   git tag -a v0.2.0 -m "Release description"
   ```
4. Push commits and tag:
   ```bash
   git push origin main --tags
   ```

### Version history

- `v0.1.0` - Initial release with 13 MCP tools (discovery, revenue, financial)

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

- 003-open-receivables: Open receivables tools (get_open_receivables, get_customer_open_items, get_overdue_receivables)
- 002-revenue-tools: Revenue analysis tools (get_revenue_by_period, get_revenue_by_customer, get_revenue_by_project)
- 001-balance-sheet-financial: Financial reporting tools (get_profit_loss_overview, get_gl_account_balance, get_balance_sheet_summary, list_gl_account_balances, get_aging_receivables, get_aging_payables, get_gl_account_transactions)

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

## Financial Reporting API Notes

- P&L overview from `read/financial/ProfitLossOverview` - returns current vs previous year
- GL account balances from `financial/ReportingBalance` - filter by GLAccountID, year, period
- Account types: BalanceType "B" (balance sheet) vs "W" (profit/loss)
- Account type codes: 10=Kas, 12=Bank, 20=Debiteuren, 40=Crediteuren, 110=Omzet, 121=Bedrijfskosten
- Aging reports from `read/financial/AgingReceivablesList` and `AgingPayablesList`
- Transaction drill-down from `financialtransaction/TransactionLines` - filter by GLAccount GUID

## Costs by Period (No CostList Endpoint)

**Important**: Unlike `read/financial/RevenueList` and `RevenueListByYear`, there is NO dedicated `CostList` or `CostListByYear` endpoint in the Exact Online API. The `ProfitLossOverview` only provides costs for the current period and yearly totals.

**To get costs by period**, use `financial/ReportingBalance` with these filters:
```
Filter: ReportingYear eq {year} and ReportingPeriod eq {period} and BalanceType eq 'W' and Amount gt 0
Select: GLAccountCode,GLAccountDescription,Amount,ReportingPeriod
```

**Key points:**
- `BalanceType eq 'W'` = P/L accounts only (Winst/Verlies)
- `Amount gt 0` = Cost accounts (debit balances = positive)
- Revenue accounts have negative amounts (credit = negative in Dutch accounting)
- Cost account codes: 4xxx (operating expenses), 5xxx (personnel), 85xx (purchases/COGS)
- Revenue account codes: 8000-8009 (Omzet)

**Example - Q3 costs query:**
```
financial/ReportingBalance?$filter=ReportingYear eq 2024 and ReportingPeriod ge 7 and ReportingPeriod le 9 and BalanceType eq 'W' and Amount gt 0&$select=GLAccountCode,GLAccountDescription,Amount,ReportingPeriod
```

## Open Receivables API Notes

- Endpoint: `cashflow/Receivables` for individual invoice detail
- `AmountDC`: Negative = receivable (customer owes), Positive = credit (we owe)
- `TransactionAmountDC`: Original invoice amount
- OData dates in format `/Date(milliseconds)/` - use `parse_odata_date()` helper
- Filter `IsFullyPaid eq false` for open items only
- `days_overdue` calculated as (today - due_date).days
- Different from `AgingReceivablesList` which shows bucketed totals per customer
<!-- MANUAL ADDITIONS END -->
