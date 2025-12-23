# Tasks: Balance Sheet & Financial Reporting Tools

**Input**: Design documents from `/specs/001-balance-sheet-financial/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓

**Tests**: Not explicitly requested in spec. Manual validation with real Exact Online data per constitution.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/exactonline_mcp/`, `tests/` at repository root

---

## Phase 1: Setup

**Purpose**: Verify existing project structure and add new endpoints to catalog

- [ ] T001 Verify existing project structure and dependencies in pyproject.toml
- [ ] T002 [P] Add financial reporting endpoints to catalog in src/exactonline_mcp/endpoints.py

---

## Phase 2: Foundational (Shared Infrastructure)

**Purpose**: Core dataclasses and helpers that all user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Add ProfitLossOverview dataclass to src/exactonline_mcp/models.py
- [ ] T004 [P] Add GLAccountBalance dataclass to src/exactonline_mcp/models.py
- [ ] T005 [P] Add BalanceSheetCategory dataclass to src/exactonline_mcp/models.py
- [ ] T006 [P] Add BalanceSheetSummary dataclass to src/exactonline_mcp/models.py
- [ ] T007 [P] Add AgingEntry dataclass to src/exactonline_mcp/models.py
- [ ] T008 [P] Add TransactionLine dataclass to src/exactonline_mcp/models.py
- [ ] T009 Add ACCOUNT_TYPE_CATEGORIES mapping constant to src/exactonline_mcp/models.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - View Profit & Loss Overview (Priority: P1) 🎯 MVP

**Goal**: Business owners can see P&L summary with year-over-year comparison

**Independent Test**: Call `get_profit_loss_overview` and verify it returns revenue, costs, and result for current year vs previous year.

### Implementation for User Story 1

- [ ] T010 [US1] Add helper function `fetch_profit_loss_overview` to src/exactonline_mcp/client.py
- [ ] T011 [US1] Implement `get_profit_loss_overview` MCP tool in src/exactonline_mcp/server.py
- [ ] T012 [US1] Add input validation for division parameter in src/exactonline_mcp/server.py
- [ ] T013 [US1] Handle empty/zero results gracefully in src/exactonline_mcp/server.py

**Checkpoint**: User Story 1 fully functional - can query P&L overview

---

## Phase 4: User Story 2 - Query GL Account Balances (Priority: P1)

**Goal**: Accountants can check current balance on specific grootboekrekeningen

**Independent Test**: Call `get_gl_account_balance` with account code "1300" (Debiteuren) and verify it returns the current balance.

### Implementation for User Story 2

- [ ] T014 [US2] Add helper function `fetch_reporting_balance` to src/exactonline_mcp/client.py
- [ ] T015 [US2] Add helper function `fetch_gl_account_by_code` to src/exactonline_mcp/client.py
- [ ] T016 [US2] Implement `get_gl_account_balance` MCP tool in src/exactonline_mcp/server.py
- [ ] T017 [US2] Add year/period parameter validation in src/exactonline_mcp/server.py
- [ ] T018 [US2] Handle invalid account code with clear error message in src/exactonline_mcp/server.py

**Checkpoint**: User Story 2 fully functional - can query individual account balances

---

## Phase 5: User Story 3 - View Balance Sheet Summary (Priority: P2)

**Goal**: Business owners can see balance sheet with assets, liabilities, and equity totals

**Independent Test**: Call `get_balance_sheet_summary` and verify it returns categorized totals for assets, liabilities, and equity.

### Implementation for User Story 3

- [ ] T019 [US3] Add helper function `fetch_all_balance_sheet_balances` to src/exactonline_mcp/client.py
- [ ] T020 [US3] Add helper function `aggregate_balances_by_category` to src/exactonline_mcp/client.py
- [ ] T021 [US3] Implement `get_balance_sheet_summary` MCP tool in src/exactonline_mcp/server.py
- [ ] T022 [US3] Add year/period parameter support in src/exactonline_mcp/server.py

**Checkpoint**: User Story 3 fully functional - can view balance sheet summary

---

## Phase 6: User Story 4 - List GL Accounts with Balances (Priority: P2)

**Goal**: Accountants can list all GL accounts filtered by type to see composition of costs/revenue

**Independent Test**: Call `list_gl_account_balances` with filter `balance_type="W"` (P&L) and verify it returns all revenue/cost accounts with balances.

### Implementation for User Story 4

- [ ] T023 [US4] Add helper function `fetch_filtered_balances` to src/exactonline_mcp/client.py
- [ ] T024 [US4] Implement `list_gl_account_balances` MCP tool in src/exactonline_mcp/server.py
- [ ] T025 [US4] Add balance_type filter ("B" or "W") support in src/exactonline_mcp/server.py
- [ ] T026 [US4] Add account_type filter support in src/exactonline_mcp/server.py

**Checkpoint**: User Story 4 fully functional - can list accounts with balances

---

## Phase 7: User Story 5 - View Aging Reports (Priority: P3)

**Goal**: Financial controllers can see aging reports for receivables and payables

**Independent Test**: Call `get_aging_receivables` and verify it returns accounts with aging buckets (0-30, 31-60, 61-90, >90 days).

### Implementation for User Story 5

