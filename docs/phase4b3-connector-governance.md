# Phase 4B.3 — Audited connector metadata governance

This is a **safe, non-executable connector governance milestone**. It is not a credential vault, SQL execution service, data ingestion engine, cloud provider integration, or production-ready identity service.

## Changes

- Organisation-scoped connector purpose and data classification (`public`, `internal`, `confidential`, `restricted`).
- Explicit metadata lifecycle: `not_configured` → `pending_review` → `metadata_approved` → `disabled`. An administrator/owner may request review, **only an owner may approve metadata**, and an administrator/owner may disable or delete. Invalid transitions are rejected with HTTP 409.
- Every successful transition is committed with an organisation-scoped audit event. Audit panel can refresh, and connector actions automatically refresh it.
- UI highlights the hash-selected navigation link instead of always selecting Overview.
- CORS now permits DELETE for administrative metadata deletion, retaining API authorisation checks.
- Regression tests for owner approval, unauthorised viewers, cross-tenant attempts, forbidden credential/host parameters, invalid transitions and audit persistence.
- CI checks both upgrade and rollback of the latest database migration.

## New database migration

`backend/alembic/versions/0005_connector_governance.py` adds four fields to `enterprise_connectors` while retaining old rows:

| Column | Purpose |
| --- | --- |
| `purpose` | Non-secret justification for registering this data source |
| `data_classification` | Data sensitivity label; **not an enforcement mechanism** |
| `reviewed_by` | User ID who approved metadata, nullable |
| `reviewed_at` | UTC timestamp of metadata approval, nullable |

Existing connectors receive default `purpose='Existing demonstration connector'` and `data_classification='internal'`. **These values are defaults, not discovered facts.** Owners should verify them before any future connection is enabled. Data and Docker volumes are not deleted by running Alembic upgrade.

## Permissions

| Role | List | Register / request review | Approve metadata | Disable / delete | Audit |
| --- | --- | --- | --- | --- | --- |
| Viewer / analyst | yes | no | no | no | no |
| Admin | yes | yes | no | yes | yes |
| Owner | yes | yes | yes | yes | yes |

Unrelated organisations receive 404 to avoid enumerating other tenants. Status changes are not data-plane privileges. All provider definitions continue reporting `execution_supported=false` and `credentials_supported=false`, including approved records.

## Local validation (Windows PowerShell)

```powershell
cd C:\Users\Lenny\Documents\opsintelligence\backend
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m pytest -q

cd ..\frontend
npm ci
npm run build
npm test

cd ..
docker compose -f compose.full.yaml build
docker compose -f compose.full.yaml up -d
docker compose -f compose.full.yaml ps -a
Invoke-RestMethod http://127.0.0.1:8080/api/v1/health
```

Do **not** run `docker compose down -v`, paste secrets into registry fields, or make the database publicly accessible. In a Docker-only setup, Compose's migration service applies migration `0005` before backend startup. For a working running Compose stack, taking a PostgreSQL backup before migrating remains strongly recommended.

## Outstanding production security work

- Replace bearer-in-memory local identity with a production-reviewed identity provider/session design and CSRF protection as appropriate.
- Store credentials only in a supported secret manager; use short-lived workload identity wherever possible.
- Require scoped read-only database principals, explicit host allowlists and network egress policy; never execute user-provided SQL without strict policy.
- Bind approved metadata to a separate, auditable connection authorisation gate with least privilege and explicit environment approvals.
- Incorporate document evidence validation, provenance, data retention controls, and tenant-isolated operational datasets.
- Review security logging retention/tamper resistance, migration rollbacks, and permission/role reassignment.

`metadata_approved` **never means live/connected**. The product remains a local synthetic demonstration environment.
