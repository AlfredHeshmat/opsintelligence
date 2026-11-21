# Phase 4B.2 — reproducible deployment, CI/CD, and safe connector registration

## What this release actually implements

- A full-stack, local Docker Compose deployment (`compose.full.yaml`): PostgreSQL, a one-shot Alembic migration job, the FastAPI backend, and React built into an unprivileged Nginx image.
- Same-origin reverse proxy: the frontend at `http://127.0.0.1:8080` forwards `/api/*` to FastAPI over the private Compose network. Existing Vite development mode still uses port 5173 and the local FastAPI URL.
- GitHub Actions CI: backend regression tests, frontend build/tests, Alembic migration verification against PostgreSQL, and backend/frontend Docker image builds. It does **not** automatically push or deploy images.
- Tenant-scoped, credential-free connector registration, with administrator/owner-only writes, read access for organisation members, audit logging, and strict provider/type validation.
- A connector status panel in the signed-in organisation workspace. No secrets are accepted and **all connector execution is disabled**.

## First-time and existing local installs

**Do not overwrite your original `.env` files or reset PostgreSQL volumes. Back up your existing database before trying a different orchestration method.** Run from the repository root:

```powershell
# Review container configuration without starting it:
docker compose -f compose.full.yaml config --services
# The root .env must provide POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB.
# The existing database volume should already contain your local demo account.
docker compose -f compose.full.yaml up -d --build
# Display status and migration diagnostics:
docker compose -f compose.full.yaml ps
docker compose -f compose.full.yaml logs migrate --tail 80
# Open http://127.0.0.1:8080
```

**Important:** `compose.yaml` remains the original DB-only development definition. Use `-f compose.full.yaml` explicitly for the full-stack deployment. Because both files live in the same folder with the same Compose project name, they may reuse/recreate services and the database volume. Stop the existing frontend/backend development processes before switching modes to avoid confusion; do not use `down -v`.

The full-stack Compose file intentionally only publishes the frontend to the **localhost** interface. The API and PostgreSQL have no published host ports in this deployment. HTTPS, backups, credential rotation, persistent file storage, vault integration, worker scheduling and multi-replica operation are **not implemented** and require a separate production design.

### Local development (unchanged)

```powershell
docker compose up -d db
# backend terminal:
cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8000
# frontend terminal:
cd frontend
npm run dev
```

For Phase 4B.2, the new migration is `0004_connector_registry.py`; install updated Python dependencies before running migrations. If you switch to the full Compose stack, its one-shot migration service upgrades the schema automatically. An existing user account and organisation are retained if the same DB volume is used. Never run the bootstrap script on an already initialised identity database.

## Connector security boundaries

The connector endpoints require a valid bearer session:

- `GET /api/v1/enterprise/connector-types`: public capability metadata, but requires sign-in.
- `GET /api/v1/enterprise/organisations/{id}/connectors`: membership required.
- `POST /api/v1/enterprise/organisations/{id}/connectors`: admin or owner; accepts **only** display_name, kind, provider; extra fields, including passwords and tokens, are rejected.
- `DELETE /api/v1/enterprise/organisations/{id}/connectors/{connector_id}`: admin or owner.

All registrations have `status=not_configured`. No endpoint performs a connection test, network request, secret encryption, credential persistence, live data ingestion or MCP invocation. A real connector requires subsequent vault storage, per-tenant egress policies/SSRF prevention, least-privilege identity, connector-specific permission scopes, timeouts, review workflow and threat-model testing.

The existing warehouse demonstration remains **public synthetic data**. Do **not** connect real company data to the demonstration routes. This release is **not a production-security certification**.

## Verification

- `cd backend; .\.venv\Scripts\python.exe -m pytest -q`
- `cd frontend; npm ci; npm run build; npm test`
- `docker compose -f compose.full.yaml config`
- `docker compose -f compose.full.yaml up --build -d`
- Check `GET http://127.0.0.1:8080/api/v1/health` and `/api/v1/ready`.
- Sign in to Organisation security and confirm connector metadata is listed and tenant scoped. Do not submit credentials.
- Run a PR; review GitHub Actions checks before merging.

## Next gates

1. Production-grade secrets manager with short-lived provider identity and safe network egress.
2. Secure read-only PostgreSQL connector with schema introspection and access review, then MongoDB/cloud adapters.
3. Organisation-scoped datasets and optimisation runs, not only metadata.
4. Image scanning, SBOMs, versioned registry publishing, signature verification, rollout and rollback.
5. Enterprise-grade workload isolation, model provenance, rate limits, pen testing and disaster recovery.
