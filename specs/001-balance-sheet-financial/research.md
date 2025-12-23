# Research: Balance Sheet & Financial Reporting Tools

**Feature**: 001-balance-sheet-financial
**Date**: 2025-12-23
**Status**: Complete

## Overview

This document captures API research findings for implementing financial reporting tools in the exactonline-mcp server.

## API Endpoint Research

### 1. Profit & Loss Overview

**Endpoint**: `read/financial/ProfitLossOverview`

**Decision**: Use this endpoint for P&L summary - provides exactly what's needed.

**Rationale**: Single API call returns complete P&L with year-over-year comparison. No need to aggregate from transaction lines.

**Sample Response** (YipYip BV, 2025):
```json
{
  "CurrentYear": 2025,
  "PreviousYear": 2024,
  "CurrentPeriod": 12,
  "CurrencyCode": "EUR",
  "ResultCurrentYear": 136095.35,
  "ResultPreviousYear": 11556.04,
  "RevenueCurrentYear": 971192.32,
  "RevenuePreviousYear": 942635.79,
  "CostsCurrentYear": 835096.97,
  "CostsPreviousYear": 931079.75,
  "ResultCurrentPeriod": -66014.66,
  "RevenueCurrentPeriod": 18831.51,
  "CostsCurrentPeriod": 84846.17
}
```

**Key Fields**:
- `RevenueCurrentYear`, `RevenuePreviousYear` - Total revenue
- `CostsCurrentYear`, `CostsPreviousYear` - Total costs
- `ResultCurrentYear`, `ResultPreviousYear` - Net result (profit/loss)
- `*CurrentPeriod` variants - Current period values
- `CurrencyCode` - Always EUR for Dutch divisions

**Alternatives Considered**:
- Aggregating from `financial/ReportingBalance` with BalanceType="W" - More complex, requires multiple calls
- Using `financialtransaction/TransactionLines` - Too granular, would need extensive aggregation

---

### 2. GL Account Balances

**Endpoint**: `financial/ReportingBalance`

**Decision**: Use this endpoint for account-level balances with period filtering.

**Rationale**: Provides balance by GL account, year, and period. Includes debit/credit breakdown.

**Query Requirements**:
- Requires `$top=1` or `$select` parameter (API quirk)
- Filter by `ReportingYear` and `ReportingPeriod`
- Filter by `GLAccountCode` for specific account lookup

**Sample Response** (Period 12, 2024):
```json
{
  "Amount": 138301.82,
  "AmountDebit": 138301.82,
  "AmountCredit": 0,
  "BalanceType": "B",
  "GLAccountCode": "1300",
  "GLAccountDescription": "Debiteuren",
  "ReportingYear": 2024,
  "ReportingPeriod": 12,
  "Type": 20,
  "Status": 50
}
```

**Key Fields**:
- `Amount` - Net balance (debit - credit, considering BalanceSide)
- `AmountDebit`, `AmountCredit` - Gross movements
- `BalanceType` - "B" (Balance sheet) or "W" (Profit/Loss / Winst-verlies)
- `Type` - Account type code (20=Accounts receivable, 40=Accounts payable, etc.)
- `Status` - 50 = finalized

**Account Types Discovered**:
| Type | Description |
|------|-------------|
| 10 | Cash |
| 12 | Bank |
| 20 | Accounts receivable |
| 30 | Fixed assets |
| 40 | Accounts payable |
| 50 | VAT |
| 60 | Current portion of debt |
| 90 | General |
| 110 | Revenue |
| 111 | Cost of goods |
| 121 | Sales, general administrative expenses |

---

### 3. Chart of Accounts

**Endpoint**: `financial/GLAccounts`

**Decision**: Use for account metadata lookup (code, description, type).

**Rationale**: Provides account master data including type categorization for balance sheet grouping.

**Sample Response**:
```json
{
  "ID": "58d37649-be42-4232-94b1-019f9bc96b1e",
  "Code": "1300",
  "Description": "Debiteuren",
  "BalanceType": "B",
  "BalanceSide": "D",
  "Type": 20,
  "TypeDescription": "Accounts receivable"
}
```

**Key Fields**:
- `Code` - GL account code (e.g., "1300", "8000")
- `Description` - Dutch account name
- `BalanceType` - "B" (balance sheet) or "W" (P&L)
- `BalanceSide` - "D" (debit normal) or "C" (credit normal)
- `Type`, `TypeDescription` - Account classification

---

### 4. Aging Reports

**Endpoints**:
- `read/financial/AgingReceivablesList` - Outstanding customer invoices
- `read/financial/AgingPayablesList` - Outstanding supplier invoices

**Decision**: Use these pre-built aging reports - already provide aging bucket breakdown.

