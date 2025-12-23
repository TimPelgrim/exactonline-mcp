# Research: Revenue Tools API Endpoints

**Feature**: 002-revenue-tools
**Date**: 2025-12-22
**Status**: Complete

## Overview

This document captures API research for implementing the three revenue analysis tools:
1. `get_revenue_by_period` - Revenue by time period with YoY comparison
2. `get_revenue_by_customer` - Customer revenue rankings
3. `get_revenue_by_project` - Project-based revenue with hours

## Primary Endpoints

### 1. salesinvoice/SalesInvoices

**Path**: `/api/v1/{division}/salesinvoice/SalesInvoices`

**Purpose**: Primary source for revenue data (invoice headers)

**Key Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `ID` | Edm.Guid | Invoice identifier |
| `AmountDC` | Edm.Double | Total amount in default currency (sum of lines) |
| `AmountFC` | Edm.Double | Total amount in foreign currency (sum of lines, including VAT) |
| `InvoiceDate` | Edm.DateTime | Official invoice date |
| `InvoiceTo` | Edm.Guid | Customer reference (GUID) |
| `InvoiceToName` | Edm.String | Customer name |
| `Status` | Edm.Int16 | Processing status |
| `Currency` | Edm.String | Currency code |
| `Journal` | Edm.String | Sales journal reference |

**Status Values**:
| Status | Meaning | Include in Revenue? |
|--------|---------|---------------------|
| 10 | Draft | ❌ No - unfinished, excluded from reports |
| 20 | Open | ❌ No - still modifiable |
| 50 | Processed | ✅ Yes - finalized and locked |

**Filter for Finalized Invoices**:
```
$filter=Status eq 50
```

**Date Range Filter**:
```
$filter=InvoiceDate ge datetime'2024-01-01' and InvoiceDate le datetime'2024-12-31'
```

**Credit Notes**: Represented as invoices with negative `AmountDC`/`AmountFC` values. No separate endpoint needed - simply include in sum, and they automatically reduce totals.

### 2. salesinvoice/SalesInvoiceLines

**Path**: `/api/v1/{division}/salesinvoice/SalesInvoiceLines`

**Purpose**: Invoice line details with project links (needed for project-based revenue)

**Key Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `ID` | Edm.Guid | Line identifier |
| `InvoiceID` | Edm.Guid | Parent invoice reference |
| `Project` | Edm.Guid | Project reference (can differ per line) |
| `AmountFC` | Edm.Double | Line amount excluding VAT (foreign currency) |
| `AmountDC` | Edm.Double | Line amount excluding VAT (default currency) |
| `VATAmountFC` | Edm.Double | VAT amount |
| `Quantity` | Edm.Double | Number of items |
| `UnitPrice` | Edm.Double | Price per unit |

**Note**: Project field is on SalesInvoiceLines, not SalesInvoices. For project-based revenue, must query invoice lines and aggregate by Project field.

### 3. project/Projects

**Path**: `/api/v1/{division}/project/Projects`

**Purpose**: Project metadata for revenue by project tool

**Key Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `ID` | Edm.Guid | Project identifier |
| `Code` | Edm.String | Project code |
| `Description` | Edm.String | Project name |
| `Account` | Edm.Guid | Client reference |
| `AccountCode` | Edm.String | Client identifier |
| `AccountName` | Edm.String | Client name |
| `Type` | Edm.Int32 | Project type |

**Project Types**:
| Type | Meaning |
|------|---------|
| 1 | Campaign |
| 2 | Fixed Price |
| 3 | Time and Material |
| 4 | Non-billable |
| 5 | Prepaid |

### 4. project/TimeTransactions

**Path**: `/api/v1/{division}/project/TimeTransactions`

**Purpose**: Hours tracking for project-based revenue

**Key Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `ID` | Edm.Guid | Transaction identifier |
| `Project` | Edm.Guid | Project reference |
| `Account` | Edm.Guid | Customer reference |
| `Date` | Edm.DateTime | Transaction date |
| `Quantity` | Edm.Double | Hours (quantity of time item) |
| `Employee` | Edm.Guid | Employee reference |
| `AmountFC` | Edm.Double | Calculated amount (Quantity × PriceFC) |

**Note**: `Quantity` field represents hours when the linked `Item` is a time-based item.

### 5. crm/Accounts

