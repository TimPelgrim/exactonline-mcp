# Quickstart: Bank & Purchase Data Tools

**Feature**: 004-bank-purchase-data

## Overview

Two new MCP tools for exposing bank transaction and purchase invoice data:

1. **`get_bank_transactions`** - Bank entry lines with transaction details
2. **`get_purchase_invoices`** - Purchase invoices from suppliers

## Example Prompts

```
"Show me bank transactions from last month"
"What payments did we make to Office Supplies B.V.?"
"Show transactions from our ING account (1055)"
"List all purchase invoices from December"
"What did we pay to supplier 700?"
```

## Quick Implementation Guide

### 1. Add Models (models.py)

```python
@dataclass
class BankTransaction:
    id: str
    date: str
    description: str
    amount: float
    account_code: str | None
    account_name: str | None
    gl_account_code: str
    gl_account_description: str
    entry_number: int
    document_subject: str
    notes: str | None
    our_ref: int | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "date": self.date,
            "description": self.description,
            "amount": self.amount,
            "account_code": self.account_code,
            "account_name": self.account_name,
            "gl_account_code": self.gl_account_code,
            "gl_account_description": self.gl_account_description,
            "entry_number": self.entry_number,
            "document_subject": self.document_subject,
            "notes": self.notes,
            "our_ref": self.our_ref,
        }


@dataclass
class PurchaseInvoice:
    id: str
    invoice_number: int
    invoice_date: str
    due_date: str | None
    supplier_code: str
    supplier_name: str
    amount: float
    currency: str
    status: int
    status_description: str
    description: str
    payment_condition: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "invoice_number": self.invoice_number,
            "invoice_date": self.invoice_date,
            "due_date": self.due_date,
            "supplier_code": self.supplier_code,
            "supplier_name": self.supplier_name,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
            "status_description": self.status_description,
            "description": self.description,
            "payment_condition": self.payment_condition,
        }
```

### 2. Add Client Methods (client.py)

```python
async def fetch_bank_transactions(
    self,
    division: int,
    top: int = 100,
    start_date: str | None = None,
    end_date: str | None = None,
    gl_account_code: str | None = None,
) -> list[dict]:
    """Fetch bank transaction lines from financialtransaction/BankEntryLines."""
    filters = []
    if start_date:
        filters.append(f"Date ge datetime'{start_date}'")
    if end_date:
        filters.append(f"Date le datetime'{end_date}'")
    if gl_account_code:
        filters.append(f"trim(GLAccountCode) eq '{gl_account_code}'")

    params = {
        "$select": "ID,Date,Description,AmountDC,AccountCode,AccountName,"
                   "GLAccountCode,GLAccountDescription,EntryNumber,"
                   "DocumentSubject,Notes,OurRef",
        "$top": str(min(top, 1000)),
        "$orderby": "Date desc",
    }
    if filters:
        params["$filter"] = " and ".join(filters)

    return await self.fetch(
        "financialtransaction/BankEntryLines",
        division=division,
        params=params,
    )


async def fetch_purchase_invoices(
    self,
    division: int,
    top: int = 100,
    start_date: str | None = None,
    end_date: str | None = None,
    supplier_code: str | None = None,
) -> list[dict]:
    """Fetch purchase invoices from purchase/PurchaseInvoices."""
    filters = []
    if start_date:
        filters.append(f"InvoiceDate ge datetime'{start_date}'")
    if end_date:
        filters.append(f"InvoiceDate le datetime'{end_date}'")
    if supplier_code:
        filters.append(f"trim(SupplierCode) eq '{supplier_code}'")

    params = {
        "$select": "ID,InvoiceNumber,InvoiceDate,DueDate,SupplierCode,"
                   "SupplierName,AmountDC,Currency,Status,StatusDescription,"
                   "Description,PaymentConditionDescription",
        "$top": str(min(top, 1000)),
        "$orderby": "InvoiceDate desc",
    }
    if filters:
        params["$filter"] = " and ".join(filters)

    return await self.fetch(
        "purchase/PurchaseInvoices",
        division=division,
        params=params,
    )
```

### 3. Add Tools (server.py)

```python
@mcp.tool()
async def get_bank_transactions(
    division: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    gl_account_code: str | None = None,
    top: int = 100,
) -> dict:
    """List bank transaction lines with optional filtering.

    Args:
        division: Division code (uses default if not specified)
        start_date: Filter from date (YYYY-MM-DD)
        end_date: Filter to date (YYYY-MM-DD)
        gl_account_code: Filter by bank GL account code (e.g., "1055")
        top: Maximum records to return (1-1000)
    """
    # Implementation...


@mcp.tool()
async def get_purchase_invoices(
    division: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    supplier_code: str | None = None,
    top: int = 100,
) -> dict:
    """List purchase invoices from suppliers.

    Args:
        division: Division code (uses default if not specified)
        start_date: Invoice date from (YYYY-MM-DD)
        end_date: Invoice date to (YYYY-MM-DD)
        supplier_code: Filter by supplier account code
        top: Maximum records to return (1-1000)

    Note: Requires Purchase module. Returns error if module unavailable.
    """
    # Implementation with graceful error handling for module unavailability...
```

### 4. Update README

Add to Available Tools table:
```markdown
| `get_bank_transactions` | List bank transaction lines with filtering |
| `get_purchase_invoices` | List purchase invoices from suppliers |
```

## Key Files to Modify

| File | Changes |
|------|---------|
| `src/exactonline_mcp/models.py` | Add `BankTransaction`, `PurchaseInvoice` dataclasses |
| `src/exactonline_mcp/client.py` | Add `fetch_bank_transactions()`, `fetch_purchase_invoices()` |
| `src/exactonline_mcp/server.py` | Add 2 new tool definitions |
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

### BankEntryLines

**Endpoint**: `financialtransaction/BankEntryLines`

**Key fields**:
- `AmountDC` < 0 = money leaving account (payment)
- `AmountDC` > 0 = money entering account (receipt)
- `GLAccountCode` = bank account code (e.g., "1055" for ING)
- `AccountCode` = related party (customer/supplier) if applicable

**Date format**: OData timestamp `/Date(1234567890000)/` -> parse to ISO

### PurchaseInvoices

**Endpoint**: `purchase/PurchaseInvoices`

**Key fields**:
- `Status` 10=Draft, 20=Open, 50=Processed/Paid
- `AmountDC` = invoice amount in default currency

**Note**: This endpoint may require the Purchase module subscription. Handle `DivisionNotAccessible` error gracefully with a clear message.
