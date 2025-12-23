# Implementation Plan: Balance Sheet & Financial Reporting Tools

**Branch**: `001-balance-sheet-financial` | **Date**: 2025-12-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-balance-sheet-financial/spec.md`

## Summary

Add MCP tools for accessing balance sheet data, profit/loss overview, and general ledger account balances from Exact Online. This extends the existing exactonline-mcp server with financial reporting capabilities using discovered API endpoints (`read/financial/ProfitLossOverview`, `financial/ReportingBalance`, `read/financial/AgingReceivablesList`, `read/financial/AgingPayablesList`).

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: mcp (Anthropic SDK), httpx, python-dotenv, keyring
**Storage**: N/A (read-only from Exact Online API)
**Testing**: Manual validation with real Exact Online data (per constitution)
**Target Platform**: CLI/MCP server (stdio transport)
**Project Type**: Single project (extends existing exactonline-mcp)
**Performance Goals**: Response within rate limit (60 calls/min), pagination for large datasets
**Constraints**: Read-only, max 1000 records per API call, respect rate limits
**Scale/Scope**: Single-tenant (YipYip internal use)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Read-Only by Design | PASS | All tools use GET requests only (ProfitLossOverview, ReportingBalance, AgingLists) |
| II. Security First | PASS | No new credential handling; uses existing OAuth flow |
| III. Discovery-Driven Development | PASS | Based on API exploration done prior to spec |
| IV. Fail Gracefully | PASS | Will implement error handling for missing accounts/periods |
| Tech Stack | PASS | Python 3.11+, uv, mcp, httpx - all per constitution |
| Code Conventions | PASS | Type hints, Google docstrings, async/await required |
| MCP Tool Design | PASS | Returns structured dicts, pagination built-in |

**Gate Status**: PASS - No violations. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-balance-sheet-financial/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/exactonline_mcp/
├── __init__.py
├── __main__.py          # Entry point
├── server.py            # MCP server + tools (add new tools here)
├── auth.py              # OAuth2 flow (unchanged)
├── client.py            # API client (add helper functions)
├── models.py            # Data models (add new dataclasses)
├── endpoints.py         # Endpoint catalog (add financial endpoints)
└── exceptions.py        # Custom exceptions (unchanged)

tests/
└── (manual validation with real data per constitution)
```

**Structure Decision**: Single project extending existing codebase. New tools added to server.py, new models to models.py, new helpers to client.py.

## Complexity Tracking

> No violations to justify - design follows constitution.

## API Endpoints (from exploration)

| Endpoint | Purpose | Key Fields |
|----------|---------|------------|
| `read/financial/ProfitLossOverview` | P&L summary | RevenueCurrentYear, CostsCurrentYear, ResultCurrentYear, *PreviousYear variants |
| `financial/ReportingBalance` | GL account balances | GLAccountCode, Amount, AmountDebit, AmountCredit, ReportingYear, ReportingPeriod, BalanceType |
| `financial/GLAccounts` | Chart of accounts | Code, Description, Type, TypeDescription, BalanceType, BalanceSide |
| `read/financial/AgingReceivablesList` | Outstanding receivables | AccountName, TotalAmount, AgeGroup1-4 amounts |
| `read/financial/AgingPayablesList` | Outstanding payables | AccountName, TotalAmount, AgeGroup1-4 amounts |
| `financial/FinancialPeriods` | Period definitions | FinYear, FinPeriod, StartDate, EndDate |
| `financialtransaction/TransactionLines` | Individual transactions | Date, GLAccountCode, Description, AmountDC, EntryNumber, JournalCode |
