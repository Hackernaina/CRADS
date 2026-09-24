"""Phase 2 orchestrator: Inventory -> TestPlan.

Pipeline per endpoint:
  rules.evaluate  -> deterministic signals + risk band
  is_candidate?   -> skip low-signal endpoints (recorded in plan.skipped)
  llm.plan_endpoint (if key present) else fallback.plan_endpoint

The plan is a document. Nothing is sent to any target — Phase 3 executes,
and only against authorized sandboxes.
"""
from __future__ import annotations

from ..models import Inventory
from . import fallback, llm, rules
from .models import TestPlan


def build_plan(inv: Inventory, use_llm: bool = True, client=None,
               model: str = llm.DEFAULT_MODEL) -> TestPlan:
    plan = TestPlan(inventory_title=inv.title, model="rules-only")
    active_client = client
    if use_llm and active_client is None:
        active_client = llm._client()
    if active_client is not None:
        plan.model = model

    for ep in inv.endpoints:
        signals = rules.evaluate(ep)
        if not rules.is_candidate(signals):
            plan.skipped.append(ep.id)
            continue
        risk = rules.risk_band(rules.score(signals))

        ep_plan = None
        if active_client is not None:
            try:
                ep_plan = llm.plan_endpoint(ep, signals, risk, client=active_client, model=model)
            except Exception as e:  # network/parse issues never break the pipeline
                plan.warnings.append(f"LLM failed on {ep.id}: {e}; used fallback")
        if ep_plan is None:
            ep_plan = fallback.plan_endpoint(ep, signals, risk)

        plan.endpoints.append(ep_plan)

    plan.endpoints.sort(key=lambda e: {"high": 0, "medium": 1, "low": 2}[e.risk])
    return plan
