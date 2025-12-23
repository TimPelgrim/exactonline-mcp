# Data Model: Balance Sheet & Financial Reporting Tools

**Feature**: 001-balance-sheet-financial
**Date**: 2025-12-23

## Overview

This document defines the data models (Python dataclasses) for the financial reporting tools.

## Dataclasses

### ProfitLossOverview

Summary profit and loss statement with year-over-year comparison.

```python
@dataclass
class ProfitLossOverview:
    """Profit and loss overview with year-over-year comparison.

    Args:
        division: Exact Online division code.
        current_year: Current fiscal year.
        previous_year: Previous fiscal year for comparison.
        currency_code: Currency (typically EUR).
        revenue_current_year: Total revenue current year.
        revenue_previous_year: Total revenue previous year.
        costs_current_year: Total costs current year.
        costs_previous_year: Total costs previous year.
        result_current_year: Net result current year (revenue - costs).
        result_previous_year: Net result previous year.
        current_period: Current reporting period (1-12).
        revenue_current_period: Revenue for current period.
        costs_current_period: Costs for current period.
        result_current_period: Net result for current period.
    """
    division: int
    current_year: int
    previous_year: int
    currency_code: str
    revenue_current_year: float
    revenue_previous_year: float
    costs_current_year: float
    costs_previous_year: float
    result_current_year: float
    result_previous_year: float
    current_period: int
    revenue_current_period: float
    costs_current_period: float
    result_current_period: float
```

**Validation Rules**:
- `current_year` must be >= `previous_year`
- All monetary values can be negative (loss scenarios)
- `current_period` range: 1-12

---

### GLAccountBalance

Balance for a single general ledger account at a specific period.

```python
@dataclass
class GLAccountBalance:
    """Balance for a GL account at a specific reporting period.

    Args:
        gl_account_id: Exact Online account GUID.
        gl_account_code: Account code (e.g., "1300").
        gl_account_description: Account name (e.g., "Debiteuren").
        amount: Net balance amount.
        amount_debit: Total debit movements.
        amount_credit: Total credit movements.
        balance_type: "B" (balance sheet) or "W" (profit/loss).
        account_type: Numeric type code (20, 40, 110, etc.).
        account_type_description: Human-readable type (e.g., "Accounts receivable").
        reporting_year: Fiscal year.
        reporting_period: Period number (1-12).
    """
    gl_account_id: str
    gl_account_code: str
    gl_account_description: str
    amount: float
    amount_debit: float
    amount_credit: float
    balance_type: str  # "B" or "W"
    account_type: int
    account_type_description: str
    reporting_year: int
    reporting_period: int
```

**Validation Rules**:
- `balance_type` must be "B" or "W"
- `reporting_period` range: 0-12 (0 for opening balance)
- `amount` = `amount_debit` - `amount_credit` (for debit-normal accounts)

---

### BalanceSheetSummary

Aggregated balance sheet with categorized totals.

```python
@dataclass
class BalanceSheetCategory:
    """A category within the balance sheet.

    Args:
        name: Category name (e.g., "Liquide middelen", "Vorderingen").
        amount: Total amount for this category.
        account_count: Number of accounts in this category.
    """
    name: str
    amount: float
    account_count: int


@dataclass
class BalanceSheetSummary:
    """Balance sheet summary grouped by category.

    Args:
        division: Exact Online division code.
        reporting_year: Fiscal year.
        reporting_period: Period number.
        currency_code: Currency (typically EUR).
        total_assets: Sum of all asset categories.
        total_liabilities: Sum of all liability categories.
        total_equity: Sum of equity accounts.
        assets: List of asset categories with amounts.
        liabilities: List of liability categories with amounts.
        equity: List of equity categories with amounts.
    """
    division: int
    reporting_year: int
    reporting_period: int
    currency_code: str
    total_assets: float
    total_liabilities: float
    total_equity: float
    assets: list[BalanceSheetCategory]
    liabilities: list[BalanceSheetCategory]
    equity: list[BalanceSheetCategory]
```

**Validation Rules**:
- `total_assets` should approximately equal `total_liabilities` + `total_equity` (accounting equation)
- All amounts can be negative

---

### AgingEntry

Entry in an aging report for receivables or payables.

```python
@dataclass
class AgingEntry:
    """Entry in aging receivables or payables report.

    Args:
        account_id: Exact Online account GUID.
        account_code: Customer/supplier code.
        account_name: Customer/supplier name.
        total_amount: Total outstanding amount.
        age_0_30: Amount outstanding 0-30 days.
        age_31_60: Amount outstanding 31-60 days.
        age_61_90: Amount outstanding 61-90 days.
        age_over_90: Amount outstanding over 90 days.
        currency_code: Currency (typically EUR).
    """
    account_id: str
    account_code: str
    account_name: str
    total_amount: float
    age_0_30: float
    age_31_60: float
    age_61_90: float
    age_over_90: float
    currency_code: str
```

**Validation Rules**:
- `total_amount` = sum of all age buckets
- Amounts can be negative (credit balances)

---

### TransactionLine

Individual journal entry line for drill-down into account activity.

```python
@dataclass
class TransactionLine:
    """Individual transaction line from a journal entry.

    Args:
        id: Exact Online transaction line GUID.
        date: Transaction date (ISO format YYYY-MM-DD).
        financial_year: Fiscal year.
        financial_period: Period number (1-12).
        gl_account_code: GL account code.
        gl_account_description: GL account name.
        description: Transaction description/memo.
        amount: Amount in default currency (positive=debit, negative=credit).
        entry_number: Journal entry number.
        journal_code: Journal/dagboek code.
    """
    id: str
    date: str
    financial_year: int
    financial_period: int
    gl_account_code: str
    gl_account_description: str
    description: str
    amount: float
    entry_number: int
    journal_code: str
```

**Validation Rules**:
- `date` in ISO format YYYY-MM-DD
- `financial_period` range: 1-12
- `amount` positive for debit, negative for credit

---

## Entity Relationships

```
ProfitLossOverview
    └── Standalone summary (no relationships)

GLAccountBalance
    └── References GLAccount by gl_account_id/code
    └── Can drill down to TransactionLine records

BalanceSheetSummary
    └── Aggregates multiple GLAccountBalance records
    └── Contains BalanceSheetCategory sub-entities

AgingEntry
    └── References Account (customer/supplier) by account_id

TransactionLine
    └── References GLAccount by gl_account_code
    └── Belongs to Journal by journal_code
```

## Account Type Mapping

For balance sheet categorization:

```python
ACCOUNT_TYPE_CATEGORIES = {
    # Assets
    10: ("assets", "Kas"),
    12: ("assets", "Bank"),
    20: ("assets", "Debiteuren"),
    30: ("assets", "Vaste activa"),

    # Liabilities
    40: ("liabilities", "Crediteuren"),
    50: ("liabilities", "BTW"),
    60: ("liabilities", "Kortlopende schulden"),

    # Equity
    90: ("equity", "Overig"),  # Needs code-based refinement

    # P&L (not on balance sheet)
    110: ("pl", "Omzet"),
    111: ("pl", "Kostprijs omzet"),
    121: ("pl", "Bedrijfskosten"),
}
```
