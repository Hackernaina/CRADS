"""Deterministic sensitivity heuristics.

Pure functions over the Phase 1 model — no LLM, no network. These flag which
endpoints deserve attention during an authorized security review and why.
The LLM layer (llm.py) reasons on top of these signals; keeping them separate
means the plan is explainable and reproducible even with the LLM turned off.
"""
from __future__ import annotations

import re

from ..models import Endpoint
from .models import Signal

# name-pattern -> (regex, weight, human note)
_PATTERNS: list[tuple[str, str, int, str]] = [
    ("user-or-account", r"user|account|profile|member|customer|\bme\b", 2,
     "operates on user/account resources"),
    ("admin-surface", r"admin|internal|superuser|manage|root", 3,
     "administrative or privileged surface"),
    ("payment", r"pay|billing|invoice|charge|card|wallet|checkout|refund|order", 3,
     "handles money or orders"),
    ("credential", r"login|logout|token|password|otp|session|auth|reset", 2,
     "part of authentication / credential handling"),
    ("data-access", r"file|download|upload|export|report|backup|config|debug", 2,
     "reads or moves data / configuration"),
]

_WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# endpoints expected to be reachable without a session
_PUBLIC_BY_DESIGN = re.compile(r"login|logout|register|signup|sign-up|token|reset|forgot|refresh")


def _has_object_id(ep: Endpoint) -> Signal | None:
    """A path/query id that selects one record is the classic BOLA pivot."""
    for p in ep.params:
        if p.location in ("path", "query") and re.search(r"id$|Id$|_id|uuid|key", p.name):
            return Signal("object-id", f"takes resource identifier '{p.name}' ({p.location})", 2)
    if re.search(r"\{[^}]*(id|Id|uuid)[^}]*\}", ep.path):
        return Signal("object-id", "path contains a resource identifier", 2)
    return None


def _reflective_field(ep: Endpoint) -> Signal | None:
    """Bodies exposing role/privilege fields invite mass-assignment mistakes."""
    body = ep.request_body or {}
    props = ((body.get("schema") or {}).get("properties")) or {}
    hot = [k for k in props if re.search(r"admin|role|is_|permission|owner|balance|price", k)]
    if hot:
        return Signal("privileged-field", f"body accepts privileged field(s): {', '.join(hot)}", 3)
    return None


def evaluate(ep: Endpoint) -> list[Signal]:
    """Return every rule that fired for this endpoint."""
    signals: list[Signal] = []
    haystack = f"{ep.path} {ep.operation_id or ''} {ep.summary} {' '.join(ep.tags)}".lower()

    for name, pat, weight, note in _PATTERNS:
        if re.search(pat, haystack):
            signals.append(Signal(name, note, weight))

    if not ep.requires_auth and not _PUBLIC_BY_DESIGN.search(haystack):
        signals.append(Signal("no-auth", "endpoint requires no authentication", 3))

    if ep.method in _WRITE_METHODS:
        signals.append(Signal("state-changing", f"{ep.method} mutates server state", 1))

    if ep.deprecated:
        signals.append(Signal("deprecated", "marked deprecated but still exposed", 1))

    for maybe in (_has_object_id(ep), _reflective_field(ep)):
        if maybe:
            signals.append(maybe)

    return signals


def score(signals: list[Signal]) -> int:
    return sum(s.weight for s in signals)


def risk_band(total: int) -> str:
    return "high" if total >= 6 else "medium" if total >= 3 else "low"


def is_candidate(signals: list[Signal]) -> bool:
    """Worth showing to the LLM / including in the plan."""
    return score(signals) >= 3
