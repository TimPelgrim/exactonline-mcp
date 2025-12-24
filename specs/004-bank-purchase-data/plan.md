# Implementation Plan: Bank & Purchase Data Tools

**Branch**: `004-bank-purchase-data` | **Date**: 2025-12-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-bank-purchase-data/spec.md`

## Summary

Add 2 MCP tools for exposing bank transaction lines and purchase invoice data from Exact Online. Following the "data exposure only" principle - no pre-computed analysis, raw data for Claude to analyze downstream.

**Tools to implement**:
1. `get_bank_transactions` - Bank entry lines from `financialtransaction/BankEntryLines`
2. `get_purchase_invoices` - Purchase invoices from `purchase/PurchaseInvoices`

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
| I. Read-Only by Design | ✅ PASS | Only GET requests to BankEntryLines and PurchaseInvoices |
| II. Security First | ✅ PASS | No credential logging, uses existing auth |
| III. Discovery-Driven | ✅ PASS | Endpoints already explored and documented |
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
specs/004-bank-purchase-data/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # API endpoint research
├── data-model.md        # BankTransaction, PurchaseInvoice dataclasses
├── quickstart.md        # Implementation guide
├── contracts/
│   └── mcp-tools.md     # Tool parameter/response contracts
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
src/exactonline_mcp/
├── models.py            # Add BankTransaction, PurchaseInvoice dataclasses
├── client.py            # Add fetch_bank_transactions(), fetch_purchase_invoices() methods
└── server.py            # Add 2 new tool definitions

tests/
└── test_bank_purchase.py  # New test file (optional)
```

**Structure Decision**: Extend existing single-project structure. No new directories needed - just add to existing modules following established patterns.

## Complexity Tracking

No violations - this feature follows all constitution guidelines.

## Phase 0 Outputs

- ✅ `research.md` - Endpoint discovery, field mapping, design decisions

## Phase 1 Outputs

- ✅ `data-model.md` - BankTransaction and PurchaseInvoice dataclasses
- ✅ `contracts/mcp-tools.md` - Tool parameters, responses, errors
- ✅ `quickstart.md` - Implementation guide

## Next Steps

Run `/speckit.tasks` to generate the implementation task list.
