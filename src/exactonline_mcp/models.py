"""Data models for Exact Online MCP server.

This module contains dataclasses representing the core entities used throughout
the application: Division, Token, Endpoint, ExplorationResult, revenue models,
and financial reporting models.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Division:
    """Represents an Exact Online division (administratie).

    Args:
        code: Unique numeric division identifier (e.g., 7095).
        name: Display name of the division.
        is_current: Whether this is the user's default/current division.
    """

    code: int
    name: str
    is_current: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "code": self.code,
            "name": self.name,
            "is_current": self.is_current,
        }


@dataclass
class Token:
    """OAuth2 token pair for API authentication.

    Args:
        access_token: Bearer token for API calls (10 min lifetime).
        refresh_token: Token for obtaining new access token (30 day lifetime).
        obtained_at: Timestamp when tokens were obtained.
        expires_in: Seconds until access token expires (usually 600).
    """

    access_token: str
    refresh_token: str
    obtained_at: datetime
    expires_in: int = 600

    def is_expired(self, buffer_seconds: int = 30) -> bool:
        """Check if the access token is expired or about to expire.

        Args:
            buffer_seconds: Number of seconds before actual expiry to consider
                as expired (default 30 seconds for safety margin).

        Returns:
            True if token is expired or will expire within buffer_seconds.
        """
        elapsed = (datetime.now() - self.obtained_at).total_seconds()
        # Ensure expires_in is int (may be string from old keyring data)
        expires_in = int(self.expires_in) if isinstance(self.expires_in, str) else self.expires_in
        return elapsed >= (expires_in - buffer_seconds)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage (excluding sensitive display)."""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "obtained_at": self.obtained_at.isoformat(),
            "expires_in": self.expires_in,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Token":
        """Create Token from dictionary (e.g., from storage).

        Args:
            data: Dictionary containing token fields.

        Returns:
            Token instance.
        """
        obtained_at = data.get("obtained_at")
        if isinstance(obtained_at, str):
            obtained_at = datetime.fromisoformat(obtained_at)
        elif obtained_at is None:
            obtained_at = datetime.now()

        return cls(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            obtained_at=obtained_at,
            expires_in=int(data.get("expires_in", 600)),
        )


@dataclass
class Endpoint:
    """A known Exact Online API endpoint in the catalog.

    Args:
        path: API path (e.g., "crm/Accounts").
        category: Grouping category (crm, sales, financial, project, logistics).
        description: Human-readable description of the endpoint.
        typical_use: Example use case for this endpoint.
    """

    path: str
    category: str
    description: str
    typical_use: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "path": self.path,
            "category": self.category,
            "description": self.description,
            "typical_use": self.typical_use,
        }


@dataclass
class ExplorationResult:
    """Result of exploring an API endpoint.

    Args:
        endpoint: The requested endpoint path.
        division: Division code used for the query.
        count: Number of records returned.
        data: Sample records from the endpoint.
        available_fields: Field names found in the response.
    """

    endpoint: str
    division: int
    count: int
    data: list[dict[str, Any]] = field(default_factory=list)
    available_fields: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "endpoint": self.endpoint,
            "division": self.division,
            "count": self.count,
            "data": self.data,
            "available_fields": self.available_fields,
        }


# =============================================================================
# Revenue Models (Feature 002-revenue-tools)
# =============================================================================


@dataclass
class RevenuePeriod:
    """Revenue totals for a time period with year-over-year comparison.

    Args:
        period_key: Period identifier (e.g., "2024-Q1", "2024-01", "2024").
        start_date: First day of the period (ISO format YYYY-MM-DD).
        end_date: Last day of the period (ISO format YYYY-MM-DD).
        revenue: Total revenue in default currency.
        invoice_count: Number of invoices in period.
        previous_revenue: Revenue for same period last year (None if N/A).
        change_percentage: Year-over-year change (None if previous is None/zero).
    """

    period_key: str
    start_date: str
    end_date: str
    revenue: float
    invoice_count: int
    previous_revenue: float | None = None
    change_percentage: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "period_key": self.period_key,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "revenue": self.revenue,
            "invoice_count": self.invoice_count,
            "previous_revenue": self.previous_revenue,
            "change_percentage": self.change_percentage,
        }


@dataclass
class CustomerRevenue:
    """Revenue metrics for a single customer.

    Args:
        customer_id: Exact Online account GUID.
        customer_name: Account name.
        revenue: Total revenue in default currency.
        invoice_count: Number of invoices.
        percentage_of_total: Share of total revenue (0-100).
    """

    customer_id: str
    customer_name: str
    revenue: float
    invoice_count: int
    percentage_of_total: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "revenue": self.revenue,
            "invoice_count": self.invoice_count,
            "percentage_of_total": self.percentage_of_total,
        }


