"""LLM reasoning layer.

Given an endpoint plus the deterministic signals, the LLM explains *why* it is
sensitive and proposes safe verification steps for an authorized review. This
module is optional: if no API key is configured, `plan_endpoint` returns None
and the planner falls back to templated reasoning (fallback.py). Kept strictly
separate from rules.py so the deterministic evidence is never LLM-dependent.
"""
from __future__ import annotations

import json
import os
from typing import Any

from ..models import Endpoint
from .models import Account, EndpointPlan, Signal, TestCase, TestStep

DEFAULT_MODEL = os.getenv("SENTINEL_MODEL", "claude-opus-4-8")

SYSTEM = """You are a defensive API security reviewer helping plan an AUTHORIZED
test against the reviewer's own sandbox. You do NOT execute anything and you do
NOT write exploit payloads. For one endpoint you:
1. Explain in plain language why it is security-sensitive.
2. Map it to the OWASP API Security Top 10 (2023) where relevant.
3. Describe verification steps a tester would perform to confirm the API is
   secure — phrased as checks ("verify that ...", "confirm that ..."), naming
   which test accounts are needed. Steps must be non-destructive and read-only
   where possible.
Return ONLY JSON matching the given schema. No prose outside JSON."""

SCHEMA = {
    "reason": "string",
    "test_cases": [{
        "hypothesis": "what weakness this checks for",
        "category": "OWASP id e.g. API1:2023",
        "required_accounts": [{"role": "string", "purpose": "string"}],
        "steps": [{"action": "verification a tester performs",
                   "expected_secure": "what a secure API should do"}],
    }],
}


def _client():
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return None
    try:
        import anthropic
    except ImportError:
        return None
    return anthropic.Anthropic(api_key=key)


def _endpoint_brief(ep: Endpoint, signals: list[Signal]) -> str:
    return json.dumps({
        "endpoint": ep.id,
        "summary": ep.summary,
        "requires_auth": ep.requires_auth,
        "security": ep.security,
        "params": [{"name": p.name, "in": p.location, "required": p.required} for p in ep.params],
        "request_body": ep.request_body,
        "response_statuses": list(ep.responses),
        "deterministic_signals": [{"rule": s.rule, "detail": s.detail} for s in signals],
    }, default=str)


def plan_endpoint(ep: Endpoint, signals: list[Signal], risk: str,
                  client: Any = None, model: str = DEFAULT_MODEL) -> EndpointPlan | None:
    client = client or _client()
    if client is None:
        return None

    prompt = (f"Endpoint under review:\n{_endpoint_brief(ep, signals)}\n\n"
              f"Return JSON with this shape:\n{json.dumps(SCHEMA)}")
    msg = client.messages.create(
        model=model, max_tokens=1500, system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    data = _extract_json(raw)
    return _to_plan(ep, signals, risk, data)


def _extract_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1].lstrip("json").strip()
    start, end = raw.find("{"), raw.rfind("}")
    return json.loads(raw[start:end + 1])


def _to_plan(ep: Endpoint, signals: list[Signal], risk: str, d: dict) -> EndpointPlan:
    cases = []
    for c in d.get("test_cases", []):
        cases.append(TestCase(
            hypothesis=c.get("hypothesis", ""),
            category=c.get("category", ""),
            required_accounts=[Account(a.get("role", ""), a.get("purpose", ""))
                               for a in c.get("required_accounts", [])],
            steps=[TestStep(s.get("action", ""), s.get("expected_secure", ""))
                   for s in c.get("steps", [])],
        ))
    return EndpointPlan(ep.id, ep.method, ep.path, risk,
                        d.get("reason", ""), signals, cases)
