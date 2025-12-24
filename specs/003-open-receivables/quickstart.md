# Quickstart: Open Receivables Tools

**Feature**: 003-open-receivables

## Overview

Three new MCP tools for viewing detailed open receivables from Exact Online:

1. **`get_open_receivables`** - List all open invoices/credits
2. **`get_customer_open_items`** - Open items for a specific customer
3. **`get_overdue_receivables`** - Overdue items sorted by age

## Example Prompts

```
"Show me all open receivables"
"What invoices are outstanding for FTB Mobile?"
"Which invoices are overdue?"
"Show receivables more than 30 days overdue"
"What's the total amount we're waiting to receive?"
```

## Quick Implementation Guide

### 1. Add Model (models.py)

```python
@dataclass
class OpenReceivable:
    account_code: str
    account_name: str
    invoice_number: int
    invoice_date: str
    due_date: str
    original_amount: float
    remaining_amount: float
    is_credit: bool
    description: str
    payment_terms: str
    days_overdue: int
    currency: str
```

### 2. Add Client Method (client.py)

```python
async def fetch_open_receivables(
    self,
    division: int,
    top: int = 100,
    account_code: str | None = None,
    overdue_only: bool = False,
) -> list[dict]:
    """Fetch open receivables from cashflow/Receivables."""
    filters = ["IsFullyPaid eq false"]
    if account_code:
        filters.append(f"AccountCode eq '{sanitize_odata_string(account_code)}'")
    if overdue_only:
        today = datetime.now().strftime("%Y-%m-%d")
        filters.append(f"DueDate lt datetime'{today}'")

    return await self.fetch(
        f"cashflow/Receivables",
        division=division,
        params={
            "$filter": " and ".join(filters),
            "$select": "AccountCode,AccountName,InvoiceNumber,...",
            "$top": str(min(top, 1000)),
        },
    )
```

### 3. Add Tool (server.py)

```python
@mcp.tool()
async def get_open_receivables(
    division: int | None = None,
    top: int = 100,
    account_code: str | None = None,
    overdue_only: bool = False,
) -> dict:
    """List open (unpaid) receivables with optional filtering."""
    # Implementation...
```

### 4. Update README

Add to Available Tools table:
```markdown
| `get_open_receivables` | List open invoices with filtering |
| `get_customer_open_items` | Open items for specific customer |
| `get_overdue_receivables` | Overdue receivables sorted by age |
```

## Key Files to Modify

| File | Changes |
|------|---------|
| `src/exactonline_mcp/models.py` | Add `OpenReceivable` dataclass |
| `src/exactonline_mcp/client.py` | Add `fetch_open_receivables()` method |
| `src/exactonline_mcp/server.py` | Add 3 new tool definitions |
| `README.md` | Document new tools |
| `CLAUDE.md` | Update Recent Changes |

## Testing

```bash
# Run all tests
uv run pytest

# Test with real data (manual)
uv run python -m exactonline_mcp
# Then use MCP inspector or Claude to call tools
```

## API Details

**Endpoint**: `cashflow/Receivables`

**Key fields**:
- `AmountDC` < 0 = receivable (we get money)
- `AmountDC` > 0 = credit (we owe money)
- `IsFullyPaid` = false for open items

**Date format**: OData timestamp `/Date(1234567890000)/` -> parse to ISO
