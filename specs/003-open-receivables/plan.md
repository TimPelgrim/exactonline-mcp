# Implementation Plan: Open Receivables Tool

**Branch**: `003-open-receivables` | **Date**: 2025-12-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-open-receivables/spec.md`

## Summary

Add 3 MCP tools for accessing detailed open receivables from Exact Online via the `cashflow/Receivables` endpoint. This provides invoice-level detail (individual invoices, due dates, amounts) that complements the existing aging report which only shows bucketed totals per customer.

**Tools to implement**:
1. `get_open_receivables` - List all open invoices with filtering
2. `get_customer_open_items` - Open items for a specific customer
3. `get_overdue_receivables` - Overdue items sorted by days overdue

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: mcp (Anthropic SDK), httpx, python-dotenv, keyring
**Storage**: N/A (read-only from Exact Online API)
**Testing**: pytest with real Exact Online data
**Target Platform**: MCP server (stdio transport)
**Project Type**: Single project (existing MCP server extension)
**Performance Goals**: N/A (follows existing patterns)
**Constraints**: Read-only, 60 calls/min rate limit, max 1000 records/call
**Scale/Scope**: YipYip internal use

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Read-Only by Design | ✅ PASS | Only GET requests to cashflow/Receivables |
| II. Security First | ✅ PASS | No credential logging, uses existing auth |
| III. Discovery-Driven | ✅ PASS | Endpoint already discovered and documented |
| IV. Fail Gracefully | ✅ PASS | Uses existing error handling patterns |

**Code Conventions**:
- ✅ Type hints on all functions
- ✅ Google-style docstrings
- ✅ Async/await for I/O
- ✅ Specific exception handling

**API Constraints**:
- ✅ Division explicit in all tools
- ✅ Pagination built-in (top parameter, max 1000)
- ✅ Returns structured data (dicts/lists)

## Project Structure

### Documentation (this feature)

```text
specs/003-open-receivables/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # API endpoint research
├── data-model.md        # OpenReceivable dataclass
├── quickstart.md        # Implementation guide
├── contracts/
│   └── mcp-tools.md     # Tool parameter/response contracts
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
src/exactonline_mcp/
├── models.py            # Add OpenReceivable dataclass
├── client.py            # Add fetch_open_receivables() method
└── server.py            # Add 3 new tool definitions

tests/
└── test_receivables.py  # New test file (optional)
```

**Structure Decision**: Extend existing single-project structure. No new directories needed - just add to existing modules following established patterns.

## Complexity Tracking

No violations - this feature follows all constitution guidelines.

## Phase 0 Outputs

- ✅ `research.md` - Endpoint discovery, field mapping, design decisions

## Phase 1 Outputs

- ✅ `data-model.md` - OpenReceivable and OpenReceivablesSummary dataclasses
- ✅ `contracts/mcp-tools.md` - Tool parameters, responses, errors
- ✅ `quickstart.md` - Implementation guide

## Next Steps

Run `/speckit.tasks` to generate the implementation task list.
