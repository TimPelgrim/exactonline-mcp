# Data Model: Discovery Tools

**Date**: 2025-12-22
**Feature**: 001-discovery-tools

## Entities

### Division

Represents an Exact Online administratie (company/entity).

| Field | Type | Description |
|-------|------|-------------|
| code | int | Unique division identifier (e.g., 7095) |
| name | str | Display name of the division |
| is_current | bool | Whether this is the user's default division |

**Source**: `GET /api/v1/{division}/hrm/Divisions`

**Notes:**
- Code is numeric, not a string
- Sorted by name when returned to user
- `is_current` determined by comparing to `Me.CurrentDivision`

---

### Token

OAuth2 token pair for API authentication.

| Field | Type | Description |
|-------|------|-------------|
| access_token | str | Bearer token for API calls (10 min lifetime) |
| refresh_token | str | Token for obtaining new access token (30 day lifetime) |
| obtained_at | datetime | Timestamp when tokens were obtained |
| expires_in | int | Seconds until access token expires (usually 600) |

**Storage**: System keyring or encrypted JSON file

**Notes:**
- NEVER logged or included in responses
- Refresh before `obtained_at + 9.5 minutes`
- New refresh_token returned on each refresh (old one invalidates)

---

### Endpoint

A known Exact Online API endpoint in the catalog.

| Field | Type | Description |
|-------|------|-------------|
| path | str | API path (e.g., "crm/Accounts") |
| category | str | Grouping category (crm, sales, financial, project, logistics) |
| description | str | Human-readable description |
| typical_use | str | Example use case |

**Source**: Static catalog in `endpoints.py`

**Notes:**
- No API call needed; locally maintained list
- Expandable based on discovery findings

---

### ExplorationResult

Result of exploring an API endpoint.

| Field | Type | Description |
|-------|------|-------------|
| endpoint | str | The requested endpoint path |
| division | int | Division code used for the query |
| count | int | Number of records returned |
| data | list[dict] | Sample records from the endpoint |
| available_fields | list[str] | Field names found in the response |

**Notes:**
- `data` contains raw API response records
- `available_fields` extracted from first record's keys
- `count` capped at `top` parameter (max 25)

---

## Relationships

```
┌─────────────┐
│   Token     │
└─────────────┘
       │
       │ authenticates
       ▼
┌─────────────┐       queries        ┌─────────────────────┐
│   Client    │ ──────────────────▶  │   Division          │
└─────────────┘                      └─────────────────────┘
       │                                      │
       │ explores                             │ scopes
       ▼                                      ▼
┌─────────────────────┐              ┌─────────────────────┐
│  ExplorationResult  │ ◀──────────  │   Endpoint          │
└─────────────────────┘   uses       └─────────────────────┘
```

---

## State Transitions

### Token Lifecycle

```
[Initial] ──auth flow──▶ [Valid] ──9.5 min──▶ [Near Expiry]
                            │                       │
                            │                       │ refresh
                            │                       ▼
                            │                  [Valid] (new tokens)
                            │
                            └──30 days no use──▶ [Expired]
                                                    │
                                                    │ requires
                                                    ▼
                                              [Re-authentication]
```

### Request Flow

```
[Request] ──check token──▶ [Valid?]
                              │
              ┌───────────────┴───────────────┐
              │ yes                           │ no
              ▼                               ▼
        [Check Rate]                    [Refresh Token]
              │                               │
              │                               ▼
              │                         [Store New]
              ▼                               │
        [Under Limit?] ◀──────────────────────┘
              │
    ┌─────────┴─────────┐
    │ yes               │ no
    ▼                   ▼
[Execute]          [Wait + Retry]
    │
    ▼
[Response]
```

---

## Validation Rules

### Division
- `code` must be positive integer
- `name` must be non-empty string
- Only accessible divisions returned (API enforces)

### Token
- `access_token` and `refresh_token` must be non-empty
- `obtained_at` must be valid datetime
- Never stored in plaintext outside secure storage

### Endpoint (explore_endpoint parameters)
- `endpoint` must match pattern `category/Resource` (e.g., "crm/Accounts")
- `division` defaults to first accessible if not specified
- `top` must be 1-25 (capped if exceeded)
- `select` must be valid OData field list if provided
- `filter` must be valid OData filter expression if provided

---

## OData Query Parameters

The Exact Online API uses OData conventions:

| Parameter | Format | Example |
|-----------|--------|---------|
| $select | field1,field2 | `$select=ID,Name,Email` |
| $filter | field op value | `$filter=Name eq 'Acme'` |
| $top | integer | `$top=25` |
| $skip | integer | `$skip=100` |
| $orderby | field [asc\|desc] | `$orderby=Name asc` |

**Notes:**
- Max 1000 records per request (API limit)
- Our tool caps at 25 for exploration
- Pagination via $skip for larger datasets (future feature)
