"""Known Exact Online API endpoints catalog.

This module provides a curated list of commonly-used Exact Online API endpoints,
organized by category. Use list_endpoints() to browse available endpoints.
"""

from exactonline_mcp.models import Endpoint

# Curated catalog of known Exact Online API endpoints
KNOWN_ENDPOINTS: list[Endpoint] = [
    # CRM endpoints
    Endpoint(
        path="crm/Accounts",
        category="crm",
        description="Customer and supplier accounts",
        typical_use="Look up customer details, search for accounts by name",
    ),
    Endpoint(
        path="crm/Contacts",
        category="crm",
        description="Contact persons linked to accounts",
        typical_use="Find contact details for a customer",
    ),
    Endpoint(
        path="crm/Addresses",
        category="crm",
        description="Addresses linked to accounts",
        typical_use="Get delivery or invoice addresses",
    ),
    # Sales endpoints
    Endpoint(
        path="salesinvoice/SalesInvoices",
        category="sales",
        description="Sales invoices header data with amounts and status",
        typical_use="Revenue analysis, list invoices, check invoice status",
    ),
    Endpoint(
        path="salesinvoice/SalesInvoiceLines",
        category="sales",
        description="Invoice line items with project links",
        typical_use="Project-based revenue, get invoice line details",
    ),
    Endpoint(
        path="salesorder/SalesOrders",
        category="sales",
        description="Sales orders header data",
        typical_use="Track order status, list pending orders",
    ),
    Endpoint(
        path="salesorder/SalesOrderLines",
        category="sales",
        description="Line items on sales orders",
        typical_use="Get order line details",
    ),
    # Financial endpoints
    Endpoint(
        path="financial/GLAccounts",
        category="financial",
        description="General ledger accounts",
        typical_use="Look up account codes and descriptions",
    ),
    Endpoint(
        path="financialtransaction/TransactionLines",
        category="financial",
        description="Transaction lines (journal entries)",
        typical_use="Analyze financial transactions",
    ),
    Endpoint(
        path="cashflow/Receivables",
        category="financial",
        description="Outstanding receivables",
        typical_use="Check unpaid invoices, aging analysis",
    ),
    Endpoint(
        path="cashflow/Payables",
        category="financial",
        description="Outstanding payables",
        typical_use="Check bills to pay, cash flow planning",
    ),
    Endpoint(
        path="budget/Budgets",
        category="financial",
        description="Budget definitions",
        typical_use="Review budget allocations",
    ),
    # Project endpoints
    Endpoint(
        path="project/Projects",
        category="project",
        description="Project definitions",
        typical_use="List active projects, project status",
    ),
    Endpoint(
        path="project/TimeTransactions",
        category="project",
        description="Time entries on projects",
        typical_use="Review logged hours, time analysis",
    ),
    Endpoint(
        path="project/CostTransactions",
        category="project",
        description="Cost entries on projects",
        typical_use="Track project costs",
    ),
    # Logistics endpoints
    Endpoint(
        path="logistics/Items",
        category="logistics",
        description="Product/item master data",
        typical_use="Look up products, check stock items",
    ),
    Endpoint(
        path="inventory/StockPositions",
        category="logistics",
        description="Current stock levels",
        typical_use="Check inventory, stock availability",
    ),
    Endpoint(
        path="purchaseorder/PurchaseOrders",
        category="logistics",
        description="Purchase orders header data",
        typical_use="Track purchase orders",
    ),
    # Financial reporting endpoints (Feature 001-balance-sheet-financial)
    Endpoint(
        path="read/financial/ProfitLossOverview",
        category="financial",
        description="Profit & loss summary with year-over-year comparison",
        typical_use="Get P&L overview, revenue vs costs comparison",
    ),
    Endpoint(
        path="financial/ReportingBalance",
        category="financial",
        description="GL account balances by reporting period",
        typical_use="Check account balances, balance sheet data",
    ),
    Endpoint(
        path="read/financial/AgingReceivablesList",
        category="financial",
        description="Outstanding receivables with aging buckets",
        typical_use="Analyze overdue customer invoices by age",
    ),
    Endpoint(
        path="read/financial/AgingPayablesList",
        category="financial",
        description="Outstanding payables with aging buckets",
        typical_use="Analyze overdue supplier invoices by age",
    ),
    Endpoint(
        path="financial/FinancialPeriods",
        category="financial",
        description="Fiscal year and period definitions",
        typical_use="Get period boundaries for reporting",
    ),
]


def get_endpoints_by_category(category: str) -> list[Endpoint]:
    """Get endpoints filtered by category.

    Args:
        category: Category name to filter by.

    Returns:
        List of Endpoint objects in the specified category.
    """
    return [ep for ep in KNOWN_ENDPOINTS if ep.category == category]


def get_all_categories() -> list[str]:
    """Get list of all available categories.

    Returns:
        Sorted list of unique category names.
    """
    return sorted({ep.category for ep in KNOWN_ENDPOINTS})
