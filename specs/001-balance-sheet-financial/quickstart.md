# Quickstart: Balance Sheet & Financial Reporting Tools

**Feature**: 001-balance-sheet-financial
**Date**: 2025-12-23

## Overview

The Balance Sheet & Financial Reporting feature adds seven MCP tools for accessing financial data from Exact Online:

1. **get_profit_loss_overview** - P&L summary with year-over-year comparison
2. **get_gl_account_balance** - Balance for a specific GL account
3. **get_balance_sheet_summary** - Balance sheet totals by category
4. **list_gl_account_balances** - List accounts with balances, filterable
5. **get_aging_receivables** - Outstanding customer invoices by age
6. **get_aging_payables** - Outstanding supplier invoices by age
7. **get_gl_account_transactions** - Drill down into individual transactions

## Prerequisites

- Authenticated with Exact Online (run `uv run python -m exactonline_mcp.auth` if needed)
- Division with financial transactions

## Tool Usage

### get_profit_loss_overview

Get high-level P&L summary with current year vs previous year.

**Parameters**:
- `division` (optional) - Division code, defaults to current

**Example Prompts**:
```
"Show me the profit and loss overview"
"What's our revenue this year compared to last year?"
"How is the company performing financially?"
```

**Example Response**:
```json
{
  "division": 1913290,
  "current_year": 2025,
  "previous_year": 2024,
  "currency_code": "EUR",
  "revenue_current_year": 971192.32,
  "revenue_previous_year": 942635.79,
  "costs_current_year": 835096.97,
  "costs_previous_year": 931079.75,
  "result_current_year": 136095.35,
  "result_previous_year": 11556.04
}
```

---

### get_gl_account_balance

Query balance for a specific grootboekrekening by account code.

**Parameters**:
- `account_code` (required) - GL account code (e.g., "1300", "8000")
- `year` (optional) - Fiscal year, defaults to current
- `period` (optional) - Period 1-12, defaults to current
- `division` (optional) - Division code

**Example Prompts**:
```
"What's the balance on account 1300 (Debiteuren)?"
"Show me the current balance for account 8000"
"What was the balance on account 1600 at the end of 2024?"
```

**Example Response**:
```json
{
  "gl_account_code": "1300",
  "gl_account_description": "Debiteuren",
  "amount": 138301.82,
  "amount_debit": 138301.82,
  "amount_credit": 0,
  "balance_type": "B",
  "account_type": 20,
  "account_type_description": "Accounts receivable",
  "reporting_year": 2024,
  "reporting_period": 12
}
```

---

### get_balance_sheet_summary

Get balance sheet totals grouped by category (assets, liabilities, equity).

**Parameters**:
- `year` (optional) - Fiscal year
- `period` (optional) - Period 1-12
- `division` (optional) - Division code

**Example Prompts**:
```
"Show me the balance sheet summary"
"What are our total assets and liabilities?"
"Give me a balance sheet overview for year-end 2024"
```

**Example Response**:
```json
{
  "division": 1913290,
  "reporting_year": 2024,
  "reporting_period": 12,
  "currency_code": "EUR",
  "total_assets": 250000.00,
  "total_liabilities": 180000.00,
  "total_equity": 70000.00,
  "assets": [
    {"name": "Bank", "amount": 50000.00, "account_count": 3},
    {"name": "Debiteuren", "amount": 138301.82, "account_count": 1}
  ],
  "liabilities": [
    {"name": "Crediteuren", "amount": 30876.27, "account_count": 1}
  ]
}
```

---

### list_gl_account_balances

List all GL accounts with balances, optionally filtered.

**Parameters**:
- `balance_type` (optional) - "B" for balance sheet, "W" for P&L
- `account_type` (optional) - Account type code (20, 110, 121, etc.)
- `year` (optional) - Fiscal year
- `period` (optional) - Period 1-12
- `division` (optional) - Division code

**Example Prompts**:
```
"Show me all revenue accounts with their balances"
"List all P&L accounts for 2024"
"What accounts make up our costs?"
```

