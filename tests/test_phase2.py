from pathlib import Path

from sentinel import ingest
from sentinel.models import Inventory
from sentinel.planner import build_plan
from sentinel.planner import rules

SAMPLE = (Path(__file__).parent.parent / "samples" / "vuln_api.yaml").read_text()
INV = ingest(SAMPLE)


def plan_for(pid):
    plan = build_plan(INV, use_llm=False)
    return plan, next((e for e in plan.endpoints if e.endpoint == pid), None)


def test_rules_flag_no_auth_admin():
    ep = next(e for e in INV.endpoints if e.id == "DELETE /admin/users")
    fired = {s.rule for s in rules.evaluate(ep)}
    assert {"no-auth", "admin-surface", "state-changing"} <= fired
    assert rules.risk_band(rules.score(rules.evaluate(ep))) == "high"


def test_object_id_detected():
    ep = next(e for e in INV.endpoints if e.id == "GET /users/{userId}")
    assert any(s.rule == "object-id" for s in rules.evaluate(ep))


def test_privileged_field_detected():
    ep = next(e for e in INV.endpoints if e.id == "PUT /users/{userId}")
    assert any(s.rule == "privileged-field" for s in rules.evaluate(ep))


def test_plan_fallback_offline():
    plan, admin = plan_for("DELETE /admin/users")
    assert plan.model == "rules-only" and not plan.executed
    assert plan.scope == "authorized-sandbox-only"
    assert admin and admin.risk == "high"
    # BFLA + no-auth cases present
    cats = {c.category for c in admin.test_cases}
    assert "API5:2023" in cats or "API2:2023" in cats
    assert all(c.required_accounts for c in admin.test_cases)


def test_bola_case_for_id_endpoint():
    _, u = plan_for("GET /users/{userId}")
    assert any(c.category == "API1:2023" for c in u.test_cases)
    roles = {a.role for c in u.test_cases for a in c.required_accounts}
    assert {"user_a", "user_b"} <= roles


def test_low_signal_skipped():
    plan = build_plan(INV, use_llm=False)
    planned = {e.endpoint for e in plan.endpoints}
    assert planned and plan.skipped  # some in, some out
    assert set(plan.skipped).isdisjoint(planned)


def test_roundtrip_from_dict():
    inv2 = Inventory.from_dict(INV.to_dict())
    assert build_plan(inv2, use_llm=False).endpoints


def test_api_plan_route(tmp_path, monkeypatch):
    monkeypatch.setenv("SENTINEL_DB", str(tmp_path / "t.db"))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    import importlib, app
    importlib.reload(app)
    from fastapi.testclient import TestClient
    c = TestClient(app.app)
    sid = c.post("/specs", files={"file": ("s.yaml", SAMPLE)}).json()["id"]
    r = c.post(f"/specs/{sid}/plan?use_llm=false")
    assert r.status_code == 200
    body = r.json()
    assert body["scope"] == "authorized-sandbox-only" and body["endpoints"]
    assert c.post("/specs/nope/plan").status_code == 404
