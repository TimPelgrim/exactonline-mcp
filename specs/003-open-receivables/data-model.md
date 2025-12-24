# Data Model: Open Receivables Tool

**Feature**: 003-open-receivables
**Date**: 2025-12-23

## Entities

### OpenReceivable

Represents a single open invoice or credit note from a customer.

```python
@dataclass
class OpenReceivable:
    """Single open receivable (invoice/credit) from a customer.

    Args:
        account_code: Customer account code (e.g., "400").
        account_name: Customer display name.
        invoice_number: Invoice number.
        invoice_date: Invoice date (ISO format YYYY-MM-DD).
        due_date: Payment due date (ISO format YYYY-MM-DD).
        original_amount: Original invoice amount (always positive).
        remaining_amount: Amount still outstanding (always positive).
        is_credit: True if this is a credit note/overpayment.
        description: Invoice description/memo.
        payment_terms: Payment condition description.
        days_overdue: Days past due date (negative if not yet due).
        currency: Currency code (typically EUR).
    """
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

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "account_code": self.account_code,
            "account_name": self.account_name,
            "invoice_number": self.invoice_number,
            "invoice_date": self.invoice_date,
            "due_date": self.due_date,
            "original_amount": self.original_amount,
            "remaining_amount": self.remaining_amount,
            "is_credit": self.is_credit,
            "description": self.description,
            "payment_terms": self.payment_terms,
            "days_overdue": self.days_overdue,
            "currency": self.currency,
        }
```

### OpenReceivablesSummary

Summary statistics for a collection of receivables.

```python
@dataclass
class OpenReceivablesSummary:
    """Summary of open receivables query results.

    Args:
        division: Exact Online division code.
        total_receivables: Total amount outstanding (excluding credits).
        total_credits: Total credit amounts.
        net_receivables: Net amount (receivables - credits).
        invoice_count: Number of open invoices.
        credit_count: Number of credit notes.
        overdue_amount: Total amount that is past due.
        overdue_count: Number of overdue items.
        currency: Currency code.
        items: List of individual receivables.
    """
    division: int
    total_receivables: float
    total_credits: float
    net_receivables: float
    invoice_count: int
    credit_count: int
    overdue_amount: float
    overdue_count: int
    currency: str
    items: list[OpenReceivable] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "division": self.division,
            "total_receivables": self.total_receivables,
            "total_credits": self.total_credits,
            "net_receivables": self.net_receivables,
            "invoice_count": self.invoice_count,
            "credit_count": self.credit_count,
            "overdue_amount": self.overdue_amount,
            "overdue_count": self.overdue_count,
            "currency": self.currency,
            "items": [item.to_dict() for item in self.items],
        }
```

## Field Mapping

### API to Model Mapping

| API Field | Model Field | Transformation |
|-----------|-------------|----------------|
| `AccountCode` | `account_code` | Strip whitespace |
| `AccountName` | `account_name` | Direct |
| `InvoiceNumber` | `invoice_number` | Direct (int) |
| `InvoiceDate` | `invoice_date` | Parse OData date to ISO |
| `DueDate` | `due_date` | Parse OData date to ISO |
| `TransactionAmountDC` | `original_amount` | `abs(value)` |
| `AmountDC` | `remaining_amount` | `abs(value)` |
| `AmountDC` | `is_credit` | `value > 0` |
| `Description` | `description` | Direct |
| `PaymentConditionDescription` | `payment_terms` | Direct |
| `Currency` | `currency` | Direct |
| (calculated) | `days_overdue` | `(today - due_date).days` |

### Sign Convention Translation

**API Values**:
- `AmountDC < 0`: Customer owes money (receivable)
- `AmountDC > 0`: We owe customer (credit/overpayment)
- `TransactionAmountDC > 0`: Invoice
- `TransactionAmountDC < 0`: Credit note

**Model Values**:
- `remaining_amount`: Always positive
- `original_amount`: Always positive
- `is_credit`: Boolean flag for direction

## Validation Rules

1. `invoice_number` must be positive integer
2. `original_amount` must be >= `remaining_amount`
3. `days_overdue` is negative for items not yet due
4. `currency` must be 3-letter ISO code

## State Transitions

Not applicable - receivables are read-only views of invoice state.
