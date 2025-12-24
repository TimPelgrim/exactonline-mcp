# Research: Bank & Purchase Data Tools

**Feature**: 004-bank-purchase-data
**Date**: 2025-12-24

## Endpoint Discovery

### financialtransaction/BankEntryLines

**Status**: ✅ Confirmed working

**Endpoint**: `financialtransaction/BankEntryLines`

**Sample Query**:
```
GET /api/v1/{division}/financialtransaction/BankEntryLines?$top=5&$select=ID,Date,Description,AmountDC,GLAccountCode
```

**Available Fields** (from exploration):
- `ID` - GUID for the transaction line
- `Date` - Transaction date (OData format)
- `Description` - Transaction description/memo
- `AmountDC` - Amount in default currency (negative = outflow, positive = inflow)
- `AmountFC` - Amount in foreign currency
- `Account` - Related party GUID (customer/supplier)
- `AccountCode` - Related party code
- `AccountName` - Related party name
- `GLAccount` - GL account GUID
- `GLAccountCode` - GL account code (e.g., "1055" for bank account)
- `GLAccountDescription` - GL account name
- `EntryID` - Parent entry GUID
- `EntryNumber` - Journal entry number
- `DocumentNumber` - Source document number
- `DocumentSubject` - Document description
- `Notes` - Additional notes
- `OurRef` - Internal reference
- `Project` - Project GUID (if applicable)
- `ProjectCode` - Project code
- `ProjectDescription` - Project name
- `Created`, `Modified` - Timestamps
- `Creator`, `CreatorFullName` - Who created
- `Division` - Division code

**Key Findings**:
- Rich data including related party, GL account, and project information
- AmountDC follows standard accounting sign convention
- OData date format `/Date(ms)/` needs parsing
- Can filter by Date, GLAccountCode for bank account filtering

---

### purchase/PurchaseInvoices

**Status**: ⚠️ May require Purchase module

**Endpoint**: `purchase/PurchaseInvoices`

**Test Result**: "Division not accessible" error on both test divisions

**Implication**: This endpoint requires the Purchase module subscription in Exact Online. Not all divisions have this module enabled.

**Handling Strategy**:
- Implement the tool but handle the "Division not accessible" error gracefully
- Return clear error message explaining module requirement
- Document as optional functionality

---

## Design Decisions

### Decision 1: Field Selection for BankTransaction

**Decision**: Include core transaction fields plus related party and GL account info

**Selected Fields**:
- `ID`, `Date`, `Description`, `AmountDC`
- `AccountCode`, `AccountName` (related party)
- `GLAccountCode`, `GLAccountDescription` (bank account)
- `EntryNumber`, `DocumentSubject`
- `Notes`, `OurRef`

**Rationale**: These fields provide enough context for Claude to answer questions like "What did we pay to X?" while keeping payload size reasonable.

**Alternatives Considered**:
- All fields: Too verbose, includes rarely-needed metadata
- Minimal fields: Not enough context for useful analysis

### Decision 2: Date Filtering

**Decision**: Use OData datetime filter with user-provided ISO dates

**Filter Format**:
```
Date ge datetime'{start_date}' and Date le datetime'{end_date}'
```

**Rationale**: Consistent with existing tools (receivables, transactions). Users provide ISO dates, we convert to OData format.

### Decision 3: Bank Account Filtering

**Decision**: Filter by GLAccountCode (trim function for padded codes)

**Filter Format**:
```
trim(GLAccountCode) eq '{account_code}'
```

**Rationale**: Bank accounts are GL accounts (Type 12). Users know their bank account codes (e.g., "1055"). Consistent with how we handle AccountCode filtering in receivables.

### Decision 4: Purchase Invoices Graceful Degradation

**Decision**: Implement tool but handle module unavailability gracefully

**Error Response**:
```python
{
    "error": "module_not_available",
    "message": "Purchase module not enabled for this division",
    "action": "Contact your Exact Online administrator to enable the Purchase module"
}
```

**Rationale**: Better to expose the tool and explain limitations than to silently omit functionality that might be available for some users.

---

## API Patterns

### Date Format Conversion

Same pattern as open receivables:
```python
from exactonline_mcp.client import parse_odata_date
# /Date(1590451200000)/ -> "2020-05-26"
```

### Response Structure

Follow existing tool patterns:
```python
{
    "division": 1913290,
    "count": 50,
    "items": [...]
}
```

No pre-computed totals or aggregations - raw data only (per spec).

### Error Handling

Use existing `ExactOnlineError` hierarchy:
- `DivisionNotAccessibleError` for module issues
- Standard error dict format with `error`, `message`, `action`