**Rationale**: API provides complete aging analysis with 30-day buckets. No calculation needed.

**Sample Response** (Receivables):
```json
{
  "AccountId": "2fff0522-e25e-426c-b05a-156338b6d891",
  "AccountCode": "592",
  "AccountName": "Retail Media Support Belgium B.V.",
  "TotalAmount": 87092.78,
  "AgeGroup1": 1,
  "AgeGroup1Description": "<= 30",
  "AgeGroup1Amount": 87092.78,
  "AgeGroup2": 2,
  "AgeGroup2Description": "31 - 60",
  "AgeGroup2Amount": 0,
  "AgeGroup3": 3,
  "AgeGroup3Description": "61 - 90",
  "AgeGroup3Amount": 0,
  "AgeGroup4": 4,
  "AgeGroup4Description": "> 90",
  "AgeGroup4Amount": 0,
  "CurrencyCode": "EUR"
}
```

**Aging Buckets**:
| Group | Description |
|-------|-------------|
| 1 | <= 30 days |
| 2 | 31-60 days |
| 3 | 61-90 days |
| 4 | > 90 days |

---

### 5. Financial Periods

**Endpoint**: `financial/FinancialPeriods`

**Decision**: Use for period validation and date range lookup.

**Rationale**: Needed to validate user-provided periods and get period boundaries.

**Sample Response**:
```json
{
  "FinYear": 2024,
  "FinPeriod": 12,
  "StartDate": "/Date(1733011200000)/",
  "EndDate": "/Date(1735603200000)/"
}
```

---

### 6. Transaction Lines

**Endpoint**: `financialtransaction/TransactionLines`

**Decision**: Use for drill-down into individual transactions for a GL account.

**Rationale**: Enables audit trail and detail view behind account balances. Supports filtering by GL account, period, and date range.

**Sample Response**:
```json
{
  "ID": "0ba3aaf0-bca9-4ee3-9a12-0002140ada17",
  "Date": "/Date(1593475200000)/",
  "FinancialYear": 2020,
  "FinancialPeriod": 6,
  "GLAccountCode": "1060",
  "Description": "Refund: NOTION LABS INC SAN FRANCISCO",
  "AmountDC": 4.46,
  "EntryNumber": 2050294,
  "JournalCode": "5"
}
```

**Key Fields**:
- `Date` - Transaction date (epoch timestamp)
- `GLAccountCode` - GL account for filtering
- `Description` - Transaction description/memo
- `AmountDC` - Amount in default currency (positive=debit, negative=credit)
- `EntryNumber` - Journal entry number
- `JournalCode` - Journal/dagboek code
- `FinancialYear`, `FinancialPeriod` - For period filtering

**Filter Examples**:
- By account: `GLAccountCode eq '1300'`
- By period: `FinancialYear eq 2024 and FinancialPeriod eq 12`
- By date range: `Date ge datetime'2024-01-01' and Date le datetime'2024-12-31'`

---

## Balance Sheet Grouping Strategy

**Decision**: Group accounts by Type field for balance sheet summary.

**Rationale**: The `Type` field provides standard accounting categories that map to balance sheet sections.

**Grouping**:
```
Assets (Activa):
  - Type 10, 12: Liquide middelen (Cash & Bank)
  - Type 20: Vorderingen (Receivables)
  - Type 30: Vaste activa (Fixed assets)

Liabilities (Passiva):
  - Type 40: Schulden (Payables)
  - Type 50: BTW schulden (VAT liabilities)
  - Type 60: Kortlopende schulden (Current liabilities)

Equity:
  - Type 90 with specific codes: Eigen vermogen
```

**Alternatives Considered**:
- Using RGS classification (`GLAccountClassificationMappings`) - More accurate for jaarrekening but adds complexity
- Grouping by account code ranges (0xxx, 1xxx) - Less reliable than Type field

---

## Implementation Notes

### API Quirks

1. **ReportingBalance requires special query**: Must use `$top=1` or `$select` parameter, cannot query without restrictions
2. **Date format**: Exact Online uses `/Date(timestamp)/` format in responses
3. **Period numbering**: 1-12 for months, may have period 0 for opening balance
4. **Amount signs**: Credit accounts (revenue) have negative amounts in ReportingBalance

### Error Handling

- Invalid GL account code: API returns empty result set
- Future period: API returns empty result set
- Division without financial data: API returns empty result set
- All cases return valid JSON, no HTTP errors

### Performance

- `ProfitLossOverview`: Single call, very fast
- `ReportingBalance`: May need pagination for full account list
- `AgingLists`: Pre-aggregated, typically <100 records
- `GLAccounts`: May have 100+ accounts, use pagination

---

## Unresolved Questions

None - all technical questions resolved through API exploration.
