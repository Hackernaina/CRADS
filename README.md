# SentinelAPI

SentinelAPI is a defensive API security scanner. It ingests OpenAPI 3.x and
Swagger 2.0 JSON/YAML specifications, builds a normalized endpoint inventory,
and plans authorized security checks. Phase 3 execution is not implemented:
the planner only produces documentation and never sends requests to a target.

## Frontend

The React/Vite dashboard currently uses mock data and mock upload actions. It
does not call the FastAPI backend yet.

```bash
npm install
npm run dev
```

Open the printed Vite URL, usually `http://127.0.0.1:5173/`.

## Backend

Install Python dependencies and run the API separately:

```bash
python3 -m pip install -r requirements.txt
python3 -m pytest -q
uvicorn app:app --reload --port 8000
```

The backend UI is available at `http://127.0.0.1:8000/`.

## CLI

```bash
python cli.py samples/vuln_api.yaml
python cli.py samples/vuln_api.yaml --plan --no-llm
```

The first command prints the normalized inventory. The second creates a
deterministic Phase 2 test plan without requiring an LLM API key.

## API

| Method | Route | Purpose |
|--------|-------|---------|
| POST | `/specs` | Upload a JSON/YAML spec and store its inventory |
| GET | `/specs` | List stored inventories |
| GET | `/specs/{id}` | Fetch one inventory |
| POST | `/specs/{id}/plan?use_llm=false` | Build a deterministic test plan |

Example upload:

```bash
curl -F "file=@samples/vuln_api.yaml" http://127.0.0.1:8000/specs
```

The normalized model preserves endpoint metadata, parameters, security,
request/response media types, schemas, examples, and local `$ref` resolution
warnings. Invalid or unsupported specifications return explicit errors.
