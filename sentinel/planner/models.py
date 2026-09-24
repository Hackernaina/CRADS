"""Test plan model — the contract Phase 3 (executor) consumes."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Signal:
    """Deterministic rule hit."""
    rule: str
    detail: str
    weight: int


@dataclass
class Account:
    role: str      # e.g. "user_a", "user_b", "admin", "anonymous"
    purpose: str


@dataclass
class TestStep:
    action: str            # what the executor will do (sandbox only)
    expected_secure: str   # what a secure API should return


@dataclass
class TestCase:
    hypothesis: str
    category: str          # OWASP API Top 10 id, e.g. "API1:2023"
    required_accounts: list[Account]
    steps: list[TestStep]


@dataclass
class EndpointPlan:
    endpoint: str          # "METHOD /path"
    method: str
    path: str
    risk: str              # high | medium | low
    reason: str            # LLM explanation
    signals: list[Signal]  # deterministic evidence
    test_cases: list[TestCase]


@dataclass
class TestPlan:
    inventory_title: str
    model: str
    endpoints: list[EndpointPlan] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)   # candidates the LLM judged not sensitive
    warnings: list[str] = field(default_factory=list)
    scope: str = "authorized-sandbox-only"
    executed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
