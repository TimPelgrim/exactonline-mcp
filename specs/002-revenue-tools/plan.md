# Implementation Plan: Revenue Tools

**Branch**: `002-revenue-tools` | **Date**: 2025-12-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-revenue-tools/spec.md`

## Summary

Implement three MCP tools for analyzing revenue data from Exact Online: revenue by period (with year-over-year comparison), revenue by customer (with rankings), and revenue by project (with hours tracking). Tools build on existing ExactOnlineClient infrastructure and follow established patterns from discovery tools.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: mcp (Anthropic SDK), httpx, python-dotenv, keyring
**Storage**: Keyring or encrypted JSON for OAuth tokens (existing)
**Testing**: pytest with real Exact Online data
**Target Platform**: MCP server (stdio transport for Claude Desktop)
**Project Type**: single
**Performance Goals**: Under 5 seconds per tool call (per SC-001)
**Constraints**: Rate limit 60 calls/minute, max 1000 records per API call
**Scale/Scope**: Single-tenant (YipYip internal use)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Read-Only by Design | ✅ PASS | All tools perform GET requests only |
| II. Security First | ✅ PASS | Uses existing OAuth infrastructure, no new credential handling |
| III. Discovery-Driven | ✅ PASS | Built after exploring SalesInvoices endpoint |
| IV. Fail Gracefully | ✅ PASS | Leverages existing retry/rate limit logic |

**Tech Stack Compliance**:
- Python 3.11+ ✅
- uv package manager ✅
- mcp (Anthropic) SDK ✅
- httpx async client ✅

**Code Conventions**:
- Type hints: Required on all functions ✅
- Docstrings: Google style ✅
- Async/await: All I/O operations ✅
- Naming: snake_case (`get_revenue_by_period`) ✅

## Project Structure

### Documentation (this feature)

```text
specs/002-revenue-tools/
├── plan.md              # This file
├── research.md          # Phase 0 output - API endpoint analysis
├── data-model.md        # Phase 1 output - Revenue entity definitions
├── quickstart.md        # Phase 1 output - Usage guide
├── contracts/           # Phase 1 output - MCP tool schemas
│   └── mcp-tools.json
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/exactonline_mcp/
├── __init__.py          # Package exports
├── __main__.py          # Entry point (existing)
├── auth.py              # OAuth2 client (existing)
├── client.py            # ExactOnlineClient (existing, may extend)
├── endpoints.py         # Known endpoints catalog (existing)
├── exceptions.py        # Custom exceptions (existing)
├── models.py            # Data models (extend with revenue entities)
└── server.py            # MCP tools (add 3 new tools)

tests/
├── conftest.py          # Shared fixtures
├── test_revenue.py      # Revenue tool tests
└── integration/
    └── test_revenue_integration.py  # Live API tests
```

**Structure Decision**: Extends existing single-project structure. New revenue tools added to `server.py`, new data models added to `models.py`. No new files needed except tests.

## Complexity Tracking

> No violations detected. Implementation follows existing patterns.

| Aspect | Assessment |
|--------|------------|
| New dependencies | None - uses existing stack |
| New patterns | None - follows existing tool patterns |
| External APIs | Same Exact Online endpoints, different filters |

## Phase 0: Research

### API Endpoints to Investigate

1. **salesinvoice/SalesInvoices** - Primary revenue source
   - Fields: AmountFC, InvoiceDate, InvoiceTo (customer), Project
   - Filter: Status for finalized invoices only
   - Verify: Credit notes have negative amounts

2. **crm/Accounts** - Customer names for revenue by customer
   - Fields: ID, Name
   - Join: Via InvoiceTo field on invoices

3. **project/Projects** - Project details for revenue by project
   - Fields: ID, Code, Description, Account (client)
   - Join: Via Project field on invoices

4. **project/TimeTransactions** - Hours tracking (if available)
   - Fields: Hours, Project
   - Aggregation: Sum hours per project

### Research Deliverables

- [ ] Document SalesInvoices fields and filter syntax
- [ ] Verify finalized invoice status values
- [ ] Test credit note representation
- [ ] Confirm customer/project joins work
- [ ] Check TimeTransactions availability and fields

## Phase 1: Design

### Data Models (to add in models.py)

1. **RevenuePeriod**: period_key, start_date, end_date, revenue, previous_revenue, change_percentage
2. **CustomerRevenue**: customer_id, customer_name, revenue, invoice_count, percentage_of_total
3. **ProjectRevenue**: project_id, project_name, client_name, revenue, hours

### MCP Tool Signatures

```python
@mcp.tool()
async def get_revenue_by_period(
    start_date: str,
    end_date: str,
    group_by: str = "month",  # month | quarter | year
    division: int | None = None,
) -> dict[str, Any]:
    """Revenue totals grouped by time period with year-over-year comparison."""

@mcp.tool()
async def get_revenue_by_customer(
    division: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    top: int = 10,
) -> dict[str, Any]:
    """Customer revenue rankings with metrics."""

@mcp.tool()
async def get_revenue_by_project(
    division: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """Project revenue with optional hours tracking."""
```

### Implementation Notes

- Invoice amounts in base currency (AmountFC field)
- Filter finalized invoices: need to determine Status field values
- Year-over-year: same period last year (e.g., Q1 2024 vs Q1 2023)
- Credit notes: negative AmountFC reduces revenue total
- Pagination: use `$skip` and `$top` for large datasets
