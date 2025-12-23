# Feature Specification: Balance Sheet & Financial Reporting Tools

**Feature Branch**: `001-balance-sheet-financial`
**Created**: 2025-12-23
**Status**: Draft
**Input**: User description: "Add MCP tools for accessing balance sheet data, profit/loss overview, and general ledger account balances from Exact Online."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Profit & Loss Overview (Priority: P1)

As a business owner or financial controller, I want to see a high-level profit and loss overview so I can quickly understand the company's financial performance.

**Why this priority**: This is the most commonly requested financial insight - understanding revenue, costs, and profit at a glance with year-over-year comparison. Provides immediate value.

**Independent Test**: Call `get_profit_loss_overview` and verify it returns revenue, costs, and result for current year vs previous year.

**Acceptance Scenarios**:

1. **Given** authenticated user with division access, **When** calling `get_profit_loss_overview`, **Then** return P&L summary with current year revenue, costs, result and previous year comparison
2. **Given** authenticated user, **When** calling with optional division parameter, **Then** return P&L for specified division
3. **Given** no data for division, **When** calling `get_profit_loss_overview`, **Then** return zero values gracefully

---

### User Story 2 - Query GL Account Balances (Priority: P1)

As an accountant, I want to check the current balance on specific grootboekrekeningen (GL accounts) so I can verify account status and prepare financial statements.

**Why this priority**: Core functionality for checking specific account balances - essential for any financial reporting use case.

**Independent Test**: Call `get_gl_account_balance` with account code "1300" (Debiteuren) and verify it returns the current balance.

**Acceptance Scenarios**:

1. **Given** valid GL account code, **When** calling `get_gl_account_balance`, **Then** return balance, debit amount, credit amount for that account
2. **Given** optional year/period parameters, **When** calling with specific period, **Then** return balance for that period
3. **Given** invalid GL account code, **When** calling `get_gl_account_balance`, **Then** return clear error message
4. **Given** account with no transactions, **When** querying balance, **Then** return zero balance

---

### User Story 3 - View Balance Sheet Summary (Priority: P2)

As a business owner, I want to see a balance sheet summary with assets, liabilities, and equity so I can understand the company's financial position.

**Why this priority**: Important for year-end reporting and financial health assessment, but less frequently accessed than P&L.

**Independent Test**: Call `get_balance_sheet_summary` and verify it returns categorized totals for assets, liabilities, and equity.

**Acceptance Scenarios**:

1. **Given** authenticated user, **When** calling `get_balance_sheet_summary`, **Then** return totals grouped by account type (assets, liabilities, equity)
2. **Given** optional year parameter, **When** calling with specific year, **Then** return balance sheet as of year-end
3. **Given** optional period parameter, **When** calling with specific period, **Then** return balance sheet as of that period

---

### User Story 4 - List GL Accounts with Balances (Priority: P2)

As an accountant, I want to list all GL accounts with their current balances filtered by type so I can see the composition of costs, revenue, assets, or liabilities.

**Why this priority**: Enables detailed analysis of what makes up each category - essential for understanding cost/revenue composition.

**Independent Test**: Call `list_gl_account_balances` with filter `balance_type="W"` (P&L) and verify it returns all revenue/cost accounts with balances.

**Acceptance Scenarios**:

1. **Given** filter by balance_type "B" (balance sheet), **When** calling `list_gl_account_balances`, **Then** return all balance sheet accounts with balances
2. **Given** filter by balance_type "W" (profit/loss), **When** calling `list_gl_account_balances`, **Then** return all P&L accounts with balances
3. **Given** filter by account_type (e.g., 121 for "Sales, general administrative expenses"), **When** calling, **Then** return only accounts of that type
4. **Given** optional year/period, **When** calling with period filter, **Then** return balances for that period

---

### User Story 5 - View Aging Reports (Priority: P3)

As a financial controller, I want to see aging reports for receivables and payables so I can manage cash flow and identify overdue items.

**Why this priority**: Important for cash flow management but less frequently needed than core balance/P&L queries.

**Independent Test**: Call `get_aging_receivables` and verify it returns accounts with aging buckets (0-30, 31-60, 61-90, >90 days).

**Acceptance Scenarios**:

1. **Given** authenticated user, **When** calling `get_aging_receivables`, **Then** return list of customers with outstanding amounts by aging bucket
2. **Given** authenticated user, **When** calling `get_aging_payables`, **Then** return list of suppliers with outstanding amounts by aging bucket
3. **Given** no outstanding items, **When** calling aging reports, **Then** return empty list gracefully

---

### User Story 6 - View GL Account Transactions (Priority: P2)

As an accountant, I want to view individual transactions for a specific GL account so I can drill down into the details behind a balance and verify specific entries.

**Why this priority**: Essential for auditing and understanding what makes up an account balance - enables drill-down from summary to detail.

**Independent Test**: Call `get_gl_account_transactions` with account code "1300" and verify it returns individual transaction lines with dates, amounts, and descriptions.

**Acceptance Scenarios**:

1. **Given** valid GL account code, **When** calling `get_gl_account_transactions`, **Then** return list of transaction lines with date, amount, description, entry number
2. **Given** optional year/period parameters, **When** calling with specific period, **Then** return only transactions for that period
3. **Given** optional date range (start_date, end_date), **When** calling with date filter, **Then** return transactions within that range
4. **Given** account with many transactions, **When** calling without limit, **Then** return paginated results (default limit, e.g., 100)
5. **Given** invalid GL account code, **When** calling `get_gl_account_transactions`, **Then** return clear error message

---

### Edge Cases

- What happens when GL account code doesn't exist? Return clear error message.
- What happens when division has no financial data? Return zero values/empty lists.
- What happens when requested period is in the future? Return empty or error.
- How to handle accounts with only debit or only credit entries? Show actual amounts.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide P&L overview with revenue, costs, and result for current vs previous year
- **FR-002**: System MUST allow querying individual GL account balances by account code
- **FR-003**: System MUST support filtering by financial year and period
- **FR-004**: System MUST return balance sheet totals grouped by account type
- **FR-005**: System MUST list GL accounts with balances, filterable by balance type (B/W)
- **FR-006**: System MUST provide aging reports for receivables with aging buckets
- **FR-007**: System MUST provide aging reports for payables with aging buckets
- **FR-008**: System MUST handle empty results gracefully (zero values, empty arrays)
- **FR-009**: All tools MUST support optional division parameter (default to current division)
- **FR-010**: System MUST provide transaction detail view for a specific GL account
- **FR-011**: Transaction queries MUST support filtering by year/period or date range
- **FR-012**: Transaction queries MUST support pagination with configurable limit

### Key Entities

- **GLAccount**: General ledger account with code, description, type, balance type (B=balance sheet, W=profit/loss)
- **ReportingBalance**: Balance for a GL account at a specific period, includes amount, debit, credit
- **ProfitLossOverview**: Summary P&L with revenue, costs, result for current and previous year
- **AgingEntry**: Receivable/payable entry with account, total amount, and aging bucket breakdowns
- **TransactionLine**: Individual journal entry line with date, amount, description, entry number, journal code

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can retrieve P&L overview in a single tool call
- **SC-002**: Users can check any GL account balance by providing account code
- **SC-003**: Users can filter account balances by financial year and period
- **SC-004**: Aging reports show clear breakdown by 30-day buckets
- **SC-005**: All tools return structured data that Claude can format for user presentation
- **SC-006**: Users can drill down from account balance to individual transactions
