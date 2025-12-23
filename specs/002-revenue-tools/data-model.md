# Data Model: Revenue Tools

**Feature**: 002-revenue-tools
**Date**: 2025-12-22
**Status**: Complete

## Overview

This document defines the data models for the three revenue analysis tools. These models extend the existing `models.py` in the exactonline-mcp project.

## Entity Definitions

### RevenuePeriod

Represents revenue totals for a specific time period with year-over-year comparison.

```python
@dataclass
class RevenuePeriod:
    """Revenue totals for a time period with comparison.

    Args:
        period_key: Period identifier (e.g., "2024-Q1", "2024-01", "2024")
        start_date: First day of the period (ISO format)
        end_date: Last day of the period (ISO format)
        revenue: Total revenue in default currency
        invoice_count: Number of invoices in period
        previous_revenue: Revenue for same period last year (None if N/A)
        change_percentage: Year-over-year change (None if previous_revenue is None/zero)
    """
    period_key: str
    start_date: str
    end_date: str
    revenue: float
    invoice_count: int
    previous_revenue: float | None = None
    change_percentage: float | None = None
```

**Field Details**:
| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `period_key` | str | Computed | Format depends on group_by: "2024-01" (month), "2024-Q1" (quarter), "2024" (year) |
| `start_date` | str | Computed | ISO date (YYYY-MM-DD) |
| `end_date` | str | Computed | ISO date (YYYY-MM-DD) |
| `revenue` | float | SalesInvoices.AmountDC | Sum of all processed invoices in period |
| `invoice_count` | int | Computed | Count of processed invoices |
| `previous_revenue` | float? | SalesInvoices.AmountDC | Same period, previous year |
| `change_percentage` | float? | Computed | `((revenue - previous) / previous) * 100` |

### CustomerRevenue

Represents aggregated revenue for a single customer.

```python
@dataclass
class CustomerRevenue:
    """Revenue metrics for a single customer.

    Args:
        customer_id: Exact Online account GUID
        customer_name: Account name
        revenue: Total revenue in default currency
        invoice_count: Number of invoices
        percentage_of_total: Share of total revenue (0-100)
    """
    customer_id: str
    customer_name: str
    revenue: float
    invoice_count: int
    percentage_of_total: float
```

**Field Details**:
| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `customer_id` | str | SalesInvoices.InvoiceTo | GUID as string |
| `customer_name` | str | SalesInvoices.InvoiceToName | Denormalized from invoice |
| `revenue` | float | SalesInvoices.AmountDC | Sum per customer |
| `invoice_count` | int | Computed | Count per customer |
| `percentage_of_total` | float | Computed | `(customer_revenue / total_revenue) * 100` |

### ProjectRevenue

Represents aggregated revenue for a single project with optional hours.

```python
@dataclass
class ProjectRevenue:
    """Revenue metrics for a single project.

    Args:
        project_id: Exact Online project GUID
        project_code: Project code
        project_name: Project description
        client_id: Client account GUID (optional)
        client_name: Client account name (optional)
        revenue: Total revenue in default currency
        invoice_count: Number of invoice lines
        hours: Total hours logged (optional, from TimeTransactions)
    """
    project_id: str
    project_code: str
    project_name: str
    client_id: str | None
    client_name: str | None
    revenue: float
    invoice_count: int
    hours: float | None = None
```

**Field Details**:
| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `project_id` | str | SalesInvoiceLines.Project | GUID as string |
| `project_code` | str | Projects.Code | From project lookup |
| `project_name` | str | Projects.Description | From project lookup |
| `client_id` | str? | Projects.Account | GUID as string |
| `client_name` | str? | Projects.AccountName | Denormalized |
| `revenue` | float | SalesInvoiceLines.AmountDC | Sum per project |
| `invoice_count` | int | Computed | Count of invoice lines |
| `hours` | float? | TimeTransactions.Quantity | Sum of hours (optional) |

## Response Structures

### RevenueByPeriodResponse

```python
@dataclass
class RevenueByPeriodResponse:
    """Response for get_revenue_by_period tool."""
    division: int
    start_date: str
    end_date: str
    group_by: str  # month | quarter | year
    total_revenue: float
    total_invoices: int
    periods: list[RevenuePeriod]
```

### RevenueByCustomerResponse

```python
@dataclass
class RevenueByCustomerResponse:
    """Response for get_revenue_by_customer tool."""
    division: int
    start_date: str | None
    end_date: str | None
    total_revenue: float
    total_invoices: int
    customer_count: int
    customers: list[CustomerRevenue]
```

### RevenueByProjectResponse

```python
@dataclass
class RevenueByProjectResponse:
    """Response for get_revenue_by_project tool."""
    division: int
    start_date: str | None
    end_date: str | None
    total_revenue: float
    total_invoices: int
    project_count: int
    projects: list[ProjectRevenue]
    hours_available: bool  # Whether hours data was fetched
```

## API Field Mappings

### From SalesInvoices

| Our Field | API Field | Notes |
|-----------|-----------|-------|
| revenue | AmountDC | Default currency, includes all lines |
| invoice_date | InvoiceDate | For period grouping |
| customer_id | InvoiceTo | GUID reference |
| customer_name | InvoiceToName | Already denormalized |
| status | Status | Filter: `eq 50` for processed |

### From SalesInvoiceLines

| Our Field | API Field | Notes |
|-----------|-----------|-------|
| revenue | AmountDC | Excludes VAT, per line |
| project_id | Project | GUID reference, can be null |
| invoice_id | InvoiceID | For joining to header |

### From Projects

| Our Field | API Field | Notes |
|-----------|-----------|-------|
| project_id | ID | Primary key |
| project_code | Code | Display identifier |
| project_name | Description | Human-readable name |
| client_id | Account | GUID reference |
| client_name | AccountName | Already denormalized |

### From TimeTransactions

| Our Field | API Field | Notes |
|-----------|-----------|-------|
| hours | Quantity | When Item is time-based |
| project_id | Project | For aggregation |
| date | Date | For date filtering |

## Serialization

All dataclasses will include a `to_dict()` method following the existing pattern in `models.py`:

```python
def to_dict(self) -> dict[str, Any]:
    """Convert to dictionary for JSON serialization."""
    return {
        "period_key": self.period_key,
        "start_date": self.start_date,
        "end_date": self.end_date,
        "revenue": self.revenue,
        "invoice_count": self.invoice_count,
        "previous_revenue": self.previous_revenue,
        "change_percentage": self.change_percentage,
    }
```

## Constraints and Validation

### Revenue Calculations
- Only include invoices with `Status eq 50` (processed)
- Credit notes have negative AmountDC - include in sums
- Use `AmountDC` (default currency) for consistency

### Date Handling
- All dates in ISO format (YYYY-MM-DD)
- Period boundaries are inclusive
- Year-over-year compares same calendar period

### Percentage Calculations
- `change_percentage`: None if previous_revenue is None or zero (avoid division by zero)
- `percentage_of_total`: 0-100 scale, 2 decimal precision
- Round percentages to 2 decimal places
