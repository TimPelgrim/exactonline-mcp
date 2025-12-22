# Tasks: Discovery Tools

**Input**: Design documents from `/specs/001-discovery-tools/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation
and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/exactonline_mcp/` at repository root
- **Tests**: `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project directory structure per plan.md in src/exactonline_mcp/
- [x] T002 Initialize uv project with pyproject.toml (Python 3.11+, mcp, httpx, python-dotenv, keyring dependencies)
- [x] T003 [P] Create .env.example with EXACT_ONLINE_CLIENT_ID, EXACT_ONLINE_CLIENT_SECRET, EXACT_ONLINE_REGION placeholders
- [x] T004 [P] Configure ruff for linting in pyproject.toml
- [x] T005 Create src/exactonline_mcp/__init__.py with package version

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Data Models (shared across stories)

- [x] T006 [P] Create Division dataclass in src/exactonline_mcp/models.py (code: int, name: str, is_current: bool)
- [x] T007 [P] Create Token dataclass in src/exactonline_mcp/models.py (access_token, refresh_token, obtained_at, expires_in)
- [x] T008 [P] Create Endpoint dataclass in src/exactonline_mcp/models.py (path, category, description, typical_use)
- [x] T009 [P] Create ExplorationResult dataclass in src/exactonline_mcp/models.py (endpoint, division, count, data, available_fields)

### Exception Hierarchy

- [x] T010 Create custom exceptions in src/exactonline_mcp/exceptions.py (ExactOnlineError, AuthenticationError, RateLimitError, DivisionNotAccessibleError)

### OAuth2 Authentication (US0 - P0 Prerequisite)

- [x] T011 Implement TokenStorage abstract base class in src/exactonline_mcp/auth.py
- [x] T012 Implement KeyringStorage class in src/exactonline_mcp/auth.py (system keyring)
- [x] T013 Implement EncryptedFileStorage class in src/exactonline_mcp/auth.py (fallback)
- [x] T014 Implement OAuth2 authorization URL generation in src/exactonline_mcp/auth.py
- [x] T015 Implement OAuth2 token exchange (code → tokens) in src/exactonline_mcp/auth.py
- [x] T016 Implement token refresh logic in src/exactonline_mcp/auth.py (pre-emptive at 9.5 min)
- [x] T017 Implement auth CLI command in src/exactonline_mcp/auth.py (browser open, callback server)

### API Client

- [x] T018 Implement ExactOnlineClient class in src/exactonline_mcp/client.py (httpx.AsyncClient)
- [x] T019 Add rate limiting logic to client (60 calls/min tracking) in src/exactonline_mcp/client.py
- [x] T020 Add retry logic with exponential backoff for 429 responses in src/exactonline_mcp/client.py
- [x] T021 Add automatic token refresh before requests in src/exactonline_mcp/client.py
- [x] T022 Add 30-second timeout configuration in src/exactonline_mcp/client.py

### MCP Server Shell

- [x] T023 Create FastMCP server instance in src/exactonline_mcp/server.py
- [x] T024 Create __main__.py entry point in src/exactonline_mcp/__main__.py (mcp.run with stdio transport)

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - View Available Divisions (Priority: P1) 🎯 MVP

**Goal**: Users can see all accessible Exact Online divisions with code, name, and
current status to know which division ID to use for queries.

**Independent Test**: Request division list, verify at least one division returned
with code (int), name (str), and is_current (bool).

### Implementation for User Story 1

- [x] T025 [US1] Implement get_divisions method in ExactOnlineClient in src/exactonline_mcp/client.py
- [x] T026 [US1] Implement get_current_division method in ExactOnlineClient in src/exactonline_mcp/client.py
- [x] T027 [US1] Implement list_divisions MCP tool in src/exactonline_mcp/server.py
- [x] T028 [US1] Add error handling for auth failures in list_divisions tool in src/exactonline_mcp/server.py

**Checkpoint**: list_divisions tool functional - can validate auth and see divisions

---

## Phase 4: User Story 2 - Explore Endpoint Data (Priority: P2)

**Goal**: Users can retrieve sample data from any Exact Online API endpoint to
understand data structure and available fields.

**Independent Test**: Request sample data from crm/Accounts endpoint, verify
structured response with count, data array, and available_fields list.

### Implementation for User Story 2

- [x] T029 [US2] Implement generic get method in ExactOnlineClient in src/exactonline_mcp/client.py (division, endpoint, OData params)
- [x] T030 [US2] Add OData parameter building ($select, $filter, $top) in src/exactonline_mcp/client.py
- [x] T031 [US2] Implement explore_endpoint MCP tool in src/exactonline_mcp/server.py
- [x] T032 [US2] Add parameter validation (top max 25, endpoint format) in src/exactonline_mcp/server.py
- [x] T033 [US2] Add field extraction from response in src/exactonline_mcp/server.py
- [x] T034 [US2] Add default division fallback logic in src/exactonline_mcp/server.py

**Checkpoint**: explore_endpoint tool functional - can explore any API endpoint

---

## Phase 5: User Story 3 - Browse Known Endpoints (Priority: P3)

**Goal**: Users can see a curated list of known Exact Online endpoints grouped by
category for discoverability.

**Independent Test**: Request endpoint list, verify categories (crm, sales,
financial, project, logistics) with endpoint details.

### Implementation for User Story 3

- [x] T035 [P] [US3] Create endpoint catalog in src/exactonline_mcp/endpoints.py (KNOWN_ENDPOINTS dict)
- [x] T036 [US3] Implement list_endpoints MCP tool in src/exactonline_mcp/server.py
- [x] T037 [US3] Add category filter support in list_endpoints tool in src/exactonline_mcp/server.py

**Checkpoint**: All three discovery tools functional and testable

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, cleanup, and validation

- [x] T038 [P] Create README.md with installation, setup, and usage instructions
- [x] T039 [P] Update CLAUDE.md if needed with any discovered patterns
- [x] T040 Validate quickstart.md flow works end-to-end
- [x] T041 Test with real Exact Online credentials (per Definition of Done)
- [x] T042 Verify no tokens appear in logs or error messages

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - US1 (P1): First priority, validates auth works
  - US2 (P2): Depends on US1 (needs working auth + division fetching)
  - US3 (P3): Independent of US1/US2 (static data)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational - No dependencies on other stories
- **US2 (P2)**: Can start after Foundational - Uses client from US1 but independent
- **US3 (P3)**: Can start after Foundational - Fully independent (no API calls)

### Within Each User Story

- Client methods before MCP tools
- Core implementation before validation/error handling

### Parallel Opportunities

**Phase 1 (Setup):**
```bash
# T003 and T004 can run in parallel:
Task: "Create .env.example"
Task: "Configure ruff for linting"
```

**Phase 2 (Foundational):**
```bash
# T006-T009 can all run in parallel (different dataclasses):
Task: "Create Division dataclass"
Task: "Create Token dataclass"
Task: "Create Endpoint dataclass"
Task: "Create ExplorationResult dataclass"
```

**Phase 5 (US3):**
```bash
# T035 can run in parallel with T036:
Task: "Create endpoint catalog"
Task: "Implement list_endpoints MCP tool"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (list_divisions)
4. **STOP and VALIDATE**: Test with real Exact Online account
5. Demo: "Show me my divisions" works in Claude

### Incremental Delivery

1. Setup + Foundational → Auth working, client ready
2. Add US1 (list_divisions) → Test → Demo MVP
3. Add US2 (explore_endpoint) → Test → Explore any endpoint
4. Add US3 (list_endpoints) → Test → Full discovery capability
5. Polish → README, validation → Production ready

### Suggested Implementation Order

For single developer, execute phases sequentially:
1. T001-T005 (Setup)
2. T006-T024 (Foundational - this is the bulk of work)
3. T025-T028 (US1 - validates everything works)
4. T029-T034 (US2 - core discovery)
5. T035-T037 (US3 - quick win)
6. T038-T042 (Polish)

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate
- Definition of Done requires testing with real Exact Online data (T041)
