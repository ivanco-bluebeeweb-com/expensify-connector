"""Expense report handlers + value-add reports for Expensify Connector."""
from __future__ import annotations

from imperal_sdk import ActionResult

import expensify_client as ec
from app import chat
from handlers_connection import resolve_or_error
from schemas import (
    ListReportsParams, ReportList, ReportSummary,
    GetReportParams, ReportDetail,
    SpendOverviewReport, PendingApprovalsReport,
)


def _to_summary(r: dict) -> ReportSummary:
    return ReportSummary(
        report_id=r.get("reportID", ""),
        report_name=r.get("reportName", ""),
        total=float(r.get("total", 0) or 0),
        currency=r.get("currency", ""),
        state=r.get("state", ""),
        submitter_email=r.get("submitterEmail", ""),
    )


@chat.function(
    "list_reports",
    "List expense reports on the connected Expensify account, optionally filtered to one policy.",
    action_type="read", chain_callable=True, data_model=ReportList,
)
async def list_reports(ctx, params: ListReportsParams) -> ActionResult:
    """List expense reports."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if not conn:
        return err
    input_settings = {"type": "reportList", "limit": params.limit}
    if params.policy_id:
        input_settings["policyIDList"] = params.policy_id
    data = await ec.request(ctx, conn, "get", input_settings, action="list reports")
    rows = data if isinstance(data, list) else []
    return ActionResult.success(ReportList(reports=[_to_summary(r) for r in rows]), summary="Reports listed.")


@chat.function(
    "get_report",
    "Read one Expensify expense report in full by its report id.",
    action_type="read", chain_callable=True, data_model=ReportDetail,
)
async def get_report(ctx, params: GetReportParams) -> ActionResult:
    """Read one expense report in full."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if not conn:
        return err
    data = await ec.request(
        ctx, conn, "get", {"type": "report", "reportID": params.report_id}, action="get report",
    )
    return ActionResult.success(ReportDetail(report_id=params.report_id, data=data if isinstance(data, dict) else {}), summary="Report retrieved.")


@chat.function(
    "get_spend_overview_report",
    "Value-add report: one-glance spend overview for the connected Expensify account -- total report count, "
    "total spend, and a breakdown by report state (open/submitted/approved/reimbursed).",
    action_type="read", chain_callable=True, data_model=SpendOverviewReport,
)
async def get_spend_overview_report(ctx, params: ListReportsParams) -> ActionResult:
    """Scan reports and build a spend overview."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if not conn:
        return err
    input_settings = {"type": "reportList", "limit": params.limit or 200}
    if params.policy_id:
        input_settings["policyIDList"] = params.policy_id
    data = await ec.request(ctx, conn, "get", input_settings, action="list reports for spend overview")
    rows = data if isinstance(data, list) else []
    by_state: dict[str, int] = {}
    total_spend = 0.0
    for r in rows:
        state = r.get("state", "unknown")
        by_state[state] = by_state.get(state, 0) + 1
        total_spend += float(r.get("total", 0) or 0)
    return ActionResult.success(SpendOverviewReport(total_reports=len(rows), total_spend=total_spend, by_state=by_state), summary="Spend overview report retrieved.")


@chat.function(
    "get_pending_approvals_report",
    "Value-add report: list expense reports currently awaiting your approval on the connected Expensify "
    "account.",
    action_type="read", chain_callable=True, data_model=PendingApprovalsReport,
)
async def get_pending_approvals_report(ctx, params: ListReportsParams) -> ActionResult:
    """Scan reports and flag those in a pending-approval state."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if not conn:
        return err
    input_settings = {"type": "reportList", "limit": params.limit or 200}
    if params.policy_id:
        input_settings["policyIDList"] = params.policy_id
    data = await ec.request(ctx, conn, "get", input_settings, action="list reports for pending approvals")
    rows = data if isinstance(data, list) else []
    pending = [_to_summary(r) for r in rows if r.get("state") in ("SUBMITTED", "PROCESSING")]
    return ActionResult.success(PendingApprovalsReport(count=len(pending), reports=pending), summary="Pending approvals report retrieved.")
