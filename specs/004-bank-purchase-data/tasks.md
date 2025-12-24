# Tasks: Bank & Purchase Data Tools

**Input**: Design documents from `/specs/004-bank-purchase-data/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/mcp-tools.md, quickstart.md

**Tests**: Not explicitly requested - tests are optional for this feature.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/exactonline_mcp/`, `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No setup needed - extending existing MCP server infrastructure

*All infrastructure already exists. Proceed directly to Phase 2.*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure shared by both user stories

**Note**: Both tools share the same dataclasses and client patterns. Models must be added before any tool implementation.

- [x] T001 [P] Add BankTransaction dataclass to src/exactonline_mcp/models.py per data-model.md
- [x] T002 [P] Add PurchaseInvoice dataclass to src/exactonline_mcp/models.py per data-model.md

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - View Bank Transactions (Priority: P1)

**Goal**: Enable users to view individual bank transaction lines with filtering by date range and GL account code

**Independent Test**: Call `get_bank_transactions` via MCP and verify response contains individual transaction lines with dates, amounts, and descriptions

### Implementation for User Story 1

- [x] T003 [US1] Add fetch_bank_transactions() method to src/exactonline_mcp/client.py per quickstart.md
- [x] T004 [US1] Add get_bank_transactions tool to src/exactonline_mcp/server.py per contracts/mcp-tools.md
- [x] T005 [US1] Test get_bank_transactions manually with MCP inspector or Claude

**Checkpoint**: User Story 1 complete - bank transactions are accessible via MCP

---

## Phase 4: User Story 2 - View Purchase Invoices (Priority: P2)

**Goal**: Enable users to view purchase invoices from suppliers with filtering and graceful error handling for module unavailability

**Independent Test**: Call `get_purchase_invoices` via MCP and verify response contains invoice data with supplier, amounts, and dates (or clear error if module unavailable)

### Implementation for User Story 2

- [x] T006 [US2] Add fetch_purchase_invoices() method to src/exactonline_mcp/client.py per quickstart.md
- [x] T007 [US2] Add get_purchase_invoices tool to src/exactonline_mcp/server.py with graceful error handling for MODULE_NOT_AVAILABLE
- [x] T008 [US2] Test get_purchase_invoices manually - verify both success case and module unavailable error message

**Checkpoint**: User Story 2 complete - purchase invoices accessible (or clear error shown)

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Documentation updates and final validation

- [x] T009 [P] Update README.md with new tools in Available Tools section
- [x] T010 [P] Update CLAUDE.md Recent Changes section
- [x] T011 Run quickstart.md validation - verify all example prompts work

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Skipped - existing infrastructure
- **Foundational (Phase 2)**: Add dataclasses - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on T001 (BankTransaction model)
- **User Story 2 (Phase 4)**: Depends on T002 (PurchaseInvoice model)
- **Polish (Phase 5)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after T001 - No dependencies on other stories
- **User Story 2 (P2)**: Can start after T002 - No dependencies on other stories
- **Both stories can run in parallel** after Foundational phase

### Within Each User Story

- Client method before server tool
- Server tool before manual testing
- Core implementation before documentation

### Parallel Opportunities

- T001 and T002 can run in parallel (different dataclasses in same file)
- User Story 1 and User Story 2 can run in parallel after Foundational
- T009 and T010 can run in parallel (different files)

---

## Parallel Example: Foundational Phase

```bash
# Launch both model tasks together:
Task: "Add BankTransaction dataclass to src/exactonline_mcp/models.py"
Task: "Add PurchaseInvoice dataclass to src/exactonline_mcp/models.py"
```

## Parallel Example: User Stories

```bash
# After Foundational, launch both stories in parallel:
# Developer A: User Story 1 (T003-T005)
# Developer B: User Story 2 (T006-T008)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 2: Foundational (T001-T002)
2. Complete Phase 3: User Story 1 (T003-T005)
3. **STOP and VALIDATE**: Test bank transactions via MCP
4. Deploy/demo if ready

### Incremental Delivery

1. Add models (T001-T002) → Foundation ready
2. Add US1: Bank Transactions → Test → Deploy (MVP!)
3. Add US2: Purchase Invoices → Test → Deploy
4. Polish: Update docs (T009-T011)

### Single Developer Strategy

Execute in task order: T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- BankEntryLines endpoint confirmed working
- PurchaseInvoices endpoint may require Purchase module - handle gracefully
- No tests explicitly requested - manual testing via MCP inspector
- Commit after each task or logical group
