<<<<<<< HEAD
# SentinelAPI Frontend

A frontend-only React/Vite portal for the SentinelAPI hackathon project.

## Included
- Dashboard/security overview
- OpenAPI/Swagger upload UI
- Scan configuration UI
- Findings with severity, evidence, PoC and remediation
- Attack surface endpoint view
- Resource relationship visualization
- Scan history
- CI/CD security gate mock UI
- Responsive layout
- Mock data only — no backend/API calls yet

## Run

```bash
npm install
npm run dev
```

Then open the Vite local URL.

## Next backend integration
Replace the mock data/actions in `src/main.jsx` with:
- POST /scan
- GET /scan/:id
- GET /findings
- GET /findings/:id
- POST /findings/:id/retest
- POST /upload/openapi
=======
# SentinelAPI

A **defensive** API security scanner. It reads an OpenAPI/Swagger spec, builds a
normalized endpoint inventory, and plans authorized security tests. It only ever
targets sandboxes you own and control.

```
OpenAPI → Ingest → Normalize → Inventory → Test Planner → (Phase 3: Executor)
```

## Status

- **Phase 1 — Spec Ingest + Normalizer** ✅
- **Phase 2 — Test Planner** ✅
- Phase 3 — Sandbox Executor — not built. Planning produces documents only;
  nothing is sent to any target.

## Install & run

```bash
pip install -r requirements.txt
pytest -q                     # 19 tests
uvicorn app:app --reload      # web UI at http://localhost:8000
```

CLI:

```bash
python cli.py samples/vuln_api.yaml            # inventory JSON
python cli.py samples/vuln_api.yaml --plan     # + test plan (uses LLM if ANTHROPIC_API_KEY set)
python cli.py samples/vuln_api.yaml --plan --no-llm
```

## Layout

```
sentinel/
  ingest.py       Phase 1 · load + validate JSON/YAML (raises SpecError)
  normalize.py    Phase 1 · OpenAPI 3.x / Swagger 2.0 → Inventory, $ref resolver
  models.py       Phase 1 · Endpoint / Param / Inventory
  store.py        SQLite persistence
  planner/
    rules.py      Phase 2 · deterministic sensitivity heuristics (no LLM)
    llm.py        Phase 2 · LLM reasoning layer (optional; needs ANTHROPIC_API_KEY)
    fallback.py   Phase 2 · templated planner used when LLM is unavailable
    planner.py    Phase 2 · orchestrator  build_plan(inventory) → TestPlan
    models.py     Phase 2 · TestPlan / EndpointPlan / TestCase / TestStep / Account
app.py            FastAPI: upload, inventory, and POST /specs/{id}/plan
cli.py            command-line entry point
samples/          intentionally vulnerable spec for local testing
```

## Design notes

- **Deterministic rules and LLM reasoning are separate.** `rules.py` is pure and
  reproducible; the LLM only reasons on top of its signals and never affects the
  evidence. If the LLM call fails, the orchestrator catches it and falls back to
  templated cases, so the pipeline always yields a plan.
- **Plans describe verification, not attacks.** Each test case states a
  hypothesis, the OWASP API Top-10 category, the accounts needed, and steps
  phrased as checks ("confirm user_a cannot read user_b's record") with the
  expected secure behavior. No payloads; `scope: authorized-sandbox-only`,
  `executed: false`.
- **Phase 2 consumes only the normalized model**, so the planner is decoupled
  from spec-format quirks.

## API

| Method | Route | Purpose |
|--------|-------|---------|
| POST | `/specs` | upload a spec → stored inventory |
| GET  | `/specs` | list stored inventories |
| GET  | `/specs/{id}` | fetch one inventory |
| POST | `/specs/{id}/plan?use_llm=true` | build a test plan (Phase 2) |
```
>>>>>>> 65a5e744a3c88da167352d310b70fcf1c11ce115
