"""Panel UI -- connections list/connect form + the one required "App
settings" entry point, same shape as Gusto/ADP/Paychex Flex Connector's
panels.py.

SIDEBAR CONTENT -- NO CARDS ANYWHERE, per ~/UI_INTERFACE_STANDARD.md's
"left sidebar, no decorated cards" rule. Disconnect lives only in the
"App settings" screen (panels_settings.py). The one secondary "App
settings" button is always the LAST element at the bottom of the sidebar.

PER ~/UI_INTERFACE_STANDARD.md (2026-08-21 addendum): every Input carries
its own visible label (a ui.Text wrapping the ui.Input in a Stack -- ui.Input
itself does not accept label=), the placeholder text is always contextually
specific. The "How do I set this up?" instructions live ONLY in the help
overlay below -- never duplicated as static sidebar text.
"""
from __future__ import annotations

from imperal_sdk import ui

from app import ext
import handlers_connection as h


def _settings_button() -> ui.UINode:
    return ui.Button(
        "App settings", variant="secondary", size="sm", full_width=True,
        icon="settings", on_click=ui.Call("__panel__expensify_settings"),
    )


def _connection_row(c: dict) -> ui.UINode:
    label = c.get("label") or "Expensify connection"
    return ui.Stack(direction="v", gap=1, children=[
        ui.Text(label, variant="body"),
        ui.Text("Connected", variant="caption"),
    ])


def _connections_section(connections: list[dict]) -> ui.UINode:
    if not connections:
        return ui.Text("No Expensify accounts connected yet.", variant="caption")
    children: list[ui.UINode] = []
    for i, c in enumerate(connections):
        if i > 0:
            children.append(ui.Divider())
        children.append(_connection_row(c))
    return ui.Stack(direction="v", gap=2, children=children)


def _connect_section() -> ui.UINode:
    return ui.Stack(direction="v", gap=3, children=[
        ui.Button(
            "How do I set this up?", variant="ghost", size="sm",
            on_click=ui.Call("__panel__expensify_connect_help"),
        ),
        ui.Form(
            action="connect_expensify",
            submit_label="Connect Expensify",
            children=[
                ui.Stack(direction="v", gap=1, children=[
                    ui.Text("Expensify partnerUserID", variant="caption"),
                    ui.Input(param_name="partner_user_id", placeholder="Paste your Expensify partnerUserID"),
                ]),
                ui.Stack(direction="v", gap=1, children=[
                    ui.Text("Expensify partnerUserSecret", variant="caption"),
                    ui.Password(param_name="partner_user_secret", placeholder="Paste your Expensify partnerUserSecret"),
                ]),
                ui.Stack(direction="v", gap=1, children=[
                    ui.Text("Label (optional)", variant="caption"),
                    ui.Input(param_name="label", placeholder="e.g. Acme Inc Expensify"),
                ]),
            ],
        ),
    ])


@ext.panel("expensify_connect", slot="left", title="Expensify")
async def expensify_connect_panel(ctx, **kwargs) -> object:
    connections = await h._load_connections(ctx)
    return ui.Stack(direction="v", gap=4, children=[
        ui.Header("Expensify", level=2, subtitle="Expense reports, policies & spend, connected to your own account"),
        _connections_section(connections),
        ui.Divider(),
        _connect_section(),
        ui.Divider(),
        _settings_button(),
    ])


@ext.panel("expensify_connect_help", slot="overlay", title="How do I set this up?")
async def expensify_connect_help(ctx, **kwargs) -> object:
    content = ui.Stack(direction="v", gap=3, children=[
        ui.Text("1. Sign in to Expensify and go to expensify.com/tools/integrations."),
        ui.Text("2. Generate a new partnerUserID / partnerUserSecret pair for the Integration Server API."),
        ui.Text("3. Paste both values into the form on the left, then click Connect Expensify."),
        ui.Text("No OAuth, no browser redirect -- this is a static credential pair, verified once on connect."),
    ])
    return content
