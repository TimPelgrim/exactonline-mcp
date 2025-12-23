# Tasks: Revenue Tools

**Input**: Design documents from `/specs/002-revenue-tools/`
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

**Purpose**: No new project initialization needed - extends existing project

- [x] T001 Verify existing project structure and dependencies in pyproject.toml
- [x] T002 [P] Add revenue tools to endpoints.py catalog in src/exactonline_mcp/endpoints.py

---

## Phase 2: Foundational (Shared Infrastructure)

**Purpose**: Core infrastructure that all three revenue tools depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Add RevenuePeriod dataclass to src/exactonline_mcp/models.py
- [x] T004 [P] Add CustomerRevenue dataclass to src/exactonline_mcp/models.py
- [x] T005 [P] Add ProjectRevenue dataclass to src/exactonline_mcp/models.py
- [x] T006 Add helper function for fetching paginated SalesInvoices in src/exactonline_mcp/client.py
- [x] T007 Add helper function for date range filtering in src/exactonline_mcp/client.py
- [x] T008 Add helper function for period grouping (month/quarter/year) in src/exactonline_mcp/client.py

**Checkpoint**: Foundation ready - revenue tool implementation can now begin

---

## Phase 3: User Story 1 - View Revenue by Time Period (Priority: P1) 🎯 MVP

**Goal**: Business owners can see revenue broken down by month, quarter, or year with year-over-year comparison

**Independent Test**: Call `get_revenue_by_period` with start_date="2024-01-01", end_date="2024-12-31", group_by="quarter". Verify 4 quarters returned with revenue totals and YoY change percentages.

### Implementation for User Story 1

- [x] T009 [US1] Implement `_fetch_invoices_for_period` helper to query SalesInvoices with Status=50 filter in src/exactonline_mcp/client.py
- [x] T010 [US1] Implement `_group_invoices_by_period` helper for month/quarter/year grouping in src/exactonline_mcp/client.py
- [x] T011 [US1] Implement `_calculate_yoy_comparison` helper to compute same-period-last-year percentages in src/exactonline_mcp/client.py
- [x] T012 [US1] Implement `get_revenue_by_period` MCP tool in src/exactonline_mcp/server.py
- [x] T013 [US1] Add input validation for date range (start_date < end_date) in src/exactonline_mcp/server.py
- [x] T014 [US1] Handle empty result sets gracefully (return zero values) in src/exactonline_mcp/server.py

**Checkpoint**: User Story 1 fully functional - can query revenue by period with YoY comparison

---

## Phase 4: User Story 2 - View Revenue by Customer (Priority: P2)

**Goal**: Sales managers can see top customers ranked by revenue with metrics

**Independent Test**: Call `get_revenue_by_customer` with top=5. Verify 5 customers returned sorted by revenue descending with name, revenue, invoice count, and percentage of total.

### Implementation for User Story 2

- [x] T015 [US2] Implement `_aggregate_by_customer` helper to group invoices by InvoiceTo in src/exactonline_mcp/client.py
- [x] T016 [US2] Implement `_calculate_customer_percentages` helper for percentage of total in src/exactonline_mcp/client.py
- [x] T017 [US2] Implement `get_revenue_by_customer` MCP tool in src/exactonline_mcp/server.py
- [x] T018 [US2] Add top parameter validation (1-100 range, default 10) in src/exactonline_mcp/server.py
- [x] T019 [US2] Handle empty result sets gracefully (return empty customers list) in src/exactonline_mcp/server.py

**Checkpoint**: User Story 2 fully functional - can query top customers by revenue

---

## Phase 5: User Story 3 - View Revenue by Project (Priority: P3)

**Goal**: Project managers can see project-based revenue with logged hours

**Independent Test**: Call `get_revenue_by_project`. Verify projects returned with client, revenue, invoice count, and hours (if available).

### Implementation for User Story 3

- [x] T020 [US3] Implement `_fetch_invoice_lines_with_projects` helper to query SalesInvoiceLines with Project ne null in src/exactonline_mcp/client.py
- [x] T021 [US3] Implement `_fetch_project_metadata` helper to get project details from project/Projects in src/exactonline_mcp/client.py
- [x] T022 [US3] Implement `_fetch_time_transactions` helper to get hours from project/TimeTransactions in src/exactonline_mcp/client.py
- [x] T023 [US3] Implement `_aggregate_by_project` helper to combine revenue and hours data in src/exactonline_mcp/client.py
- [x] T024 [US3] Implement `get_revenue_by_project` MCP tool in src/exactonline_mcp/server.py
- [x] T025 [US3] Add include_hours parameter support (default true) in src/exactonline_mcp/server.py
- [x] T026 [US3] Handle project module unavailable gracefully (return structured error) in src/exactonline_mcp/server.py

**Checkpoint**: User Story 3 fully functional - can query project-based revenue with hours

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect all tools

- [x] T027 [P] Update README.md with revenue tools documentation
- [x] T028 [P] Run linting (uv run ruff check .) and fix any issues
- [x] T029 Validate all three tools with real Exact Online data
- [x] T030 Run quickstart.md validation scenarios
- [x] T031 Update endpoints.py with salesinvoice/SalesInvoices, project/Projects, project/TimeTransactions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - verify existing structure
- **Foundational (Phase 2)**: Depends on Setup - adds shared models and helpers
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can proceed sequentially in priority order (P1 → P2 → P3)
  - Or in parallel if desired (all depend only on Phase 2, not on each other)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Shares invoice fetching with US1 but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Uses different endpoints, independently testable

### Within Each User Story

- Helper functions in client.py before MCP tool in server.py
- Core implementation before validation/error handling
- Story complete before moving to next priority

### Parallel Opportunities

- T002 can run in parallel with T003-T005 (different files)
- T003, T004, T005 can all run in parallel (models in same file but independent dataclasses)
- All Polish phase tasks marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members after Phase 2

---

## Parallel Example: Phase 2 Models

```bash
# Launch all model tasks together:
Task: "Add RevenuePeriod dataclass to src/exactonline_mcp/models.py"
Task: "Add CustomerRevenue dataclass to src/exactonline_mcp/models.py"
Task: "Add ProjectRevenue dataclass to src/exactonline_mcp/models.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify existing)
2. Complete Phase 2: Foundational (models + helpers)
3. Complete Phase 3: User Story 1 (get_revenue_by_period)
4. **STOP and VALIDATE**: Test with real Exact Online data
5. Deploy/demo if ready - this alone provides significant value

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test → Deploy (MVP! Core revenue tracking)
3. Add User Story 2 → Test → Deploy (Customer insights)
4. Add User Story 3 → Test → Deploy (Project profitability)
5. Each story adds value without breaking previous stories

### Sequential Execution (Recommended)

For single developer:
1. Phase 1-2: Setup and Foundational (T001-T008)
2. Phase 3: User Story 1 - Period Revenue (T009-T014)
3. **Validate MVP** - test get_revenue_by_period with real data
4. Phase 4: User Story 2 - Customer Revenue (T015-T019)
5. Phase 5: User Story 3 - Project Revenue (T020-T026)
6. Phase 6: Polish (T027-T031)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All tools use existing ExactOnlineClient rate limiting and retry logic
- Filter invoices by Status=50 for processed/finalized only
- Credit notes have negative AmountDC - include in sums to reduce totals
- Year-over-year comparison uses same calendar period previous year
