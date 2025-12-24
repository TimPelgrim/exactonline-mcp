# MCP Tool Contracts: Bank & Purchase Data

**Feature**: 004-bank-purchase-data
**Date**: 2025-12-24

## Tool: get_bank_transactions

List bank transaction lines from bank entry journals.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| division | int | No | Current | Division code |
| start_date | str | No | None | Start date (YYYY-MM-DD) |
| end_date | str | No | None | End date (YYYY-MM-DD) |
| gl_account_code | str | No | None | Filter by bank GL account code (e.g., "1055") |
| top | int | No | 100 | Max records (1-1000) |

### Response

```json
{
  "division": 1913290,
  "count": 50,
  "filters_applied": {
    "start_date": "2025-01-01",
    "end_date": "2025-12-31",
    "gl_account_code": "1055"
  },
  "items": [
    {
      "id": "abc123-...",
      "date": "2025-12-15",
      "description": "Betaling factuur 5124",
      "amount": -605.00,
      "account_code": "400",
      "account_name": "FTB Mobile B.V.",
      "gl_account_code": "1055",
      "gl_account_description": "ING Bank",
      "entry_number": 20251215,
      "document_subject": "Bank ING december",
      "notes": null,
      "our_ref": 5124
    }
  ]
}
```

### Field Descriptions

| Field | Description |
|-------|-------------|
| amount | Transaction amount (negative = outflow/payment, positive = inflow/receipt) |
| account_code | Related party code (customer/supplier), null if internal transfer |
| account_name | Related party name |
| gl_account_code | Bank account GL code |
| gl_account_description | Bank account name |
| entry_number | Journal entry number |
| our_ref | Internal reference (often invoice number) |

### Errors

| Code | Condition | Message |
|------|-----------|---------|
| AUTH_ERROR | Token expired | "Authentication failed. Please re-authenticate." |
| RATE_LIMIT | 60/min exceeded | "Rate limit exceeded. Retry in {seconds} seconds." |
| INVALID_DIVISION | Division not found | "Division {code} not accessible." |
| INVALID_PARAM | top > 1000 | "Parameter 'top' must be between 1 and 1000." |
| INVALID_DATE | Bad date format | "Invalid date format. Use YYYY-MM-DD." |
| INVALID_ACCOUNT | GL account not found | "GL account code '{code}' not found." |

---

## Tool: get_purchase_invoices

List purchase invoices from suppliers.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| division | int | No | Current | Division code |
| start_date | str | No | None | Invoice date start (YYYY-MM-DD) |
| end_date | str | No | None | Invoice date end (YYYY-MM-DD) |
| supplier_code | str | No | None | Filter by supplier account code |
| top | int | No | 100 | Max records (1-1000) |

### Response

```json
{
  "division": 1913290,
  "count": 25,
  "filters_applied": {
    "start_date": "2025-01-01",
    "end_date": "2025-12-31",
    "supplier_code": null
  },
  "items": [
    {
      "id": "xyz789-...",
      "invoice_number": 12345,
      "invoice_date": "2025-12-01",
      "due_date": "2025-12-31",
      "supplier_code": "700",
      "supplier_name": "Office Supplies B.V.",
      "amount": 1250.00,
      "currency": "EUR",
      "status": 20,
      "status_description": "Open",
      "description": "Kantoorbenodigdheden december",
      "payment_condition": "30 dagen netto"
    }
  ]
}
```

### Status Codes

| Status | Description |
|--------|-------------|
| 10 | Draft |
| 20 | Open |
| 50 | Processed/Paid |

### Errors

| Code | Condition | Message |
|------|-----------|---------|
| AUTH_ERROR | Token expired | "Authentication failed. Please re-authenticate." |
| RATE_LIMIT | 60/min exceeded | "Rate limit exceeded. Retry in {seconds} seconds." |
| INVALID_DIVISION | Division not found | "Division {code} not accessible." |
| MODULE_NOT_AVAILABLE | Purchase module missing | "Purchase module not enabled for this division. Contact your Exact Online administrator." |
| INVALID_PARAM | top > 1000 | "Parameter 'top' must be between 1 and 1000." |
| INVALID_DATE | Bad date format | "Invalid date format. Use YYYY-MM-DD." |
| INVALID_SUPPLIER | Supplier not found | "Supplier code '{code}' not found." |

### Notes

- The Purchase module may not be enabled for all Exact Online subscriptions
- When the module is unavailable, a clear error message is returned with guidance
- Status 50 (Processed/Paid) indicates the invoice has been fully processed
