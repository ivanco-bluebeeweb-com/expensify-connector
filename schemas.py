"""Pydantic params/result models for Expensify Connector.

All params models are module-scope (V17 federal invariant, same rule as
every other connector this session's schemas.py).
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class NoParams(BaseModel):
    """Explicit empty params model -- V17 disallows untyped handlers."""
    pass


class ConnectionScoped(BaseModel):
    connection_id: str = Field(
        "",
        description="Which connected Expensify account to use (see list_connections). Omit if only one is connected.",
    )


# ──────────────────────────────────────────────────────────────────────────
# Connection -- static partner credential pair, no OAuth
# ──────────────────────────────────────────────────────────────────────────


class ConnectExpensifyParams(BaseModel):
    partner_user_id: str = Field("", description="Your Expensify Integration Server partnerUserID.")
    partner_user_secret: str = Field("", description="Your Expensify Integration Server partnerUserSecret.")
    label: str = Field("", description="Optional friendly label for this connection, e.g. 'Acme Inc Expensify'.")


class ProviderConnection(BaseModel):
    id: str = ""
    label: str = ""


class ProviderConnectionList(BaseModel):
    connections: list[ProviderConnection] = Field(default_factory=list)


class DisconnectExpensifyParams(BaseModel):
    connection_id: str = Field(description="Which connection to disconnect (see list_connections).")


class DeleteResult(BaseModel):
    deleted: bool = False
    id: str = ""


# ──────────────────────────────────────────────────────────────────────────
# Policies
# ──────────────────────────────────────────────────────────────────────────


class ListPoliciesParams(ConnectionScoped):
    pass


class PolicySummary(BaseModel):
    policy_id: str = ""
    name: str = ""
    role: str = ""


class PolicyList(BaseModel):
    policies: list[PolicySummary] = Field(default_factory=list)


class GetPolicyEmployeesParams(ConnectionScoped):
    policy_id: str = Field(description="The Expensify policy id (see list_policies).")


class PolicyEmployee(BaseModel):
    email: str = ""
    role: str = ""
    forwards_to: str = ""


class PolicyEmployeeList(BaseModel):
    policy_id: str = ""
    employees: list[PolicyEmployee] = Field(default_factory=list)


class UpdatePolicyEmployeeParams(ConnectionScoped):
    policy_id: str = Field(description="The Expensify policy id.")
    email: str = Field(description="The employee's email address.")
    role: str = Field("", description="New role, e.g. 'employee', 'admin', 'approver'. Leave empty to keep unchanged.")


class UpdateResult(BaseModel):
    updated: bool = False


# ──────────────────────────────────────────────────────────────────────────
# Expense reports
# ──────────────────────────────────────────────────────────────────────────


class ListReportsParams(ConnectionScoped):
    policy_id: str = Field("", description="Optional: only reports on this policy.")
    limit: int = Field(50, ge=1, le=200)


class ReportSummary(BaseModel):
    report_id: str = ""
    report_name: str = ""
    total: float = 0.0
    currency: str = ""
    state: str = ""
    submitter_email: str = ""


class ReportList(BaseModel):
    reports: list[ReportSummary] = Field(default_factory=list)


class GetReportParams(ConnectionScoped):
    report_id: str = Field(description="The Expensify report id.")


class ReportDetail(BaseModel):
    report_id: str = ""
    data: dict = Field(default_factory=dict)


# ──────────────────────────────────────────────────────────────────────────
# Value-add reports
# ──────────────────────────────────────────────────────────────────────────


class SpendOverviewReport(BaseModel):
    total_reports: int = 0
    total_spend: float = 0.0
    by_state: dict[str, int] = Field(default_factory=dict)


class PendingApprovalsReport(BaseModel):
    count: int = 0
    reports: list[ReportSummary] = Field(default_factory=list)
