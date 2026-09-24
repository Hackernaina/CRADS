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
