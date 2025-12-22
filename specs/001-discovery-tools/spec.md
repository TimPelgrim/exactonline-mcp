# Feature Specification: Discovery Tools

**Feature Branch**: `001-discovery-tools`
**Created**: 2025-12-22
**Status**: Draft
**Input**: API exploration tools for Exact Online before building specific business tools

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Available Divisions (Priority: P1)

As a user of the MCP server, I want to see all available Exact Online divisions
(administraties) so that I know which division ID to use for subsequent queries.

**Why this priority**: This is the foundation for all other operations. Without
knowing which division to query, no other exploration is possible. This also
validates that authentication is working correctly.

**Independent Test**: Can be fully tested by requesting the division list and
verifying at least one division is returned with code, name, and current status.

**Acceptance Scenarios**:

1. **Given** the user is authenticated with Exact Online, **When** they request
   the list of divisions, **Then** they receive a list containing at least one
   division with its code (numeric), name, and whether it's the current/default.

2. **Given** the user has access to multiple divisions, **When** they request
   the list, **Then** all accessible divisions are returned sorted by name.

3. **Given** the user's authentication has expired, **When** they request
   divisions, **Then** they receive a clear error message with instructions to
   re-authenticate.

---

### User Story 2 - Explore Endpoint Data (Priority: P2)

As a user of the MCP server, I want to retrieve sample data from any Exact
Online API endpoint so that I can understand what data is available and how
it is structured.

**Why this priority**: After knowing which division to use, users need to
explore actual data. This is the core discovery functionality that enables
understanding the API before building specific tools.

**Independent Test**: Can be tested by requesting sample data from a known
endpoint (e.g., crm/Accounts) and verifying structured data is returned with
field information.

**Acceptance Scenarios**:

1. **Given** a valid division and endpoint path, **When** the user explores
   that endpoint, **Then** they receive sample records with a count and list
   of available fields.

2. **Given** an endpoint path without specifying a division, **When** the user
   explores it, **Then** the system uses the first available division as default.

3. **Given** a request for more than 25 records, **When** the user sets top=30,
   **Then** the system caps the result at 25 records maximum.

4. **Given** an invalid or non-existent endpoint, **When** the user tries to
   explore it, **Then** they receive a clear error message indicating the
   endpoint is invalid.

5. **Given** valid OData filter and select parameters, **When** the user
   includes them in the request, **Then** the results are filtered and contain
   only the selected fields.

---

### User Story 3 - Browse Known Endpoints (Priority: P3)

As a user of the MCP server, I want to see a curated list of known/useful Exact
Online endpoints grouped by category so that I can quickly find relevant data
sources without memorizing API paths.

**Why this priority**: This enhances discoverability but is not strictly
required for exploration. Users can technically explore endpoints if they know
the paths, but this makes the experience significantly better.

**Independent Test**: Can be tested by requesting the endpoint list and
verifying categories and endpoint details are returned.

**Acceptance Scenarios**:

1. **Given** the user requests the list of endpoints, **When** no category
   filter is provided, **Then** all known endpoints are returned grouped by
   category (crm, sales, financial, project, logistics).

2. **Given** a specific category filter, **When** the user requests endpoints,
   **Then** only endpoints in that category are returned.

3. **Given** the endpoint list, **When** viewing any endpoint, **Then** it
   includes path, description, and typical use case.

---

### User Story 4 - Authenticate with Exact Online (Priority: P0 - Prerequisite)

As a user setting up the MCP server for the first time, I want to complete the
OAuth2 authentication flow so that the server can access Exact Online on my
behalf.

**Why this priority**: This is a prerequisite for all other functionality.
Without authentication, nothing works. Marked as P0 because it must happen
before any P1-P3 stories can be used.

**Independent Test**: Can be tested by running the authentication command and
verifying tokens are stored securely.

**Acceptance Scenarios**:

1. **Given** a first-time user with valid Exact Online credentials, **When**
   they run the authentication command, **Then** a browser opens to Exact
   Online login, and after authorization, tokens are stored securely.

2. **Given** stored tokens that have expired, **When** any API request is made,
   **Then** tokens are automatically refreshed without user intervention.

3. **Given** a refresh token that has expired (after 30 days), **When** any
   API request is made, **Then** the user receives a clear message to
   re-authenticate with instructions.

---

### Edge Cases

- What happens when the Exact Online API returns an empty dataset for a valid
  endpoint? System returns an empty data array with count=0 and still shows
  available_fields if possible.

- What happens when rate limits are exceeded? System waits and retries once
  after a delay, then returns an error if still rate-limited.

- What happens when network connectivity is lost mid-request? System retries
  once after 2 seconds, then returns a clear network error message.

- What happens when an endpoint exists but user lacks permission? System
  returns the API's permission error with a clear explanation.

- What happens when tokens cannot be stored securely? System falls back to
  encrypted file storage and warns the user about reduced security.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support OAuth2 authorization code flow for Exact
  Online authentication.

- **FR-002**: System MUST automatically refresh access tokens when they expire
  (before the 10-minute expiry window).

- **FR-003**: System MUST store refresh tokens securely using system keyring
  or encrypted file storage.

- **FR-004**: System MUST provide a `list_divisions` tool that returns all
  accessible divisions with code, name, and current status.

- **FR-005**: System MUST provide an `explore_endpoint` tool that accepts
  endpoint path, optional division, optional record limit (max 25), optional
  field selection, and optional OData filter.

- **FR-006**: System MUST provide a `list_endpoints` tool that returns known
  endpoints grouped by category with path, description, and typical use.

- **FR-007**: System MUST return structured data (not formatted strings) from
  all tools for Claude to format appropriately.

- **FR-008**: System MUST handle API errors gracefully with clear, actionable
  error messages that do not expose sensitive data.

- **FR-009**: System MUST respect Exact Online rate limits (max 60 calls per
  minute) with automatic retry and backoff.

- **FR-010**: System MUST timeout API requests after 30 seconds.

- **FR-011**: System MUST NOT log tokens, credentials, or complete response
  bodies (which may contain PII).

- **FR-012**: System MUST require explicit division parameter OR default to
  first available division when not specified.

### Key Entities

- **Division**: Represents an Exact Online administratie. Has a numeric code,
  display name, and flag indicating if it's the user's current/default division.

- **Endpoint**: Represents a known Exact Online API endpoint. Has a path
  (e.g., "crm/Accounts"), category, description, and typical use case.

- **Token**: OAuth2 access and refresh tokens. Access token expires in 10
  minutes, refresh token in 30 days. Never exposed in logs or responses.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete the authentication setup in under 2 minutes
  from running the auth command to having valid stored tokens.

- **SC-002**: Division list is returned within 3 seconds for authenticated users.

- **SC-003**: Sample data from any valid endpoint is returned within 5 seconds
  (excluding network latency to Exact Online).

- **SC-004**: 100% of API errors result in user-friendly error messages (no
  raw exceptions or stack traces shown to users).

- **SC-005**: Token refresh happens transparently - users never see
  "token expired" errors during normal 10-minute usage windows.

- **SC-006**: System correctly handles at least 60 sequential API calls within
  one minute without rate limit errors.

- **SC-007**: All three discovery tools (list_divisions, explore_endpoint,
  list_endpoints) are accessible and functional through the MCP interface.

## Assumptions

- Users have valid Exact Online credentials with API access enabled.
- The OAuth2 client ID and secret are provided via environment variables.
- Users have at least one division accessible in their Exact Online account.
- The system has network access to Exact Online API endpoints.
- For keyring storage: the operating system provides a secure keyring service
  (macOS Keychain, Windows Credential Manager, or Linux Secret Service).