@dataclass
class ProjectRevenue:
    """Revenue metrics for a single project.

    Args:
        project_id: Exact Online project GUID.
        project_code: Project code.
        project_name: Project description.
        client_id: Client account GUID (optional).
        client_name: Client account name (optional).
        revenue: Total revenue in default currency.
        invoice_count: Number of invoice lines.
        hours: Total hours logged (optional, from TimeTransactions).
    """

    project_id: str
    project_code: str
    project_name: str
    client_id: str | None
    client_name: str | None
    revenue: float
    invoice_count: int
    hours: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "project_id": self.project_id,
            "project_code": self.project_code,
            "project_name": self.project_name,
            "client_id": self.client_id,
            "client_name": self.client_name,
            "revenue": self.revenue,
            "invoice_count": self.invoice_count,
            "hours": self.hours,
        }


# =============================================================================
# Financial Reporting Models (Feature 001-balance-sheet-financial)
# =============================================================================


# Account type to category mapping for balance sheet classification
ACCOUNT_TYPE_CATEGORIES: dict[int, tuple[str, str]] = {
    # Assets
    10: ("assets", "Kas"),
    12: ("assets", "Bank"),
    20: ("assets", "Debiteuren"),
    30: ("assets", "Vaste activa"),
    # Liabilities
    40: ("liabilities", "Crediteuren"),
    50: ("liabilities", "BTW"),
    60: ("liabilities", "Kortlopende schulden"),
    # Equity
    90: ("equity", "Overig"),
    # P&L (not on balance sheet)
    110: ("pl", "Omzet"),
    111: ("pl", "Kostprijs omzet"),
    121: ("pl", "Bedrijfskosten"),
}


@dataclass
class ProfitLossOverview:
    """Profit and loss overview with year-over-year comparison.

    Args:
        division: Exact Online division code.
        current_year: Current fiscal year.
        previous_year: Previous fiscal year for comparison.
        currency_code: Currency (typically EUR).
        revenue_current_year: Total revenue current year.
        revenue_previous_year: Total revenue previous year.
        costs_current_year: Total costs current year.
        costs_previous_year: Total costs previous year.
        result_current_year: Net result current year (revenue - costs).
        result_previous_year: Net result previous year.
        current_period: Current reporting period (1-12).
        revenue_current_period: Revenue for current period.
        costs_current_period: Costs for current period.
        result_current_period: Net result for current period.
    """

    division: int
    current_year: int
    previous_year: int
    currency_code: str
    revenue_current_year: float
    revenue_previous_year: float
    costs_current_year: float
    costs_previous_year: float
    result_current_year: float
    result_previous_year: float
    current_period: int
    revenue_current_period: float
    costs_current_period: float
    result_current_period: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "division": self.division,
            "current_year": self.current_year,
            "previous_year": self.previous_year,
            "currency_code": self.currency_code,
            "revenue_current_year": self.revenue_current_year,
            "revenue_previous_year": self.revenue_previous_year,
            "costs_current_year": self.costs_current_year,
            "costs_previous_year": self.costs_previous_year,
            "result_current_year": self.result_current_year,
            "result_previous_year": self.result_previous_year,
            "current_period": self.current_period,
            "revenue_current_period": self.revenue_current_period,
            "costs_current_period": self.costs_current_period,
            "result_current_period": self.result_current_period,
        }


@dataclass
class GLAccountBalance:
    """Balance for a GL account at a specific reporting period.

    Args:
        gl_account_id: Exact Online account GUID.
        gl_account_code: Account code (e.g., "1300").
        gl_account_description: Account name (e.g., "Debiteuren").
        amount: Net balance amount.
        amount_debit: Total debit movements.
        amount_credit: Total credit movements.
        balance_type: "B" (balance sheet) or "W" (profit/loss).
        account_type: Numeric type code (20, 40, 110, etc.).
        account_type_description: Human-readable type (e.g., "Accounts receivable").
        reporting_year: Fiscal year.
        reporting_period: Period number (1-12).
    """

    gl_account_id: str
    gl_account_code: str
    gl_account_description: str
    amount: float
    amount_debit: float
    amount_credit: float
    balance_type: str  # "B" or "W"
    account_type: int
    account_type_description: str
    reporting_year: int
    reporting_period: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "gl_account_id": self.gl_account_id,
            "gl_account_code": self.gl_account_code,
            "gl_account_description": self.gl_account_description,
            "amount": self.amount,
            "amount_debit": self.amount_debit,
            "amount_credit": self.amount_credit,
            "balance_type": self.balance_type,
            "account_type": self.account_type,
            "account_type_description": self.account_type_description,
            "reporting_year": self.reporting_year,
            "reporting_period": self.reporting_period,
        }


