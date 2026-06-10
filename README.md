# AI PEL Runtime Policy Enforcement Gate

This repository contains the scaffold for a demo Runtime Policy Enforcement Gate for AI agent actions.

## T01 scaffold

The initial scaffold starts three Docker Compose services:

- `app` — FastAPI application exposed on <http://localhost:8080>
- `opa` — Open Policy Agent exposed on <http://localhost:8181>
- `postgres` — Postgres 15 exposed on `localhost:5432`

Run the stack:

```bash
docker compose up --build
```

Check the placeholder page:

```bash
curl http://localhost:8080/
```

Check real dependency connectivity from the app:

```bash
curl http://localhost:8080/health
```

Expected health response when all services are reachable:

```json
{"app":"ok","opa":"ok","db":"ok"}
```
