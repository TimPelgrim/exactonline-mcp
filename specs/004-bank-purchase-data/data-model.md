# Data Model: Bank & Purchase Data Tools

**Feature**: 004-bank-purchase-data
**Date**: 2025-12-24

## Entities

### BankTransaction

Represents a single bank entry line (transaction) from Exact Online.

```python
@dataclass
class BankTransaction:
    """Single bank transaction line from a bank entry.

    Args:
        id: Exact Online transaction line GUID.
        date: Transaction date (ISO format YYYY-MM-DD).
        description: Transaction description/memo.
        amount: Amount in default currency (negative = outflow, positive = inflow).
        account_code: Related party code (customer/supplier), if any.
        account_name: Related party name, if any.
        gl_account_code: GL account code (bank account, e.g., "1055").
        gl_account_description: GL account name (e.g., "ING Bank").
        entry_number: Journal entry number.
        document_subject: Source document description.
        notes: Additional notes/memo.
        our_ref: Internal reference number.
    """
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
        """Convert to dictionary for JSON serialization."""
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
```

### PurchaseInvoice

Represents a purchase invoice from a supplier.

```python
@dataclass
class PurchaseInvoice:
    """Purchase invoice from a supplier.

    Args:
        id: Exact Online invoice GUID.
        invoice_number: Invoice number.
        invoice_date: Invoice date (ISO format YYYY-MM-DD).
        due_date: Payment due date (ISO format YYYY-MM-DD).
        supplier_code: Supplier account code.
        supplier_name: Supplier name.
        amount: Invoice amount in default currency.
        currency: Currency code (e.g., "EUR").
        status: Invoice status (draft, open, paid, etc.).
        description: Invoice description/memo.
        payment_condition: Payment terms description.
    """
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
        """Convert to dictionary for JSON serialization."""
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

## Field Mapping

### BankEntryLines API to BankTransaction

| API Field | Model Field | Transformation |
|-----------|-------------|----------------|
| `ID` | `id` | Direct |
| `Date` | `date` | Parse OData date to ISO |
| `Description` | `description` | Direct |
| `AmountDC` | `amount` | Direct (preserve sign) |
| `AccountCode` | `account_code` | Strip whitespace, None if empty |
| `AccountName` | `account_name` | Direct, None if empty |
| `GLAccountCode` | `gl_account_code` | Strip whitespace |
| `GLAccountDescription` | `gl_account_description` | Direct |
| `EntryNumber` | `entry_number` | Direct (int) |
| `DocumentSubject` | `document_subject` | Direct |
| `Notes` | `notes` | Direct, None if empty |
| `OurRef` | `our_ref` | Direct (int), None if empty |

### PurchaseInvoices API to PurchaseInvoice

| API Field | Model Field | Transformation |
|-----------|-------------|----------------|
| `ID` | `id` | Direct |
| `InvoiceNumber` | `invoice_number` | Direct (int) |
| `InvoiceDate` | `invoice_date` | Parse OData date to ISO |
| `DueDate` | `due_date` | Parse OData date to ISO, None if empty |
| `SupplierCode` | `supplier_code` | Strip whitespace |
| `SupplierName` | `supplier_name` | Direct |
| `AmountDC` | `amount` | Direct |
| `Currency` | `currency` | Direct |
| `Status` | `status` | Direct (int) |
| `StatusDescription` | `status_description` | Direct |
| `Description` | `description` | Direct |
| `PaymentConditionDescription` | `payment_condition` | Direct, None if empty |

## Sign Convention

### Bank Transactions
- **Negative AmountDC**: Money leaving the account (payments, withdrawals)
- **Positive AmountDC**: Money entering the account (receipts, deposits)

This matches standard accounting convention and is preserved as-is (no transformation).

## Validation Rules

1. `id` must be a valid GUID string
2. `date` must be valid ISO format (YYYY-MM-DD)
3. `amount` can be positive or negative (preserved from API)
4. `gl_account_code` must not be empty for bank transactions
5. `invoice_number` must be positive integer

## Notes

- No summary/aggregation dataclasses - per spec, this feature is "data exposure only"
- Claude handles any calculations or insights downstream
- All optional fields (account_code, notes, etc.) can be None