@dataclass
class BalanceSheetCategory:
    """A category within the balance sheet.

    Args:
        name: Category name (e.g., "Liquide middelen", "Vorderingen").
        amount: Total amount for this category.
        account_count: Number of accounts in this category.
    """

    name: str
    amount: float
    account_count: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "amount": self.amount,
            "account_count": self.account_count,
        }


@dataclass
class BalanceSheetSummary:
    """Balance sheet summary grouped by category.

    Args:
        division: Exact Online division code.
        reporting_year: Fiscal year.
        reporting_period: Period number.
        currency_code: Currency (typically EUR).
        total_assets: Sum of all asset categories.
        total_liabilities: Sum of all liability categories.
        total_equity: Sum of equity accounts.
        assets: List of asset categories with amounts.
        liabilities: List of liability categories with amounts.
        equity: List of equity categories with amounts.
    """

    division: int
    reporting_year: int
    reporting_period: int
    currency_code: str
    total_assets: float
    total_liabilities: float
    total_equity: float
    assets: list[BalanceSheetCategory] = field(default_factory=list)
    liabilities: list[BalanceSheetCategory] = field(default_factory=list)
    equity: list[BalanceSheetCategory] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "division": self.division,
            "reporting_year": self.reporting_year,
            "reporting_period": self.reporting_period,
            "currency_code": self.currency_code,
            "total_assets": self.total_assets,
            "total_liabilities": self.total_liabilities,
            "total_equity": self.total_equity,
            "assets": [a.to_dict() for a in self.assets],
            "liabilities": [lib.to_dict() for lib in self.liabilities],
            "equity": [e.to_dict() for e in self.equity],
        }


@dataclass
class AgingEntry:
    """Entry in aging receivables or payables report.

    Args:
        account_id: Exact Online account GUID.
        account_code: Customer/supplier code.
        account_name: Customer/supplier name.
        total_amount: Total outstanding amount.
        age_0_30: Amount outstanding 0-30 days.
        age_31_60: Amount outstanding 31-60 days.
        age_61_90: Amount outstanding 61-90 days.
        age_over_90: Amount outstanding over 90 days.
        currency_code: Currency (typically EUR).
    """

    account_id: str
    account_code: str
    account_name: str
    total_amount: float
    age_0_30: float
    age_31_60: float
    age_61_90: float
    age_over_90: float
    currency_code: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "account_id": self.account_id,
            "account_code": self.account_code,
            "account_name": self.account_name,
            "total_amount": self.total_amount,
            "age_0_30": self.age_0_30,
            "age_31_60": self.age_31_60,
            "age_61_90": self.age_61_90,
            "age_over_90": self.age_over_90,
            "currency_code": self.currency_code,
        }


@dataclass
class TransactionLine:
    """Individual transaction line from a journal entry.

    Args:
        id: Exact Online transaction line GUID.
        date: Transaction date (ISO format YYYY-MM-DD).
        financial_year: Fiscal year.
        financial_period: Period number (1-12).
        gl_account_code: GL account code.
        gl_account_description: GL account name.
        description: Transaction description/memo.
        amount: Amount in default currency (positive=debit, negative=credit).
        entry_number: Journal entry number.
        journal_code: Journal/dagboek code.
    """

    id: str
    date: str
    financial_year: int
    financial_period: int
    gl_account_code: str
    gl_account_description: str
    description: str
    amount: float
    entry_number: int
    journal_code: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "date": self.date,
            "financial_year": self.financial_year,
            "financial_period": self.financial_period,
            "gl_account_code": self.gl_account_code,
            "gl_account_description": self.gl_account_description,
            "description": self.description,
            "amount": self.amount,
            "entry_number": self.entry_number,
            "journal_code": self.journal_code,
        }


# =============================================================================
# Open Receivables Models (Feature 003-open-receivables)
# =============================================================================


