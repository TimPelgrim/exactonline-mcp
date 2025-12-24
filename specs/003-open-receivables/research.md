# Research: Open Receivables Tool

**Feature**: 003-open-receivables
**Date**: 2025-12-23

## Endpoint Discovery

### cashflow/Receivables

**Endpoint**: `GET /api/v1/{division}/cashflow/Receivables`

**Status**: Confirmed working

**Sample Query**:
```
cashflow/Receivables?$filter=IsFullyPaid eq false&$select=AccountCode,AccountName,InvoiceNumber,InvoiceDate,DueDate,TransactionAmountDC,AmountDC,IsFullyPaid,PaymentConditionDescription,Description&$top=10
```

### Available Fields

Full field list from API exploration:

| Field | Type | Description |
|-------|------|-------------|
| ID | GUID | Unique receivable ID |
| Account | GUID | Customer account GUID |
| AccountCode | string | Customer code (padded) |
| AccountName | string | Customer display name |
| InvoiceNumber | int | Invoice number |
| InvoiceDate | Date | Invoice creation date |
| DueDate | Date | Payment due date |
| TransactionAmountDC | decimal | Original amount (DC = default currency) |
| AmountDC | decimal | Remaining open amount |
| IsFullyPaid | bool | Payment completion flag |
| PaymentConditionDescription | string | Payment terms description |
| Description | string | Invoice line description |
| Currency | string | Currency code (EUR) |
| PaymentReference | string | Payment reference |
| LastPaymentDate | Date | Date of last payment (if partial) |
| TransactionDueDate | Date | Original transaction due date |

### Field Value Interpretation

**AmountDC Sign Convention**:
- Negative value = Amount to receive (normal receivable)
- Positive value = Credit balance (credit note or overpayment)

**TransactionAmountDC Sign Convention**:
- Positive value = Invoice (debit to customer)
- Negative value = Credit note (credit to customer)

### Date Format

Dates returned as OData timestamps: `/Date(1756684800000)/`
- Value is milliseconds since Unix epoch
- Need to parse and format for display

### Filtering Options

| Filter | OData Expression | Use Case |
|--------|------------------|----------|
| Open items only | `IsFullyPaid eq false` | Default for open receivables |
| Specific customer | `AccountCode eq '400'` | Customer detail view |
| Overdue items | `DueDate lt datetime'2025-12-23'` | Overdue report |
| By invoice | `InvoiceNumber eq 5124` | Specific invoice lookup |

### Pagination

- Endpoint requires `$select` or `$top=1` (API limitation)
- Max records per call: 1000 (via `$top`)
- Pagination via `$skip` for larger datasets

### Comparison with AgingReceivablesList

| Aspect | AgingReceivablesList | cashflow/Receivables |
|--------|---------------------|---------------------|
| Granularity | Per customer | Per invoice |
| Aging buckets | 0-30, 31-60, 61-90, >90 | No buckets (raw dates) |
| Invoice details | No | Yes (number, date, description) |
| Due date | No | Yes |
| Payment terms | No | Yes |
| Use case | Quick overview | Detailed follow-up |

## Design Decisions

### Decision 1: Tool Scope

**Decision**: Create 3 focused tools instead of 1 complex tool

**Rationale**:
- Follows constitution principle: "One tool per function; tools are composable"
- Simpler parameter handling
- Claude can combine tools as needed

**Alternatives Rejected**:
- Single tool with mode parameter: More complex, harder to use

### Decision 2: Date Handling

**Decision**: Return dates as ISO format strings (YYYY-MM-DD)

**Rationale**:
- Consistent with existing revenue tools
- Human-readable
- Easy for Claude to interpret and format

**Alternatives Rejected**:
- Raw timestamps: Not human-readable
- Localized format: Inconsistent across locales

### Decision 3: Amount Sign Convention

**Decision**: Return amounts as positive values with explicit direction field

**Rationale**:
- Clearer for users
- Consistent interpretation
- `remaining_amount` always positive, `is_credit` flag for credits

**Alternatives Rejected**:
- Raw API values: Confusing sign convention

### Decision 4: Default Pagination

**Decision**: Default `top=100`, max `top=1000`

**Rationale**:
- Reasonable default for typical use
- Prevents accidental large fetches
- Consistent with existing tools

## Implementation Notes

### Existing Patterns to Follow

From `src/exactonline_mcp/client.py`:
- Use `ExactOnlineClient.fetch()` for API calls
- OData filter building patterns
- Error handling for auth/rate limits

From `src/exactonline_mcp/server.py`:
- Tool registration pattern
- Parameter validation
- Response formatting

### New Model Required

`OpenReceivable` dataclass in `models.py`:
```python
@dataclass
class OpenReceivable:
    account_code: str
    account_name: str
    invoice_number: int
    invoice_date: str  # ISO format
    due_date: str  # ISO format
    original_amount: float
    remaining_amount: float
    is_credit: bool
    description: str
    payment_terms: str
    days_overdue: int  # Calculated
    currency: str
```

### Helper Function

Date parsing utility:
```python
def parse_odata_date(date_str: str) -> str:
    """Convert OData date to ISO format."""
    # /Date(1756684800000)/ -> 2025-09-01
```
