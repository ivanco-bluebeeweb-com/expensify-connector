"""Thin HTTP client for Expensify Integration Server API.

Single dispatch endpoint, static partner credentials -- no OAuth, no
token refresh. Same "fail()-dict + ClientFail exception" shape as every
other connector this session's *_client.py, adapted to Expensify's
job-description POST body model.
"""
from __future__ import annotations

import json
from typing import Any

import httpx

ENDPOINT = "https://integrations.expensify.com/Integration-Server/ExpensifyIntegrations"

EXPENSIFY_NOT_CONNECTED = "EXPENSIFY_NOT_CONNECTED"
EXPENSIFY_UNAUTHORIZED = "EXPENSIFY_UNAUTHORIZED"
EXPENSIFY_NOT_FOUND = "EXPENSIFY_NOT_FOUND"
EXPENSIFY_RATE_LIMITED = "EXPENSIFY_RATE_LIMITED"
EXPENSIFY_BACKEND_ERROR = "EXPENSIFY_BACKEND_ERROR"
EXPENSIFY_VALIDATION_FAILED = "EXPENSIFY_VALIDATION_FAILED"
EXPENSIFY_RESPONSE_UNEXPECTED = "EXPENSIFY_RESPONSE_UNEXPECTED"

_MESSAGES = {
    EXPENSIFY_NOT_CONNECTED: "No Expensify connection found. Connect Expensify first.",
    EXPENSIFY_UNAUTHORIZED: "Expensify rejected the partnerUserID/partnerUserSecret pair as invalid.",
    EXPENSIFY_NOT_FOUND: "That Expensify record was not found.",
    EXPENSIFY_RATE_LIMITED: "Expensify rate-limited this request. Try again shortly.",
    EXPENSIFY_BACKEND_ERROR: "Expensify's API returned an error.",
    EXPENSIFY_VALIDATION_FAILED: "Expensify rejected the request as invalid.",
    EXPENSIFY_RESPONSE_UNEXPECTED: "Expensify returned an unexpected response shape.",
}


class ClientFail(Exception):
    def __init__(self, payload: dict):
        self.payload = payload
        super().__init__(payload.get("message", "Expensify request failed"))


def fail(code: str, detail: str = "") -> dict:
    msg = _MESSAGES.get(code, "Expensify request failed.")
    if detail:
        msg = f"{msg} ({detail})"
    return {"ok": False, "code": code, "message": msg}


def parse_json_object(raw: str):
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return None
    return data if isinstance(data, dict) else None


async def verify_credentials(partner_user_id: str, partner_user_secret: str) -> dict:
    """Verify a partnerUserID/Secret pair works by requesting the policy list."""
    body = {
        "requestJobDescription": {
            "type": "get",
            "credentials": {"partnerUserID": partner_user_id, "partnerUserSecret": partner_user_secret},
            "inputSettings": {"type": "policyList"},
        }
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(ENDPOINT, json=body)
    if resp.status_code == 401:
        raise ClientFail(fail(EXPENSIFY_UNAUTHORIZED))
    if resp.status_code >= 500:
        raise ClientFail(fail(EXPENSIFY_BACKEND_ERROR, f"HTTP {resp.status_code}"))
    if resp.status_code >= 400:
        raise ClientFail(fail(EXPENSIFY_VALIDATION_FAILED, f"HTTP {resp.status_code}: {resp.text[:200]}"))
    try:
        data = resp.json()
    except ValueError:
        raise ClientFail(fail(EXPENSIFY_RESPONSE_UNEXPECTED, "non-JSON response"))
    return data if isinstance(data, (list, dict)) else {}


def _check_status(resp: httpx.Response, action: str) -> Any:
    if resp.status_code == 401:
        raise ClientFail(fail(EXPENSIFY_UNAUTHORIZED))
    if resp.status_code == 404:
        raise ClientFail(fail(EXPENSIFY_NOT_FOUND))
    if resp.status_code == 429:
        raise ClientFail(fail(EXPENSIFY_RATE_LIMITED))
    if resp.status_code >= 500:
        raise ClientFail(fail(EXPENSIFY_BACKEND_ERROR, f"HTTP {resp.status_code} while trying to {action}"))
    if resp.status_code >= 400:
        raise ClientFail(fail(EXPENSIFY_VALIDATION_FAILED, f"HTTP {resp.status_code} while trying to {action}: {resp.text[:200]}"))
    try:
        return resp.json()
    except ValueError:
        raise ClientFail(fail(EXPENSIFY_RESPONSE_UNEXPECTED, f"non-JSON response while trying to {action}"))


async def request(ctx, conn: dict, job_type: str, input_settings: dict, *, action: str = "call Expensify") -> Any:
    """Dispatch one requestJobDescription job against Expensify's single endpoint."""
    body = {
        "requestJobDescription": {
            "type": job_type,
            "credentials": {
                "partnerUserID": conn.get("partner_user_id", ""),
                "partnerUserSecret": conn.get("partner_user_secret", ""),
            },
            "inputSettings": input_settings,
        }
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(ENDPOINT, json=body)
    return _check_status(resp, action)


def known_entities() -> list[str]:
    return ["policies", "policy-employees", "reports"]
