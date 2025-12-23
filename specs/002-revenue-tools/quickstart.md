# Quickstart: Revenue Tools

**Feature**: 002-revenue-tools
**Date**: 2025-12-22

## Overview

The Revenue Tools feature adds three MCP tools for analyzing revenue data from Exact Online:

1. **get_revenue_by_period** - Revenue over time with year-over-year comparison
2. **get_revenue_by_customer** - Top customers by revenue
3. **get_revenue_by_project** - Project-based revenue with hours

## Prerequisites

- Authenticated with Exact Online (run `uv run exactonline-mcp auth` if needed)
- Division with processed sales invoices
- For project revenue: Division with project module enabled

## Tool Usage

### get_revenue_by_period

Get revenue totals grouped by month, quarter, or year with comparison to the same period last year.

**Required Parameters**:
- `start_date` - Start date (YYYY-MM-DD)
- `end_date` - End date (YYYY-MM-DD)

**Optional Parameters**:
- `group_by` - "month" (default), "quarter", or "year"
- `division` - Division code (defaults to current division)

**Example Prompts**:
```
"Show me revenue by quarter for 2024"
"What was our monthly revenue from January to June?"
"Compare yearly revenue for 2023 and 2024"
```

**Example Response**:
```json
{
  "division": 7095,
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "group_by": "quarter",
  "total_revenue": 150000.00,
  "total_invoices": 245,
  "periods": [
    {
      "period_key": "2024-Q1",
      "start_date": "2024-01-01",
      "end_date": "2024-03-31",
      "revenue": 35000.00,
      "invoice_count": 58,
      "previous_revenue": 32000.00,
      "change_percentage": 9.38
    },
    {
      "period_key": "2024-Q2",
      "start_date": "2024-04-01",
      "end_date": "2024-06-30",
      "revenue": 42000.00,
      "invoice_count": 65,
      "previous_revenue": 38000.00,
      "change_percentage": 10.53
    }
  ]
}
```

### get_revenue_by_customer

Get top customers ranked by revenue with invoice count and percentage of total.

**Optional Parameters**:
- `division` - Division code (defaults to current division)
- `start_date` - Start date for filtering (YYYY-MM-DD)
- `end_date` - End date for filtering (YYYY-MM-DD)
- `top` - Number of customers to return (default 10, max 100)

**Example Prompts**:
```
"Who are our top 5 customers this year?"
"Show customer revenue breakdown for Q4 2024"
"Which customers generated the most revenue?"
```

**Example Response**:
```json
{
  "division": 7095,
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "total_revenue": 150000.00,
  "total_invoices": 245,
  "customer_count": 42,
  "customers": [
    {
      "customer_id": "abc123-...",
      "customer_name": "Acme Corporation",
      "revenue": 45000.00,
      "invoice_count": 24,
      "percentage_of_total": 30.00
    },
    {
      "customer_id": "def456-...",
      "customer_name": "TechStart BV",
      "revenue": 28000.00,
      "invoice_count": 18,
      "percentage_of_total": 18.67
    }
  ]
}
```

### get_revenue_by_project

Get project-based revenue with client information and optional hours tracking.

**Optional Parameters**:
- `division` - Division code (defaults to current division)
- `start_date` - Start date for filtering (YYYY-MM-DD)
- `end_date` - End date for filtering (YYYY-MM-DD)
- `include_hours` - Whether to fetch hours from TimeTransactions (default true)

**Example Prompts**:
```
"Show revenue by project for 2024"
"What are our most profitable projects?"
"List project revenue with logged hours"
```

**Example Response**:
```json
{
  "division": 7095,
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "total_revenue": 85000.00,
  "total_invoices": 156,
  "project_count": 12,
  "hours_available": true,
  "projects": [
    {
      "project_id": "proj123-...",
      "project_code": "P2024-001",
      "project_name": "Website Redesign",
      "client_id": "abc123-...",
      "client_name": "Acme Corporation",
      "revenue": 25000.00,
      "invoice_count": 8,
      "hours": 320.5
    },
    {
      "project_id": "proj456-...",
      "project_code": "P2024-002",
      "project_name": "Mobile App Development",
      "client_id": "def456-...",
      "client_name": "TechStart BV",
      "revenue": 18000.00,
      "invoice_count": 6,
      "hours": 245.0
    }
  ]
}
```

## Common Use Cases

### Quarterly Business Review
```
"Show me quarterly revenue for 2024 with year-over-year comparison"
"Who were our top 10 customers in Q4?"
"Which projects had the highest revenue in Q4?"
```

### Customer Analysis
```
"Which customers have grown the most compared to last year?"
"Show all customers with revenue over €10,000 in 2024"
```

### Project Profitability
```
"What's the revenue per hour for each project?"
"Which projects have the best revenue-to-hours ratio?"
```

## Edge Cases

### Empty Results
If no processed invoices exist for the date range, tools return:
- `total_revenue: 0`
- `total_invoices: 0`
- Empty `periods`, `customers`, or `projects` array

### Credit Notes
Credit notes are included automatically as negative amounts, reducing totals.

### No Project Module
If the division doesn't have the project module enabled:
```json
{
  "error": "project_module_unavailable",
  "message": "Project module is not enabled for this division",
  "action": "This tool requires the project module in Exact Online"
}
```

## Performance Notes

- **get_revenue_by_period**: Fast - queries invoice headers only
- **get_revenue_by_customer**: Fast - aggregates invoice headers
- **get_revenue_by_project**: Slower - queries invoice lines + projects + optionally TimeTransactions
  - Set `include_hours: false` for faster response if hours not needed
  - Large date ranges with many projects may take several seconds

## Next Steps

After reviewing revenue data, you can:
- Use `explore_endpoint` to dive into specific invoices
- Use `list_divisions` to check other divisions
- Request invoice-level detail for specific customers or projects