**Path**: `/api/v1/{division}/crm/Accounts`

**Purpose**: Customer details (for enriching InvoiceTo GUID with name)

**Key Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `ID` | Edm.Guid | Account identifier |
| `Name` | Edm.String | Account name |
| `Code` | Edm.String | Account code |

**Note**: May not be needed if using `InvoiceToName` from SalesInvoices.

## Implementation Strategy

### get_revenue_by_period

1. Query `salesinvoice/SalesInvoices` with:
   - `$filter=Status eq 50 and InvoiceDate ge datetime'{start}' and InvoiceDate le datetime'{end}'`
   - `$select=InvoiceDate,AmountDC`
2. Client-side: Group by period (month/quarter/year)
3. For comparison: Query same filter for previous year
4. Calculate percentage change: `((current - previous) / previous) * 100`

**Pagination**: Use `$top=1000` and `$skip` for large datasets. Loop until no more results.

### get_revenue_by_customer

1. Query `salesinvoice/SalesInvoices` with:
   - `$filter=Status eq 50` + optional date range
   - `$select=InvoiceTo,InvoiceToName,AmountDC`
2. Client-side: Aggregate by InvoiceTo
   - Sum AmountDC per customer
   - Count invoices per customer
   - Calculate percentage of total
3. Sort by revenue descending
4. Return top N (default 10)

### get_revenue_by_project

1. Query `salesinvoice/SalesInvoiceLines` with:
   - `$filter=Project ne null` + join on invoice status/date
   - `$select=Project,AmountDC,InvoiceID`
2. Query `project/Projects` for project metadata
3. Optionally query `project/TimeTransactions` for hours:
   - `$filter=Project eq guid'{project_id}'` + date range
   - Aggregate Quantity field
4. Client-side: Join and aggregate by Project

**Challenge**: SalesInvoiceLines doesn't have direct access to parent invoice Status/Date. Options:
- Option A: Query all processed invoices first, then filter lines by InvoiceID
- Option B: Use `$expand` parameter if available
- Option C: Filter lines by their own Created/Modified dates (less accurate)

Recommend Option A for accuracy.

## OData Query Syntax

### Filter Operators
| Operator | Meaning | Example |
|----------|---------|---------|
| `eq` | Equal | `Status eq 50` |
| `ne` | Not equal | `Project ne null` |
| `gt` | Greater than | `AmountDC gt 0` |
| `lt` | Less than | `AmountDC lt 1000` |
| `ge` | Greater or equal | `InvoiceDate ge datetime'2024-01-01'` |
| `le` | Less or equal | `InvoiceDate le datetime'2024-12-31'` |
| `and` | Logical AND | `Status eq 50 and AmountDC gt 0` |
| `or` | Logical OR | `Status eq 20 or Status eq 50` |

### Date Format
```
datetime'YYYY-MM-DD'
datetime'YYYY-MM-DDTHH:MM:SS'
```

### Pagination
```
$top=1000
$skip=0   (first page)
$skip=1000 (second page)
```

### Field Selection
```
$select=ID,InvoiceDate,AmountDC,InvoiceTo,InvoiceToName
```

## Rate Limiting Considerations

- API limit: 60 calls/minute
- For large date ranges with many invoices:
  - Each page (1000 records) = 1 API call
  - 10,000 invoices = 10 API calls
- For project revenue with hours:
  - May need multiple calls per project for TimeTransactions
  - Consider batch approach or caching

## Sources

- [Exact Online REST API - SalesInvoices](https://start.exactonline.nl/docs/HlpRestAPIResourcesDetails.aspx?name=SalesInvoiceSalesInvoices)
- [Exact Online REST API - SalesInvoiceLines](https://start.exactonline.nl/docs/HlpRestAPIResourcesDetails.aspx?name=SalesInvoiceSalesInvoiceLines)
- [Exact Online REST API - Projects](https://start.exactonline.nl/docs/HlpRestAPIResourcesDetails.aspx?name=ProjectProjects)
- [Exact Online REST API - TimeTransactions](https://start.exactonline.nl/docs/HlpRestAPIResourcesDetails.aspx?name=ProjectTimeTransactions)
- [Business Example API Sales Invoice](https://support.exactonline.com/community/s/article/All-All-DNO-Content-business-example-api-sales-invoice)