**Example Response**:
```json
{
  "division": 1913290,
  "reporting_year": 2024,
  "reporting_period": 12,
  "total_accounts": 5,
  "accounts": [
    {
      "gl_account_code": "8000",
      "gl_account_description": "Omzet App development",
      "amount": -86852.50,
      "balance_type": "W",
      "account_type": 110,
      "account_type_description": "Revenue"
    }
  ]
}
```

---

### get_aging_receivables

Outstanding customer invoices with aging breakdown.

**Parameters**:
- `division` (optional) - Division code

**Example Prompts**:
```
"Show me outstanding receivables"
"Which customers have overdue invoices?"
"What's the aging on our debiteuren?"
```

**Example Response**:
```json
{
  "division": 1913290,
  "currency_code": "EUR",
  "total_outstanding": 122603.26,
  "total_0_30": 108189.08,
  "total_31_60": 13213.20,
  "total_61_90": 0,
  "total_over_90": 1206.98,
  "customer_count": 5,
  "customers": [
    {
      "account_name": "Retail Media Support Belgium B.V.",
      "total_amount": 87092.78,
      "age_0_30": 87092.78,
      "age_31_60": 0,
      "age_61_90": 0,
      "age_over_90": 0
    }
  ]
}
```

---

### get_aging_payables

Outstanding supplier invoices with aging breakdown.

**Parameters**:
- `division` (optional) - Division code

**Example Prompts**:
```
"Show me outstanding payables"
"What bills do we need to pay?"
"Which suppliers have old invoices?"
```

---

### get_gl_account_transactions

Drill down into individual transactions for a specific GL account.

**Parameters**:
- `account_code` (required) - GL account code (e.g., "1300", "8000")
- `year` (optional) - Fiscal year filter
- `period` (optional) - Period 1-12 (used with year)
- `start_date` (optional) - Start date (YYYY-MM-DD)
- `end_date` (optional) - End date (YYYY-MM-DD)
- `limit` (optional) - Max transactions to return (default 100)
- `division` (optional) - Division code

**Example Prompts**:
```
"Show me the transactions on account 1300"
"What entries were made to the bank account in December?"
"List all transactions for account 8000 in 2024"
"Show the last 50 transactions on the crediteuren account"
```

**Example Response**:
```json
{
  "division": 1913290,
  "gl_account_code": "1060",
  "gl_account_description": "NL39 BUNQ 2036 4870 09",
  "total_transactions": 3,
  "transactions": [
    {
      "id": "0ba3aaf0-bca9-4ee3-9a12-0002140ada17",
      "date": "2020-06-30",
      "financial_year": 2020,
      "financial_period": 6,
      "description": "Refund: NOTION LABS INC SAN FRANCISCO",
      "amount": 4.46,
      "entry_number": 2050294,
      "journal_code": "5"
    }
  ]
}
```

---

## Common Use Cases

### Monthly Financial Review
```
"Show me the P&L overview"
"What's our current cash position?" (check bank accounts)
"Are there any overdue receivables?"
```

### Year-End Reporting
```
"Show me the balance sheet summary for period 12, 2024"
"List all P&L accounts for 2024"
"What's the balance on account 0900 (Eigen vermogen)?"
```

### Cash Flow Management
```
"Show aging receivables - who owes us money?"
"Show aging payables - what do we owe?"
"What's the balance on our bank accounts?"
```

### Audit & Investigation
```
"Show me all transactions on the bank account in December"
"What entries were made to account 4430 this year?"
"Drill down into the transactions for account 1300"
```

## Account Type Reference

| Type | Description | Category |
|------|-------------|----------|
| 10 | Kas (Cash) | Assets |
| 12 | Bank | Assets |
| 20 | Debiteuren (Receivables) | Assets |
| 30 | Vaste activa (Fixed assets) | Assets |
| 40 | Crediteuren (Payables) | Liabilities |
| 50 | BTW | Liabilities |
| 60 | Kortlopende schulden | Liabilities |
| 90 | Overig | Equity/General |
| 110 | Omzet (Revenue) | P&L |
| 111 | Kostprijs omzet | P&L |
| 121 | Bedrijfskosten | P&L |
