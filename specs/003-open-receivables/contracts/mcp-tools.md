# MCP Tool Contracts: Open Receivables

**Feature**: 003-open-receivables
**Date**: 2025-12-23

## Tool: get_open_receivables

List open (unpaid) receivables with optional filtering.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| division | int | No | Current | Division code |
| top | int | No | 100 | Max records (1-1000) |
| account_code | str | No | None | Filter by customer code |
| overdue_only | bool | No | false | Only show overdue items |

### Response

```json
{
  "division": 1913290,
  "total_receivables": 150000.00,
  "total_credits": 5000.00,
  "net_receivables": 145000.00,
  "invoice_count": 25,
  "credit_count": 2,
  "overdue_amount": 35000.00,
  "overdue_count": 8,
  "currency": "EUR",
  "items": [
    {
      "account_code": "400",
      "account_name": "FTB Mobile B.V.",
      "invoice_number": 5124,
      "invoice_date": "2025-09-01",
      "due_date": "2025-09-15",
      "original_amount": 605.00,
      "remaining_amount": 605.00,
      "is_credit": false,
      "description": "FTB Mobile september Hosting",
      "payment_terms": "14 dagen",
      "days_overdue": 99,
      "currency": "EUR"
    }
  ]
}
```

### Errors

| Code | Condition | Message |
|------|-----------|---------|
| AUTH_ERROR | Token expired | "Authentication failed. Please re-authenticate." |
| RATE_LIMIT | 60/min exceeded | "Rate limit exceeded. Retry in {seconds} seconds." |
| INVALID_DIVISION | Division not found | "Division {code} not accessible." |
| INVALID_PARAM | top > 1000 | "Parameter 'top' must be between 1 and 1000." |

---

## Tool: get_customer_open_items

Get all open items for a specific customer.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| division | int | No | Current | Division code |
| account_code | str | **Yes** | - | Customer account code |

### Response

```json
{
  "division": 1913290,
  "customer": {
    "account_code": "400",
    "account_name": "FTB Mobile B.V."
  },
  "total_receivables": 12000.00,
  "total_credits": 0.00,
  "net_receivables": 12000.00,
  "invoice_count": 5,
  "overdue_amount": 8000.00,
  "overdue_count": 3,
  "currency": "EUR",
  "items": [
    {
      "invoice_number": 5124,
      "invoice_date": "2025-09-01",
      "due_date": "2025-09-15",
      "original_amount": 605.00,
      "remaining_amount": 605.00,
      "is_credit": false,
      "description": "september Hosting",
      "payment_terms": "14 dagen",
      "days_overdue": 99,
      "currency": "EUR"
    }
  ]
}
```

### Errors

| Code | Condition | Message |
|------|-----------|---------|
| MISSING_PARAM | account_code not provided | "Parameter 'account_code' is required." |
| NOT_FOUND | No open items | "No open items found for customer {code}." |

---

## Tool: get_overdue_receivables

List receivables past their due date, sorted by days overdue.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| division | int | No | Current | Division code |
| days_overdue | int | No | 0 | Minimum days overdue |
| top | int | No | 100 | Max records (1-1000) |

### Response

```json
{
  "division": 1913290,
  "as_of_date": "2025-12-23",
  "min_days_overdue": 0,
  "total_overdue": 35000.00,
  "invoice_count": 8,
  "currency": "EUR",
  "items": [
    {
      "account_code": "400",
      "account_name": "FTB Mobile B.V.",
      "invoice_number": 4982,
      "invoice_date": "2025-03-01",
      "due_date": "2025-03-15",
      "original_amount": 605.00,
      "remaining_amount": 605.00,
      "is_credit": false,
      "description": "maart",
      "payment_terms": "14 dagen",
      "days_overdue": 283,
      "currency": "EUR"
    }
  ]
}
```

### Notes

- Items sorted by `days_overdue` descending (most overdue first)
- Credit notes are excluded from overdue report
- `as_of_date` shows calculation reference date
