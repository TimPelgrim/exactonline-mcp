# Feature Specification: Revenue Tools

**Feature Branch**: `002-revenue-tools`
**Created**: 2025-12-22
**Status**: Draft
**Input**: MCP tools for analyzing revenue data from Exact Online

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Revenue by Time Period (Priority: P1)

As a business owner or financial analyst, I want to see revenue broken down by time periods (month, quarter, year) so I can track business performance and identify trends.

**Why this priority**: Revenue over time is the most fundamental financial metric. Without this, users cannot track business performance at all. This is the core value proposition.

**Independent Test**: Request revenue for a date range grouped by month. Verify totals are returned with period-over-period comparison percentages.

**Acceptance Scenarios**:

1. **Given** authenticated user with division access, **When** requesting revenue for Jan-Dec 2024 grouped by quarter, **Then** system returns 4 quarters with revenue totals and comparison to previous period
2. **Given** authenticated user, **When** requesting revenue grouped by month for Q1 2024, **Then** system returns 3 months (Jan, Feb, Mar) with totals and month-over-month change percentages
3. **Given** valid date range with no invoices, **When** requesting revenue, **Then** system returns zero values with appropriate indication

---

### User Story 2 - View Revenue by Customer (Priority: P2)

As a sales manager, I want to see which customers generate the most revenue so I can prioritize key accounts and identify growth opportunities.

**Why this priority**: Customer analysis is essential for sales strategy but depends on having revenue data infrastructure from P1.

**Independent Test**: Request top 10 customers by revenue. Verify customer names, revenue amounts, invoice counts, and percentage of total are returned, sorted by revenue descending.

**Acceptance Scenarios**:

1. **Given** authenticated user, **When** requesting top 5 customers for 2024, **Then** system returns 5 customers sorted by revenue descending with name, total revenue, invoice count, and percentage of total
2. **Given** date range with invoices to multiple customers, **When** requesting all customers (no top limit), **Then** system returns complete customer revenue breakdown
3. **Given** division with no invoices, **When** requesting customer revenue, **Then** system returns empty list with appropriate message

---

### User Story 3 - View Revenue by Project (Priority: P3)

As a project manager, I want to see revenue per project so I can track project profitability and compare project performance.

**Why this priority**: Project-based revenue is only relevant for companies doing project work. It's valuable but more specialized than time/customer analysis.

**Independent Test**: Request project revenue for a date range. Verify projects are returned with client, revenue, and hours (if available).

**Acceptance Scenarios**:

1. **Given** authenticated user with project-based division, **When** requesting project revenue for 2024, **Then** system returns projects with client name, revenue, and logged hours
2. **Given** project with no linked invoices, **When** requesting project revenue, **Then** project shows zero revenue
3. **Given** division without project module enabled, **When** requesting project revenue, **Then** system returns appropriate message indicating project data unavailable

---

### Edge Cases

- What happens when date range spans multiple fiscal years?
- How does system handle invoices in draft/unpaid status vs. finalized invoices?
- What happens when division parameter is invalid or user lacks access?
- How are credit notes (negative invoices) handled in revenue calculations?
- What happens when API rate limit is reached during data aggregation?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide `get_revenue_by_period` tool returning revenue totals grouped by month, quarter, or year
- **FR-002**: System MUST calculate period-over-period comparison as percentage change
- **FR-003**: System MUST provide `get_revenue_by_customer` tool returning customer revenue rankings
- **FR-004**: System MUST return customer name, total revenue, invoice count, and percentage of total revenue
- **FR-005**: System MUST support `top` parameter to limit customer results (default 10)
- **FR-006**: System MUST provide `get_revenue_by_project` tool returning project-based revenue
- **FR-007**: System MUST include project name, client name, revenue, and hours (if available) in project results
- **FR-008**: All tools MUST support optional `division` parameter, defaulting to user's current division
- **FR-009**: All tools MUST support optional date range filtering via `start_date` and `end_date` (ISO format)
- **FR-010**: System MUST use existing ExactOnlineClient infrastructure (rate limiting, retry logic, authentication)
- **FR-011**: System MUST only perform read operations (GET requests)
- **FR-012**: System MUST return structured error responses following existing patterns

### Key Entities

- **Revenue Period**: Time-bounded revenue total with period identifier, amount, and comparison percentage
- **Customer Revenue**: Customer with aggregated revenue metrics (name, total, invoice count, share of total)
- **Project Revenue**: Project with associated client, revenue amount, and optional time tracking data

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can retrieve revenue by period for any valid date range in under 5 seconds
- **SC-002**: Revenue totals accurately reflect sum of invoices in Exact Online for the specified period
- **SC-003**: Period-over-period comparisons correctly calculate percentage change
- **SC-004**: Customer revenue list correctly sorts by revenue descending
- **SC-005**: All three tools handle empty result sets gracefully without errors
- **SC-006**: Tools integrate seamlessly with Claude Desktop via MCP protocol

## Assumptions

- Revenue is calculated from finalized sales invoices (not drafts or quotes)
- Invoice amounts use the base currency of the division
- Period comparisons use equivalent length periods (e.g., Q1 2024 vs Q1 2023)
- Project revenue links to invoices via project references in Exact Online
- Hours data comes from time transactions linked to projects

## Out of Scope

- Revenue forecasting or projections
- Real-time revenue updates (point-in-time queries only)
- Multi-currency conversion or reporting
- Invoice-level detail (use `explore_endpoint` for that)
- Write operations (creating/modifying invoices)
