"""Policies + policy-employee handlers for Expensify Connector.

Uses Expensify's Integration Server 'get' job type with policyList/
policyEmployeeList inputSettings.type per integrations.expensify.com docs.
"""
from __future__ import annotations

from imperal_sdk import ActionResult

import expensify_client as ec
from app import chat
from handlers_connection import resolve_or_error
from schemas import (
    ListPoliciesParams, PolicyList, PolicySummary,
    GetPolicyEmployeesParams, PolicyEmployeeList, PolicyEmployee,
    UpdatePolicyEmployeeParams, UpdateResult,
)


@chat.function(
    "list_policies",
    "List Expensify policies (workspaces) the connected account can access, with your role on each.",
    action_type="read", chain_callable=True, data_model=PolicyList,
)
async def list_policies(ctx, params: ListPoliciesParams) -> ActionResult:
    """List Expensify policies visible to the connected account."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if not conn:
        return err
    data = await ec.request(ctx, conn, "get", {"type": "policyList"}, action="list policies")
    rows = data if isinstance(data, list) else []
    policies = [
        PolicySummary(policy_id=r.get("policyID", ""), name=r.get("name", ""), role=r.get("role", ""))
        for r in rows
    ]
    return ActionResult.success(PolicyList(policies=policies), summary="Policies listed.")


@chat.function(
    "list_policy_employees",
    "List the employees (policy members) on one Expensify policy, with their role and approval chain.",
    action_type="read", chain_callable=True, data_model=PolicyEmployeeList,
)
async def list_policy_employees(ctx, params: GetPolicyEmployeesParams) -> ActionResult:
    """List employees on one Expensify policy."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if not conn:
        return err
    data = await ec.request(
        ctx, conn, "get",
        {"type": "policyEmployeeList", "policyID": params.policy_id},
        action="list policy employees",
    )
    rows = data if isinstance(data, list) else []
    employees = [
        PolicyEmployee(email=r.get("email", ""), role=r.get("role", ""), forwards_to=r.get("forwardsTo", ""))
        for r in rows
    ]
    return ActionResult.success(PolicyEmployeeList(policy_id=params.policy_id, employees=employees), summary="Policy employees listed.")


@chat.function(
    "update_policy_employee",
    "Update an existing employee's role on an Expensify policy (e.g. promote to admin/approver).",
    action_type="write", chain_callable=True, data_model=UpdateResult,
    event="expensify-connector.update_policy_employee", effects=["update:policy_employee"],
)
async def update_policy_employee(ctx, params: UpdatePolicyEmployeeParams) -> ActionResult:
    """Update a policy employee's role."""
    conn, err = await resolve_or_error(ctx, params.connection_id)
    if not conn:
        return err
    employees = [{"email": params.email, "role": params.role}] if params.role else [{"email": params.email}]
    await ec.request(
        ctx, conn, "update",
        {"type": "policy", "policyID": params.policy_id, "employees": employees},
        action="update policy employee",
    )
    return ActionResult.success(UpdateResult(updated=True), summary="Policy employee updated.")
