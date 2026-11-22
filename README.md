# OpsIntelligence

**Operational analytics and constraint-aware decision optimisation.** A reproducible, zero-subscription, local-first full-stack portfolio application built with React/TypeScript, FastAPI, PostgreSQL and open-source mathematical optimisation tools.

> **Release scope:** Portfolio/local prototype using synthetic and hypothetical data. Mathematical optimality means **optimal for the stated mathematical formulation**, not optimal across every real-world business constraint. Enterprise identity, public registration and connector features are **not certified for confidential data or public internet exposure**. There is currently **no public hosted URL**.

## What you can do

| Experience | Capabilities | Source and limits |
| --- | --- | --- |
| **Explore Demo** — no login | Warehouse overview, order exploration, synthetic alerts, delay-model evaluation, MILP warehouse allocation, Monte Carlo scenario comparison, supported industry solver examples | Generated warehouse data and hypothetical model coefficients; not real business outcomes |
| **Enterprise workspace** — local authenticated prototype | Company onboarding, organisations, individual accounts, invitations, role-based access, projects, audit records, connector governance | Local-only demonstration; do not use real company credentials |
| **Private project data** | Validate and import a bounded Logistics CSV, persist project-scoped PostgreSQL records, view KPIs, filter and paginate orders | Up to 2 MB / 2,000 rows and the documented 13-column Logistics format; project/organisation authorization at the API |
| **Project optimisation** | Set handling capacity and assumed defer penalty, solve dispatch/defer MILP, store modelled decisions, provenance and run history | Pending orders only, at most 150 per run; no live routing, inventory or labour feasibility guarantee |

The project is architected for later industry adapters, data connectors, advanced optimisation and integrations. They are not implied to be implemented where they are not.

## Run locally (Docker)

**Requirements:** Docker with Compose, Git and a shell. No external paid API or service is needed.

```powershell
# In the repository root
Copy-Item .env.example .env   # Only if .env does not already exist
# Edit .env, setting a strong, unique local POSTGRES_PASSWORD.
docker compose -f compose.full.yaml up -d --build
docker compose -f compose.full.yaml ps -a
Invoke-RestMethod http://127.0.0.1:8080/api/v1/health
Invoke-RestMethod http://127.0.0.1:8080/api/v1/ready
```

Open **http://127.0.0.1:8080**. The database and backend should be `healthy`, frontend `Up`, and the one-time migration task `Exited (0)`.

**Preserve your data:** The named PostgreSQL volume is persistent. Never run `docker compose down -v` unless you explicitly intend to destroy the local database. `.env`, database credentials and any session/invitation tokens must not be committed. Demo signup is enabled by the local Compose configuration; turn it off for anything internet-facing.

For development without the full stack, consult [development plan](docs/development-plan.md) and the [architecture notes](docs/architecture.md).

## Guided walkthrough for recruiters

1. Open the app and choose **Explore interactive demo**; no account required.
2. At **Overview**, inspect synthetic KPIs and the interactive trend explorer.
3. At **Operational orders**, filter, sort and export the bounded synthetic preview.
4. At **Optimisation**, choose handling/labour assumptions and examine the certified solver result (when optimal).
5. At **What-if simulator**, compare two scenario settings and read the uncertainty limits.
6. At **Industry solver lab**, review examples for logistics, agriculture and technology.
7. Read [Recruiter demonstration guide](docs/recruiter-demo.md) for the enterprise prototype and mathematical limitations.

The hosted recruiter experience should use **only synthetic data**. Do not publish developer test accounts, invitation codes or an unrestricted company registration flow.

## Architecture

```text
React / TypeScript / Vite  ── Nginx reverse proxy ──┐
                                                    │
                                                 FastAPI
                                               /    |     \
                           Auth + tenancy + audit  |   Solver services
                                            SQLAlchemy   SciPy / HiGHS
                                               |           |
                                               └ PostgreSQL┘
                                               (Docker volume)
```

- `frontend/src/components/layout`: access selection, sidebar, responsive navigation and workflow guidance.
- `frontend/src/components/intelligence`: analytics, projects, connectors, scenarios and optimisation UIs.
- `backend/app/api`: authenticated and demo HTTP endpoints.
- `backend/app/services`: validation, data adapters, decision models and integration services.
- `backend/alembic`: database schema migrations.
- `.github/workflows/ci.yml`: backend tests, frontend build/lint/tests, migrations and Docker smoke tests.

## Quality checks

```powershell
cd frontend
npm ci
npm run lint
npm run build
npm test
cd ..\backend
.\.venv\Scripts\python.exe -m pytest -q
```

For a clean Python environment, install `backend[dev]` following the backend's requirements. CI is authoritative for repeatable Linux checks; local browser/role tests are complementary. An existing Starlette/httpx deprecation warning does not indicate a failing test.

## Security & deployment boundaries

**This is not production-certified enterprise software.** Project membership checks and test coverage are useful protections, but are not independent tenant-security certification. Specifically, email verification, MFA, robust reset/recovery, external threat testing, public-abuse controls and extensive per-project rights remain out of scope. Browser UI hiding is never authorization; the backend enforces access. Existing admin/enterprise workflows must remain closed to unauthenticated public visitors.

For zero-cost deployment strategy, staging gates and exact restrictions, read [Release and free hosting guide](docs/phase4f-release-guide.md). Free service availability, quotas and acceptable-use restrictions must be rechecked at deployment time. Public static demo fallback is allowed only with honest labeling; it must not imply live API execution.

## Further documentation

- [Recruiter demo and storytelling](docs/recruiter-demo.md)
- [Phase 4F release / security checklist](docs/phase4f-release-guide.md)
- [Project optimisation mathematical contract](docs/phase4e-final-optimisation-and-security.md)
- [Private CSV workspace](docs/phase4e2-private-csv-workspace.md)
- [Employee invitations](docs/phase4e3-employee-invitations.md)
- [Earlier development phases](docs/development-plan.md)

**Cost commitment:** No mandatory subscription or paid cloud/API dependencies. Local execution still uses your hardware, electricity and network; a permanent reliable public backend cannot be guaranteed free.
