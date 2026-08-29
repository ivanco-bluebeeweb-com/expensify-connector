"""Extension declaration, secrets, lifecycle hooks.

WHY BYOK, same reasoning as every other connector here -- the user's own
Expensify company/policy data lives inside THEIR OWN Expensify account.

WHY STATIC PARTNER CREDENTIALS, NOT OAUTH (confirmed against
integrations.expensify.com/Integration-Server/doc, 2026-08-29): Expensify's
Integration Server API authenticates every request with a static
partnerUserID/partnerUserSecret pair embedded in the request body's
`credentials` object -- generated once from expensify.com/tools/integrations.
No token exchange, no expiry, no refresh logic needed -- the simplest auth
model of any connector built this session.

WHY A SINGLE DISPATCH ENDPOINT. Expensify's entire API is one POST endpoint
that behaves differently based on requestJobDescription.type (create, get,
update, download, file, reconciliation) -- this connector's client wraps
that dispatch behind per-resource helper calls so tool functions read like
a normal REST connector.

WHY THIS RELEASE STOPS SHORT OF FILE/REPORT EXPORT TEMPLATES. Expensify's
full report export requires a configured export template (XML/CSV) chosen
per policy in the Expensify web UI -- out of scope for a generic
connector. v1 covers policies, employees, and expense report reads/lists
plus policy-employee writes, flagged as an explicit follow-up rather than
silently omitted.
"""
from __future__ import annotations

from imperal_sdk import ChatExtension, Extension

ext = Extension(
    "expensify-connector",
    version="0.1.0",
    display_name="Expensify",
    icon="icon.svg",
    capabilities=["expensify:read", "expensify:write"],
    description=(
        "Connect your own Expensify account (Integration Server API -- bring your own partnerUserID/"
        "partnerUserSecret from expensify.com/tools/integrations) to read policies, employees, and expense "
        "reports, plus value-add spend reports. Policy-employee writes included; full report export requires "
        "a configured export template in Expensify's own UI."
    ),
)

chat = ChatExtension(ext, tool_name="expensify")

ext.secret(
    "expensify_connections", "JSON array of saved Expensify connections (partnerUserID/Secret, label).",
    required=False, write_mode="extension", max_bytes=65536, rotation_hint_days=365,
)


@ext.health_check
async def health_check(ctx):
    raw = await ctx.secrets.get("expensify_connections")
    return {"ok": True, "has_connections": bool(raw)}
