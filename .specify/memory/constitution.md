<!--
  Sync Impact Report
  ==================
  Version change: N/A → 1.0.0 (initial constitution)

  Added sections:
  - Core Principles (4): Read-Only by Design, Security First,
    Discovery-Driven Development, Fail Gracefully
  - Tech Stack
  - Code Conventions (Style, Structure, Naming)
  - API Constraints (Exact Online Specifics, MCP Tool Design)
  - Out of Scope
  - Governance (Definition of Done, Amendment Procedure)

  Removed sections: N/A (initial)
  Modified principles: N/A (initial)

  Templates requiring updates:
  ✅ .specify/templates/plan-template.md - Compatible (generic Constitution Check)
  ✅ .specify/templates/spec-template.md - Compatible (no constitution references)
  ✅ .specify/templates/tasks-template.md - Compatible (no constitution references)
  ✅ .specify/templates/checklist-template.md - Compatible (no constitution references)

  Follow-up TODOs: None
-->

# exactonline-mcp Constitution

Een MCP (Model Context Protocol) server die Claude read-only toegang geeft tot
Exact Online boekhouding data voor YipYip.

## Core Principles

### I. Read-Only by Design

Deze server mag NOOIT data muteren in Exact Online. Alle tools zijn uitsluitend
voor het ophalen en analyseren van data. Dit is een harde vereiste vanwege de
financiële aard van de data.

**Non-negotiable rules:**
- Tools MUST only perform GET requests to Exact Online API
- No POST, PUT, PATCH, or DELETE operations are permitted
- Code reviews MUST verify read-only compliance before merge

### II. Security First

OAuth tokens en credentials worden beschermd volgens strikte beveiligingsregels.

**Non-negotiable rules:**
- OAuth tokens and credentials MUST NEVER be logged or included in responses
- Tokens MUST be stored encrypted, not in plaintext
- `.env` and token files MUST be in `.gitignore`
- Error messages MUST NOT contain sensitive financial data
- Credentials MUST NOT be hardcoded in source files

### III. Discovery-Driven Development

We kennen de exacte data-behoeften nog niet. Het project start met discovery
tools om de Exact Online API te verkennen. Specifieke tools worden pas gebouwd
na begrip van de beschikbare data.

**Guidelines:**
- Start with exploration tools before building specific implementations
- Prefix discovery tools with `explore_` or `list_`
- Document API discoveries before building production tools
- Iterate based on actual data structure findings

### IV. Fail Gracefully

De server moet robuust omgaan met fouten en edge cases.

**Non-negotiable rules:**
- Auth failures MUST produce clear, actionable error messages
- Rate limits MUST be handled with retry and exponential backoff
- Unexpected API responses MUST NOT crash the server
- All I/O operations MUST have proper exception handling

## Tech Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Language | Python 3.11+ | Mature Exact Online libraries available |
| Package Manager | uv | Speed, lockfile support |
| MCP SDK | `mcp` (Anthropic) | Official SDK |
| HTTP Client | `httpx` | Async support, modern API |
| Auth Storage | `keyring` or encrypted JSON | Secure token storage |

These choices are **non-negotiable** without constitution amendment.

## Code Conventions

### Style

- Type hints MUST be present on all functions
- Docstrings MUST be present for all public functions (Google style)
- Async/await MUST be used for all I/O operations
- Bare `except:` is PROHIBITED; always catch specific exceptions

### Structure

- One tool per function; tools are composable
- Business logic MUST be separated from MCP tool definitions
- No hardcoded division IDs or credentials

### Naming

- Tools: `snake_case`, descriptive (`get_outstanding_invoices`, not `invoices`)
- Discovery tools: prefix with `explore_` or `list_`
- Dutch terms where relevant for domain (e.g., "grootboek", "administratie")

## API Constraints

### Exact Online Specifics

- Division (administratie) MUST always be explicit
- API rate limit: respect 60 calls/minute
- Tokens expire quickly (10 min); refresh tokens after 30 days
- Pagination via `$skip` and `$top`, max 1000 records per call

### MCP Tool Design

- Tools MUST return structured data (dicts/lists), not formatted strings
- Claude formats the output, not the tool
- Optional parameters MUST have sensible defaults
- Large datasets: pagination MUST be built-in; never fetch everything at once

## Out of Scope

The following are explicitly excluded from this project:

- Writing to Exact Online (creating invoices, etc.)
- Multi-tenant support (this is for YipYip internal use)
- Web UI or dashboard
- Caching (for now; may be added later via constitution amendment)

## Governance

### Definition of Done

A tool is complete when:

1. Type hints are complete
2. Error handling is present for auth and API failures
3. Documented in README
4. Tested with real Exact Online data (not just mocks)

### Amendment Procedure

1. Proposed amendments MUST be documented with rationale
2. Changes require explicit approval before implementation
3. Version number MUST be incremented according to semver:
   - MAJOR: Principle removals or incompatible redefinitions
   - MINOR: New principles or materially expanded guidance
   - PATCH: Clarifications, wording, or non-semantic refinements
4. All dependent templates MUST be reviewed for consistency

### Compliance

- All PRs/reviews MUST verify constitution compliance
- Complexity beyond these guidelines MUST be justified in writing

**Version**: 1.0.0 | **Ratified**: 2025-12-22 | **Last Amended**: 2025-12-22