@dataclass
class OpenReceivable:
    """Single open receivable (invoice/credit) from a customer.

    Args:
        account_code: Customer account code (e.g., "400").
        account_name: Customer display name.
        invoice_number: Invoice number.
        invoice_date: Invoice date (ISO format YYYY-MM-DD).
        due_date: Payment due date (ISO format YYYY-MM-DD).
        original_amount: Original invoice amount (always positive).
        remaining_amount: Amount still outstanding (always positive).
        is_credit: True if this is a credit note/overpayment.
        description: Invoice description/memo.
        payment_terms: Payment condition description.
        days_overdue: Days past due date (negative if not yet due).
        currency: Currency code (typically EUR).
    """

    account_code: str
    account_name: str
    invoice_number: int
    invoice_date: str
    due_date: str
    original_amount: float
    remaining_amount: float
    is_credit: bool
    description: str
    payment_terms: str
    days_overdue: int
    currency: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "account_code": self.account_code,
            "account_name": self.account_name,
            "invoice_number": self.invoice_number,
            "invoice_date": self.invoice_date,
            "due_date": self.due_date,
            "original_amount": self.original_amount,
            "remaining_amount": self.remaining_amount,
            "is_credit": self.is_credit,
            "description": self.description,
            "payment_terms": self.payment_terms,
            "days_overdue": self.days_overdue,
            "currency": self.currency,
        }


@dataclass
class OpenReceivablesSummary:
    """Summary of open receivables query results.

    Args:
        division: Exact Online division code.
        total_receivables: Total amount outstanding (excluding credits).
        total_credits: Total credit amounts.
        net_receivables: Net amount (receivables - credits).
        invoice_count: Number of open invoices.
        credit_count: Number of credit notes.
        overdue_amount: Total amount that is past due.
        overdue_count: Number of overdue items.
        currency: Currency code.
        items: List of individual receivables.
    """

    division: int
    total_receivables: float
    total_credits: float
    net_receivables: float
    invoice_count: int
    credit_count: int
    overdue_amount: float
    overdue_count: int
    currency: str
    items: list[OpenReceivable] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "division": self.division,
            "total_receivables": self.total_receivables,
            "total_credits": self.total_credits,
            "net_receivables": self.net_receivables,
            "invoice_count": self.invoice_count,
            "credit_count": self.credit_count,
            "overdue_amount": self.overdue_amount,
            "overdue_count": self.overdue_count,
            "currency": self.currency,
            "items": [item.to_dict() for item in self.items],
        }


# =============================================================================
# Bank & Purchase Data Models (Feature 004-bank-purchase-data)
# =============================================================================


@dataclass
class BankTransaction:
    """Single bank transaction line from a bank entry.

    Args:
        id: Exact Online transaction line GUID.
        date: Transaction date (ISO format YYYY-MM-DD).
        description: Transaction description/memo.
        amount: Amount in default currency (negative = outflow, positive = inflow).
        account_code: Related party code (customer/supplier), if any.
        account_name: Related party name, if any.
        gl_account_code: GL account code (bank account, e.g., "1055").
        gl_account_description: GL account name (e.g., "ING Bank").
        entry_number: Journal entry number.
        document_subject: Source document description.
        notes: Additional notes/memo.
        our_ref: Internal reference number.
    """

    id: str
    date: str
    description: str
    amount: float
    account_code: str | None
    account_name: str | None
    gl_account_code: str
    gl_account_description: str
    entry_number: int
    document_subject: str
    notes: str | None
    our_ref: int | None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "date": self.date,
            "description": self.description,
            "amount": self.amount,
            "account_code": self.account_code,
            "account_name": self.account_name,
            "gl_account_code": self.gl_account_code,
            "gl_account_description": self.gl_account_description,
            "entry_number": self.entry_number,
            "document_subject": self.document_subject,
            "notes": self.notes,
            "our_ref": self.our_ref,
        }


@dataclass
class PurchaseInvoice:
    """Purchase invoice from a supplier.

    Args:
        id: Exact Online invoice GUID.
        invoice_number: Invoice number.
        invoice_date: Invoice date (ISO format YYYY-MM-DD).
        due_date: Payment due date (ISO format YYYY-MM-DD).
        supplier_code: Supplier account code.
        supplier_name: Supplier name.
        amount: Invoice amount in default currency.
        currency: Currency code (e.g., "EUR").
        status: Invoice status code (10=Draft, 20=Open, 50=Processed/Paid).
        status_description: Human-readable status.
        description: Invoice description/memo.
        payment_condition: Payment terms description.
    """

    id: str
    invoice_number: int
    invoice_date: str
    due_date: str | None
    supplier_code: str
    supplier_name: str
    amount: float
    currency: str
    status: int
    status_description: str
    description: str
    payment_condition: str | None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "invoice_number": self.invoice_number,
            "invoice_date": self.invoice_date,
            "due_date": self.due_date,
            "supplier_code": self.supplier_code,
            "supplier_name": self.supplier_name,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
            "status_description": self.status_description,
            "description": self.description,
            "payment_condition": self.payment_condition,
        }
