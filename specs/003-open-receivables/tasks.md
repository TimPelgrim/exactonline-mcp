# Tasks: Open Receivables Tool

**Input**: Design documents from `/specs/003-open-receivables/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not explicitly requested - excluded from this task list.

**Organization**: Tasks are grouped by user story (FR-1, FR-2, FR-3 from spec.md).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: No setup needed - extending existing MCP server

This feature extends an existing project. No new project initialization required.

**Checkpoint**: Ready for foundational phase

---

## Phase 2: Foundational (Shared Components)

**Purpose**: Core infrastructure shared by ALL user stories - MUST complete before any tool implementation

**⚠️ CRITICAL**: No tool implementation can begin until this phase is complete

- [x] T001 Add `parse_odata_date()` helper function in src/exactonline_mcp/client.py to convert `/Date(ms)/` to ISO format
- [x] T002 Add `OpenReceivable` dataclass in src/exactonline_mcp/models.py per data-model.md specification
- [x] T003 Add `OpenReceivablesSummary` dataclass in src/exactonline_mcp/models.py per data-model.md specification
- [x] T004 Add `fetch_open_receivables()` method in src/exactonline_mcp/client.py with OData filter building for cashflow/Receivables endpoint

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - List Open Receivables (Priority: P1) 🎯 MVP

**Goal**: Users can view all open invoices with optional filtering by customer or overdue status

**Independent Test**: Call `get_open_receivables()` via MCP and verify response contains invoice-level detail with summaries

### Implementation for User Story 1

- [x] T005 [US1] Implement `get_open_receivables` tool in src/exactonline_mcp/server.py with parameters: division, top, account_code, overdue_only
- [x] T006 [US1] Add parameter validation for top (1-1000) in get_open_receivables tool
- [x] T007 [US1] Add response building logic: calculate days_overdue, totals, and format items per contracts/mcp-tools.md

**Checkpoint**: User Story 1 complete - can list all open receivables with filtering

---

## Phase 4: User Story 2 - Customer Open Items (Priority: P2)

**Goal**: Users can view all open items for a specific customer with summary

**Independent Test**: Call `get_customer_open_items(account_code="400")` and verify customer-specific response

### Implementation for User Story 2

- [x] T008 [US2] Implement `get_customer_open_items` tool in src/exactonline_mcp/server.py with parameters: division, account_code (required)
- [x] T009 [US2] Add required parameter validation for account_code
- [x] T010 [US2] Add customer details (account_code, account_name) to response structure per contracts/mcp-tools.md

**Checkpoint**: User Story 2 complete - can view customer-specific open items

---

## Phase 5: User Story 3 - Overdue Receivables (Priority: P3)

**Goal**: Users can view overdue items sorted by days overdue (most overdue first)

**Independent Test**: Call `get_overdue_receivables()` and verify items are sorted by days_overdue descending

### Implementation for User Story 3

- [x] T011 [US3] Implement `get_overdue_receivables` tool in src/exactonline_mcp/server.py with parameters: division, days_overdue, top
- [x] T012 [US3] Add overdue filtering logic: only items where days_overdue >= min_days_overdue
- [x] T013 [US3] Add sorting by days_overdue descending (most overdue first)
- [x] T014 [US3] Add as_of_date and min_days_overdue to response per contracts/mcp-tools.md

**Checkpoint**: User Story 3 complete - can view overdue receivables sorted by age

---

## Phase 6: Polish & Documentation

**Purpose**: Documentation updates and final validation

- [x] T015 [P] Update README.md with new tools in Available Tools section
- [x] T016 [P] Update CLAUDE.md Recent Changes section with 003-open-receivables feature
- [x] T017 Run manual validation with real Exact Online data per quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: N/A - extending existing project
- **Foundational (Phase 2)**: No dependencies - can start immediately
- **User Stories (Phase 3-5)**: All depend on Foundational phase (T001-T004)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (T001-T004) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational - Reuses same client method as US1
- **User Story 3 (P3)**: Can start after Foundational - Reuses same client method as US1

### Within Foundational Phase

```
T001 (parse_odata_date) → No dependencies
T002 (OpenReceivable) → No dependencies
T003 (OpenReceivablesSummary) → Depends on T002 (uses OpenReceivable)
T004 (fetch_open_receivables) → Depends on T001, T002
```

### Parallel Opportunities

**Foundational Phase**:
- T001 and T002 can run in parallel (different concerns)
- T003 waits for T002
- T004 waits for T001 and T002

**User Stories** (after Foundational complete):
- US1, US2, US3 can all start in parallel (different tool functions)
- Within each story, tasks are sequential

**Polish Phase**:
- T015 and T016 can run in parallel (different files)

---

## Parallel Example: Foundational Phase

```bash
# Launch in parallel:
Task: "Add parse_odata_date() helper in src/exactonline_mcp/client.py"
Task: "Add OpenReceivable dataclass in src/exactonline_mcp/models.py"

# Then sequentially:
Task: "Add OpenReceivablesSummary dataclass" (depends on OpenReceivable)
Task: "Add fetch_open_receivables() method" (depends on parse_odata_date, OpenReceivable)
```

## Parallel Example: User Stories

```bash
# After Foundational complete, launch all stories in parallel:
Task: "Implement get_open_receivables tool" (US1)
Task: "Implement get_customer_open_items tool" (US2)
Task: "Implement get_overdue_receivables tool" (US3)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 2: Foundational (T001-T004)
2. Complete Phase 3: User Story 1 (T005-T007)
3. **STOP and VALIDATE**: Test `get_open_receivables` with real data
4. Deploy/demo if ready

### Incremental Delivery

1. Complete Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy (MVP!)
3. Add User Story 2 → Test independently → Deploy
4. Add User Story 3 → Test independently → Deploy
5. Polish phase → Final documentation

### Estimated Task Breakdown

| Phase | Tasks | Description |
|-------|-------|-------------|
| Foundational | 4 | Shared models and client method |
| US1 | 3 | get_open_receivables tool |
| US2 | 3 | get_customer_open_items tool |
| US3 | 4 | get_overdue_receivables tool |
| Polish | 3 | Documentation updates |
| **Total** | **17** | |

---

## Notes

- All tools reuse the same `fetch_open_receivables()` client method with different filters
- Date parsing utility (`parse_odata_date`) is shared infrastructure
- Response formatting follows existing patterns in server.py
- No new dependencies required - uses existing httpx/mcp
- OData input sanitization via existing `sanitize_odata_string()` function