- [ ] T027 [US5] Add helper function `fetch_aging_receivables` to src/exactonline_mcp/client.py
- [ ] T028 [P] [US5] Add helper function `fetch_aging_payables` to src/exactonline_mcp/client.py
- [ ] T029 [US5] Implement `get_aging_receivables` MCP tool in src/exactonline_mcp/server.py
- [ ] T030 [P] [US5] Implement `get_aging_payables` MCP tool in src/exactonline_mcp/server.py
- [ ] T031 [US5] Add aging bucket totals calculation in src/exactonline_mcp/server.py
- [ ] T032 [US5] Handle empty aging lists gracefully in src/exactonline_mcp/server.py

**Checkpoint**: User Story 5 fully functional - can view aging reports

---

## Phase 8: User Story 6 - View GL Account Transactions (Priority: P2)

**Goal**: Accountants can drill down into individual transactions for a specific GL account

**Independent Test**: Call `get_gl_account_transactions` with account code "1300" and verify it returns individual transaction lines with dates, amounts, and descriptions.

### Implementation for User Story 6

- [ ] T033 [US6] Add helper function `fetch_transaction_lines` to src/exactonline_mcp/client.py
- [ ] T034 [US6] Add date range filter support to `fetch_transaction_lines` in src/exactonline_mcp/client.py
- [ ] T035 [US6] Implement `get_gl_account_transactions` MCP tool in src/exactonline_mcp/server.py
- [ ] T036 [US6] Add year/period filter support in src/exactonline_mcp/server.py
- [ ] T037 [US6] Add start_date/end_date filter support in src/exactonline_mcp/server.py
- [ ] T038 [US6] Add pagination with configurable limit (default 100) in src/exactonline_mcp/server.py
- [ ] T039 [US6] Handle invalid account code with clear error message in src/exactonline_mcp/server.py

**Checkpoint**: User Story 6 fully functional - can drill down into transactions

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, validation, and improvements affecting all tools

- [ ] T040 [P] Update README.md with financial reporting tools documentation
- [ ] T041 [P] Run linting (uv run ruff check .) and fix any issues
- [ ] T042 Validate all seven tools with real Exact Online data
- [ ] T043 Run quickstart.md validation scenarios
- [ ] T044 Update CLAUDE.md with financial endpoints implementation notes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - verify existing structure
- **Foundational (Phase 2)**: Depends on Setup - adds shared models and helpers
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - P1 stories (US1, US2) can proceed in priority order
  - P2 stories (US3, US4, US6) can run after P1 or in parallel
  - P3 story (US5) can run after P1 or in parallel
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Uses same client helpers, independently testable
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Shares ReportingBalance endpoint, independently testable
- **User Story 5 (P3)**: Can start after Foundational (Phase 2) - Uses different endpoints, independently testable
- **User Story 6 (P2)**: Can start after Foundational (Phase 2) - Uses TransactionLines endpoint, independently testable

### Within Each User Story

- Helper functions in client.py before MCP tool in server.py
- Core implementation before validation/error handling
- Story complete before moving to next priority

### Parallel Opportunities

- T002 can run in parallel with T003-T009 (different files)
- T003-T008 can all run in parallel (models in same file but independent dataclasses)
- All Polish phase tasks marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members after Phase 2

---

## Parallel Example: Phase 2 Models

```bash
# Launch all model tasks together:
Task: "Add ProfitLossOverview dataclass to src/exactonline_mcp/models.py"
Task: "Add GLAccountBalance dataclass to src/exactonline_mcp/models.py"
Task: "Add BalanceSheetCategory dataclass to src/exactonline_mcp/models.py"
Task: "Add BalanceSheetSummary dataclass to src/exactonline_mcp/models.py"
Task: "Add AgingEntry dataclass to src/exactonline_mcp/models.py"
Task: "Add TransactionLine dataclass to src/exactonline_mcp/models.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify existing)
2. Complete Phase 2: Foundational (models + mapping)
3. Complete Phase 3: User Story 1 (get_profit_loss_overview)
4. **STOP and VALIDATE**: Test with real Exact Online data
5. Deploy/demo if ready - this alone provides significant value

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test → Deploy (MVP! P&L overview)
3. Add User Story 2 → Test → Deploy (Account balances)
4. Add User Story 3-4 → Test → Deploy (Balance sheet + listing)
5. Add User Story 5 → Test → Deploy (Aging reports)
6. Add User Story 6 → Test → Deploy (Transaction drill-down)

### Sequential Execution (Recommended)

For single developer:
1. Phase 1-2: Setup and Foundational (T001-T009)
2. Phase 3: User Story 1 - P&L Overview (T010-T013)
3. **Validate MVP** - test get_profit_loss_overview with real data
4. Phase 4: User Story 2 - Account Balance (T014-T018)
5. Phase 5: User Story 3 - Balance Sheet (T019-T022)
6. Phase 6: User Story 4 - List Accounts (T023-T026)
7. Phase 7: User Story 5 - Aging Reports (T027-T032)
8. Phase 8: User Story 6 - Transactions (T033-T039)
9. Phase 9: Polish (T040-T044)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All tools use existing ExactOnlineClient rate limiting and retry logic
- Use existing pagination helpers from client.py where applicable
