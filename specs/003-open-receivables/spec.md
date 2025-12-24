# Feature Specification: Open Receivables Tool

**Feature ID**: 003-open-receivables
**Status**: Draft
**Created**: 2025-12-23

## Summary

Add MCP tools for accessing detailed open receivables from Exact Online via the `cashflow/Receivables` endpoint. This provides invoice-level detail that complements the existing `AgingReceivablesList` which only shows bucketed totals per customer.

## Problem Statement

Currently, the `get_aging_receivables` tool (via `read/financial/AgingReceivablesList`) shows outstanding amounts grouped by aging buckets (0-30, 31-60, 61-90, >90 days) per customer. However, users need to:

1. See **individual invoices** that are outstanding, not just totals
2. Know the **due date** of each invoice for prioritization
3. View the **original invoice amount** vs **remaining amount**
4. Filter by specific customers or date ranges
5. Identify **overdue** invoices specifically for follow-up

## Target Users

- Business owners checking payment status
- Accountants reconciling receivables
- Credit controllers following up on overdue payments

## Functional Requirements

### FR-1: List Open Receivables

**Tool**: `get_open_receivables`

List all open (unpaid) receivables with filtering options.

**Parameters**:
- `division` (optional): Division code, defaults to current
- `top` (optional): Max records, default 100, max 1000
- `account_code` (optional): Filter by customer code
- `overdue_only` (optional): Only show items past due date

**Returns**:
- List of open receivables with: customer, invoice number, invoice date, due date, original amount, remaining amount, description, payment terms
- Summary totals

### FR-2: Get Customer Open Items

**Tool**: `get_customer_open_items`

Get all open items for a specific customer.

**Parameters**:
- `division` (optional): Division code
- `account_code` (required): Customer account code

**Returns**:
- Customer details
- List of open invoices
- Total outstanding amount

### FR-3: Get Overdue Receivables

**Tool**: `get_overdue_receivables`

List receivables that are past their due date.

**Parameters**:
- `division` (optional): Division code
- `days_overdue` (optional): Minimum days overdue (default: 0 = any overdue)
- `top` (optional): Max records, default 100

**Returns**:
- List of overdue items with days overdue calculated
- Sorted by days overdue (most overdue first)
- Summary totals

## API Endpoint Details

**Endpoint**: `cashflow/Receivables`

**Key Fields** (discovered via exploration):

| Field | Description | Example |
|-------|-------------|---------|
| `AccountCode` | Customer code | "400" |
| `AccountName` | Customer name | "FTB Mobile B.V." |
| `InvoiceNumber` | Invoice number | 5124 |
| `InvoiceDate` | Invoice date | /Date(1756684800000)/ |
| `DueDate` | Payment due date | /Date(1757894400000)/ |
| `TransactionAmountDC` | Original invoice amount | 605 (positive), -2032.8 (credit) |
| `AmountDC` | Remaining open amount | -605 (to receive), 2032.8 (credit) |
| `IsFullyPaid` | Payment status | false |
| `PaymentConditionDescription` | Payment terms | "14 dagen" |
| `Description` | Invoice description | "FTB Mobile september Hosting" |
| `Currency` | Currency code | "EUR" |

**Important Notes**:
- `TransactionAmountDC`: Positive = invoice, Negative = credit note
- `AmountDC`: Negative = amount to receive, Positive = credit/overpayment
- Filter `IsFullyPaid eq false` for open items only
- Dates are in millisecond timestamps

## Non-Functional Requirements

- **NFR-1**: Read-only operations only (GET requests)
- **NFR-2**: Respect 60 calls/minute rate limit
- **NFR-3**: Built-in pagination (max 1000 records per call)
- **NFR-4**: Clear error messages for auth/API failures

## Out of Scope

- Creating or modifying receivables
- Payment processing
- Automatic reminders or follow-ups
- Multi-currency conversion

## Success Criteria

1. Users can view individual open invoices per customer
2. Users can filter by customer or overdue status
3. Days overdue is calculated automatically
4. Tools integrate seamlessly with existing MCP server
