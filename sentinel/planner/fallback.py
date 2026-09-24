"""Deterministic fallback planner — used when the LLM is unavailable.

Maps fired rules to templated, non-destructive verification cases so the
pipeline always produces a usable plan (offline, in CI, or without a key).
"""
from __future__ import annotations

from ..models import Endpoint
from .models import Account, EndpointPlan, Signal, TestCase, TestStep

USER_A = Account("user_a", "primary authorized test account")
USER_B = Account("user_b", "second account, owns different resources")
ANON = Account("anonymous", "no credentials")
ADMIN = Account("admin", "privileged account")


def _templates(ep: Endpoint, fired: set[str]) -> list[TestCase]:
    cases: list[TestCase] = []

    if "object-id" in fired and ep.requires_auth:
        cases.append(TestCase(
            hypothesis="Broken object-level authorization (BOLA): one user may read another's resource.",
            category="API1:2023",
            required_accounts=[USER_A, USER_B],
            steps=[TestStep(
                f"As user_a, request {ep.id} using an identifier that belongs to user_b.",
                "API returns 403/404 and never discloses user_b's data.")],
        ))

    if "no-auth" in fired:
        cases.append(TestCase(
            hypothesis="Missing authentication on a sensitive operation.",
            category="API2:2023",
            required_accounts=[ANON],
            steps=[TestStep(
                f"Call {ep.id} with no credentials.",
                "API rejects the request with 401 rather than performing the action.")],
        ))

    if "admin-surface" in fired:
        cases.append(TestCase(
            hypothesis="Broken function-level authorization: non-admin reaches an admin operation.",
            category="API5:2023",
            required_accounts=[USER_A, ADMIN],
            steps=[TestStep(
                f"As user_a (non-admin), call {ep.id}.",
                "API returns 403; only admin may perform it.")],
        ))

    if "privileged-field" in fired:
        cases.append(TestCase(
            hypothesis="Mass assignment: client-supplied privileged fields are honored.",
            category="API6:2023",
            required_accounts=[USER_A],
            steps=[TestStep(
                f"As user_a, submit {ep.id} including a privileged field the client shouldn't set.",
                "API ignores the field; privilege/ownership is unchanged.")],
        ))

    if "payment" in fired and ep.method in ("POST", "PUT", "PATCH"):
        cases.append(TestCase(
            hypothesis="Business-flow / ownership gaps on a money or order operation.",
            category="API3:2023",
            required_accounts=[USER_A, USER_B],
            steps=[TestStep(
                f"As user_a, attempt {ep.id} referencing user_b's order/payment resource.",
                "API blocks cross-account action and validates amounts server-side.")],
        ))

    if not cases:  # generic sensitive-data check
        cases.append(TestCase(
            hypothesis="Excessive data exposure in the response.",
            category="API3:2023",
            required_accounts=[USER_A],
            steps=[TestStep(
                f"As user_a, call {ep.id} and inspect the response body.",
                "Only fields the caller is entitled to appear; no secrets/PII of others.")],
        ))
    return cases


def plan_endpoint(ep: Endpoint, signals: list[Signal], risk: str) -> EndpointPlan:
    fired = {s.rule for s in signals}
    notes = "; ".join(dict.fromkeys(s.detail for s in signals))
    reason = f"Flagged by deterministic rules ({notes})." if notes else "Flagged for review."
    return EndpointPlan(ep.id, ep.method, ep.path, risk, reason, signals,
                        _templates(ep, fired))
