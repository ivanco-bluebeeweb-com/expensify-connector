"""Connection management for Expensify Connector: connect/disconnect/list.

Simplest connection flow of any connector this session -- static
partnerUserID/partnerUserSecret pair, verified synchronously against a
harmless 'get' policyList job, no token/expiry to manage at all.
"""
from __future__ import annotations

import json
import uuid

from imperal_sdk import ActionResult

import expensify_client as ec
from app import chat
from schemas import (
    NoParams,
    ConnectExpensifyParams,
    ProviderConnection, ProviderConnectionList,
    DisconnectExpensifyParams, DeleteResult,
)

_SECRET_NAME = "expensify_connections"


async def _load_connections(ctx) -> list[dict]:
    raw = await ctx.secrets.get(_SECRET_NAME)
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return []
    return data if isinstance(data, list) else []


async def _save_connections(ctx, connections: list[dict]) -> None:
    await ctx.secrets.set(_SECRET_NAME, json.dumps(connections))


async def resolve_connection(ctx, connection_id: str = "") -> dict | None:
    connections = await _load_connections(ctx)
    if not connections:
        return None
    if connection_id:
        for c in connections:
            if c.get("id") == connection_id:
                return c
        return None
    return connections[0]


async def resolve_or_error(ctx, connection_id: str = ""):
    conn = await resolve_connection(ctx, connection_id)
    if not conn:
        return None, ActionResult.error(
            "No Expensify connection found. Connect Expensify first.",
            code="EXPENSIFY_NOT_CONNECTED",
        )
    return conn, None


@chat.function(
    "connect_expensify",
    "Connect your own Expensify account by saving your Integration Server partnerUserID/partnerUserSecret "
    "pair (from expensify.com/tools/integrations), after checking it actually works.",
    action_type="write", chain_callable=True, data_model=ProviderConnection,
    event="expensify-connector.connect_expensify", effects=["create:connection"],
)
async def connect_expensify(ctx, params: ConnectExpensifyParams) -> ActionResult:
    """Verify the partner credential pair and save the connection."""
    if not params.partner_user_id or not params.partner_user_secret:
        return ActionResult.error(
            "partner_user_id and partner_user_secret are both required.",
            code="EXPENSIFY_VALIDATION_FAILED",
        )
    result = await ec.verify_credentials(params.partner_user_id, params.partner_user_secret)
    if not result.get("ok"):
        return ActionResult.error(result.get("message", "Could not verify Expensify credentials."),
                                   code=result.get("code", "EXPENSIFY_UNAUTHORIZED"))
    connections = await _load_connections(ctx)
    conn_id = str(uuid.uuid4())
    connections.append({
        "id": conn_id,
        "label": params.label or "Expensify",
        "partner_user_id": params.partner_user_id,
        "partner_user_secret": params.partner_user_secret,
    })
    await _save_connections(ctx, connections)
    return ActionResult.ok(ProviderConnection(id=conn_id, label=params.label or "Expensify"))


@chat.function(
    "list_connections",
    "List the connected Expensify accounts.",
    action_type="read", chain_callable=True, data_model=ProviderConnectionList,
)
async def list_connections(ctx, params: NoParams) -> ActionResult:
    """List the connected Expensify accounts."""
    connections = await _load_connections(ctx)
    items = [ProviderConnection(id=c.get("id", ""), label=c.get("label", "")) for c in connections]
    return ActionResult.ok(ProviderConnectionList(connections=items))


@chat.function(
    "disconnect_expensify",
    "Disconnect an Expensify account: deletes the saved partnerUserID/partnerUserSecret pair. Nothing in "
    "Expensify itself is changed.",
    action_type="write", chain_callable=True, data_model=DeleteResult,
    event="expensify-connector.disconnect_expensify", effects=["delete:connection"],
)
async def disconnect_expensify(ctx, params: DisconnectExpensifyParams) -> ActionResult:
    """Disconnect an Expensify account: deletes the saved connection."""
    connections = await _load_connections(ctx)
    remaining = [c for c in connections if c.get("id") != params.connection_id]
    if len(remaining) == len(connections):
        return ActionResult.error("Connection not found.", code="EXPENSIFY_NOT_CONNECTED")
    await _save_connections(ctx, remaining)
    return ActionResult.ok(DeleteResult(deleted=True, id=params.connection_id))
