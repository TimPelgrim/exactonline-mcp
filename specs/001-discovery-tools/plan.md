# Implementation Plan: Discovery Tools

**Branch**: `001-discovery-tools` | **Date**: 2025-12-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-discovery-tools/spec.md`

## Summary

Build the foundational MCP server with OAuth2 authentication and three discovery
tools (`list_divisions`, `explore_endpoint`, `list_endpoints`) to explore the
Exact Online API before building specific business tools. This establishes the
core infrastructure for all future Exact Online integrations.

## Technical Context

**Language/Version**: Python 3.11+ (per constitution)
**Primary Dependencies**: mcp (Anthropic SDK), httpx, python-dotenv, keyring
**Storage**: Keyring (system) or encrypted JSON file for OAuth tokens
**Testing**: pytest with real Exact Online data (per Definition of Done)
**Target Platform**: macOS/Linux/Windows CLI (MCP server)
**Project Type**: Single project (MCP server package)
**Performance Goals**: API responses within 5 seconds, 60 calls/minute rate limit
**Constraints**: Read-only access, no token logging, encrypted storage
**Scale/Scope**: Single-tenant (YipYip internal), ~10-20 API endpoints initially

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Status |
|-----------|-------------|--------|
| I. Read-Only | Only GET requests to Exact Online API | ✅ PASS - All tools are read-only |
| II. Security First | Tokens encrypted, never logged | ✅ PASS - Using keyring/encrypted JSON |
| III. Discovery-Driven | Prefix discovery tools with `explore_`/`list_` | ✅ PASS - Tool names comply |
| IV. Fail Gracefully | Retry with backoff, clear error messages | ✅ PASS - Spec requires this |
| Tech Stack | Python 3.11+, uv, mcp, httpx, keyring | ✅ PASS - All specified |
| Code Conventions | Type hints, docstrings, async I/O | ✅ PASS - Will implement |
| MCP Tool Design | Return structured data, sensible defaults | ✅ PASS - Spec requires dicts/lists |

**Gate Result**: PASS - No violations. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-discovery-tools/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (MCP tool schemas)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
└── exactonline_mcp/
    ├── __init__.py
    ├── __main__.py      # Entry point for `python -m exactonline_mcp`
    ├── server.py        # MCP server with tool definitions
    ├── auth.py          # OAuth2 flow and token management
    ├── client.py        # Exact Online API client (httpx)
    ├── models.py        # Data models (Division, Token, etc.)
    ├── endpoints.py     # Known endpoint catalog
    └── exceptions.py    # Custom exceptions

tests/
├── conftest.py          # Shared fixtures
├── test_auth.py         # OAuth flow tests
├── test_client.py       # API client tests
└── test_tools.py        # MCP tool integration tests

pyproject.toml           # uv project configuration
README.md                # Project documentation
.env.example             # Environment variable template
```

**Structure Decision**: Single project layout with `src/exactonline_mcp/` package.
This is an MCP server, not a web application, so the simple structure applies.
Tests are at the root level for easy discovery by pytest.

## Complexity Tracking

> No violations to justify - design is minimal and follows constitution.
