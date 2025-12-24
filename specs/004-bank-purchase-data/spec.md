# Feature Specification: Bank & Purchase Data Tools

**Feature Branch**: `004-bank-purchase-data`
**Created**: 2025-12-24
**Status**: Draft
**Input**: User description: "Add MCP tools for exposing bank transaction lines and purchase invoice data from Exact Online. Data exposure only, no pre-computed analysis."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Bank Transactions (Priority: P1)

As a business owner, I want to view individual bank transaction lines so that I can understand cash movements at a granular level and let Claude analyze patterns, reconcile accounts, or answer specific questions about payments.

**Why this priority**: Bank transactions are the foundation of cash flow understanding. This endpoint is confirmed working and provides rich data including transaction dates, amounts, descriptions, and related parties.

**Independent Test**: Call `get_bank_transactions` via MCP and verify response contains individual transaction lines with dates, amounts, and descriptions.

**Acceptance Scenarios**:

1. **Given** the user has bank transactions in Exact Online, **When** they request bank transactions without filters, **Then** they receive a list of recent transactions with date, amount, description, and account details.

2. **Given** the user wants transactions for a specific period, **When** they provide start_date and end_date parameters, **Then** only transactions within that date range are returned.

3. **Given** the user wants transactions for a specific bank account, **When** they provide a GL account code (e.g., "1055" for ING Bank), **Then** only transactions from that bank account are returned.

---

### User Story 2 - View Purchase Invoices (Priority: P2)

As a business owner, I want to view purchase invoices from suppliers so that I can understand expenses, track supplier payments, and let Claude analyze spending patterns.

**Why this priority**: Purchase invoices complement sales invoices for a complete financial picture. However, this endpoint may require the Purchase module subscription in Exact Online.

**Independent Test**: Call `get_purchase_invoices` via MCP and verify response contains invoice data with supplier, amounts, and dates.

**Acceptance Scenarios**:

1. **Given** the user has purchase invoices in Exact Online, **When** they request purchase invoices without filters, **Then** they receive a list of invoices with supplier name, invoice number, date, and amount.

2. **Given** the user wants invoices for a specific period, **When** they provide start_date and end_date parameters, **Then** only invoices within that date range are returned.

3. **Given** the user wants invoices from a specific supplier, **When** they provide a supplier code, **Then** only invoices from that supplier are returned.

4. **Given** the Purchase module is not enabled for the division, **When** the user requests purchase invoices, **Then** they receive a clear error message explaining the module requirement.

---

### Edge Cases

- What happens when no transactions exist in the requested date range? Return empty list with count: 0.
- What happens when the bank account code doesn't exist? Return clear error with guidance.
- What happens when the Purchase module is not available? Return clear error explaining module requirement.
- How are negative amounts handled? Preserve sign convention from API (negative = outflow, positive = inflow for bank).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST expose bank transaction lines from the `financialtransaction/BankEntryLines` endpoint
- **FR-002**: System MUST support filtering bank transactions by date range (start_date, end_date)
- **FR-003**: System MUST support filtering bank transactions by GL account code (bank account)
- **FR-004**: System MUST support limiting the number of returned records (top parameter, max 1000)
- **FR-005**: System MUST expose purchase invoices from the `purchase/PurchaseInvoices` endpoint
- **FR-006**: System MUST support filtering purchase invoices by date range
- **FR-007**: System MUST support filtering purchase invoices by supplier code
- **FR-008**: System MUST return clear error messages when endpoints are inaccessible due to module requirements
- **FR-009**: System MUST preserve raw data without pre-computing ratios or aggregations (data exposure principle)
- **FR-010**: System MUST convert OData date formats to ISO format for readability

### Key Entities

- **BankTransaction**: Individual bank entry line representing a single transaction (date, amount, description, related party, GL account, entry number)
- **PurchaseInvoice**: Supplier invoice with header information (supplier, invoice number, date, amount, currency, status)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can retrieve bank transactions and receive response within standard API response times
- **SC-002**: Users can filter bank transactions by date range and receive only matching records
- **SC-003**: Users can filter bank transactions by bank account and receive only matching records
- **SC-004**: Claude can answer questions like "What did we pay to X last month?" using the bank transaction data
- **SC-005**: Users receive clear, actionable error messages when endpoints are unavailable
- **SC-006**: Data returned matches the raw data in Exact Online without transformation or analysis

## Assumptions

- Bank transactions are available via `financialtransaction/BankEntryLines` (confirmed working)
- Purchase invoices via `purchase/PurchaseInvoices` may require the Purchase module subscription
- Date filtering uses OData datetime format (converted from user-provided ISO dates)
- Default division is used if not specified (consistent with existing tools)
- Maximum 1000 records per request (Exact Online API limit)

## Constraints

- **Module Dependency**: Purchase invoices endpoint may not be available for all divisions (requires Purchase module)
- **Read-Only**: Only GET requests, no data modification
- **Rate Limit**: Subject to Exact Online's 60 calls/minute limit
- **Data Exposure Only**: No pre-computed analysis or aggregations - raw data for downstream processing
