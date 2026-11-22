## Phase 4B.2: Containers, CI and connector registry

The **local-only full stack** is now defined in `compose.full.yaml` (PostgreSQL, migrations, FastAPI, React/Nginx):

```powershell
docker compose -f compose.full.yaml up -d --build
```

Browse `http://127.0.0.1:8080`. Keep your existing root `.env` file. The original `compose.yaml` remains database-only. The authenticated organisation workspace includes a **metadata-only** connector catalogue, with no credential entry or live connections. Read [Phase 4B.2 deployment and security notes](docs/phase4b2-deployment-connectors.md) before running this stack, especially if you already have PostgreSQL volumes or an existing `.env`.

# OpsIntelligence

OpsIntelligence is an operations command centre for a fictional logistics and supply-chain company.

The project explores how a single application can help operations teams understand delivery performance, investigate delays, monitor inventory, and make decisions based on operational evidence. Those capabilities will be introduced incrementally. The current implementation establishes the application’s local development foundation.

The frontend uses React and TypeScript. The backend uses FastAPI, with PostgreSQL providing persistent storage. The application runs locally without cloud accounts, paid API keys, or a live language model.

> **Project status:** Phase 1 is being completed. The application shell, API health and readiness endpoints, PostgreSQL connection, migration baseline, and initial automated tests are working. Business workflows, operational dashboards, data pipelines, and machine learning are not implemented yet.

## Why I’m building this

I’m building OpsIntelligence as a portfolio project to develop practical experience across full-stack development, databases, cloud engineering, data engineering, and applied AI.

The aim is to understand the engineering decisions as well as write the code: how the frontend communicates with the backend, how database changes are managed, how failures are handled, and how tests make changes easier to review.

The project uses a modular monorepo and a single backend application. This keeps the architecture understandable while leaving room to add capabilities without splitting the application into separate services prematurely.

## What works today

The current implementation includes:

- A responsive application shell with a desktop sidebar and mobile navigation menu.
- A welcome screen styled with shared Tailwind design tokens.
- A live API connection card with loading, connected, and unavailable states.
- A retry action that checks the backend again without reloading the page.
- A FastAPI application with environment-based configuration.
- Separate endpoints for process health and database readiness.
- PostgreSQL 16 running through Docker Compose.
- Persistent database storage in a Docker-managed volume.
- SQLAlchemy engine management tied to the application lifecycle.
- An empty Alembic baseline migration.
- Structured JSON application logs.
- Backend tests for health and database readiness behaviour.
- Frontend tests for API connection success, failure, invalid responses, and retry.
- ESLint, Prettier, Ruff, and TypeScript build checks.

The welcome screen does not display fabricated operational metrics. Orders, shipments, inventory, warehouses, predictions, and recommendations will be added in later phases.

All future example operational data must be synthetic or obtained from legally reusable public datasets.

## Technology choices

| Area | Technology | Purpose |
| --- | --- | --- |
| Frontend | React and TypeScript | Component-based interface with static type checking |
| Development server and build | Vite | Local frontend development and production builds |
| Styling | Tailwind CSS v4 | Shared design tokens and utility-based styling |
| Frontend requests | Fetch API | Calls the backend without an additional HTTP client dependency |
| Frontend tests | Vitest and Testing Library | Tests user-visible component behaviour |
| Frontend quality | ESLint and Prettier | Linting and consistent formatting |
| Backend | Python and FastAPI | Typed HTTP API and generated API documentation |
| Configuration and validation | Pydantic and pydantic-settings | Validates application settings and response models |
| Database access | SQLAlchemy 2.x and psycopg | PostgreSQL connectivity and persistence foundation |
| Database migrations | Alembic | Versioned database schema changes |
| Database | PostgreSQL 16 | Relational storage |
| Local infrastructure | Docker Compose | Runs PostgreSQL with persistent storage and a health check |
| Backend tests | pytest | API and readiness tests |
| Backend quality | Ruff | Python linting and formatting |

There is no router or state-management library at this stage because the application currently has one page. Additional dependencies should solve an actual requirement rather than be added in anticipation of one.

## How the application fits together

Three processes run during local development:

```text
Browser
  |
  | Opens the React application
  v
Vite frontend — http://127.0.0.1:5173
  |
  | GET /api/v1/health
  v
FastAPI backend — http://127.0.0.1:8000
  |
  | SQLAlchemy + psycopg
  v
PostgreSQL — localhost:55432
  |
  v
Docker-managed database volume
```

The frontend and backend run directly on the development machine. PostgreSQL runs inside a Docker container.

The browser communicates with FastAPI over HTTP. FastAPI owns the database connection. Database credentials are never needed by the frontend.

PostgreSQL listens on port `5432` inside its container. Docker exposes that container port as `55432` on the development machine. This project uses `55432` because binding to the default host port `5432` failed during Windows setup.

## Repository layout

```text
opsintelligence/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── health.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── logging.py
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   └── session.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   └── readiness.py
│   │   └── main.py
│   ├── tests/
│   │   └── test_health.py
│   ├── alembic/
│   │   ├── versions/
│   │   │   └── 0001_baseline.py
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── .env.example
│   ├── alembic.ini
│   ├── pyproject.toml
│   └── requirements-dev-windows.lock
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── layout/
│   │   │       ├── AppShell.tsx
│   │   │       ├── ApiStatus.tsx
│   │   │       └── ApiStatus.test.tsx
│   │   ├── test/
│   │   │   └── setup.ts
│   │   ├── App.tsx
│   │   ├── index.css
│   │   └── main.tsx
│   ├── .env.example
│   ├── .prettierignore
│   ├── .prettierrc.json
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.ts
├── docs/
├── .github/
├── .env.example
├── .gitignore
├── compose.yaml
└── README.md
```

Generated folders such as `.venv`, `node_modules`, `dist`, and Python caches are omitted from this tree.

The `models` and `schemas` directories are reserved for the next stages of development. The current health response models are defined in `api/health.py`.

### Backend responsibilities

- `api` defines HTTP routes, response contracts, and request dependencies.
- `core` contains shared configuration and logging.
- `db` owns the database engine and SQLAlchemy model metadata.
- `services` contains work performed by the application, starting with the database connectivity query.
- `models` will contain persisted business entities.
- `schemas` will contain business request and response models.
- `main.py` assembles the application and manages startup and shutdown.

This separation keeps HTTP handling, application work, and database setup from becoming mixed together as the project grows.

## Prerequisites

The local setup requires:

- Python 3.13 for the documented Windows dependency snapshot.
- Node.js 22.12 or newer; Node 24 is used in the current Windows setup.
- npm.
- Git.
- Docker Desktop or another compatible Docker engine with Docker Compose.
- A running Linux-container engine.

VS Code is the editor used in the setup instructions, but it is not required to run the application.

The backend declares Python 3.12 or newer. The current Windows installation has been exercised with Python 3.13.5; the Windows dependency snapshot should not be treated as a verified lockfile for every Python version or operating system.

Check the tools from PowerShell:

```powershell
py --list
node --version
npm --version
git --version
docker --version
docker compose version
docker info
```

`docker --version` only confirms that the Docker client is installed. `docker info` must also return server information before containers can start.

## Configuration

There are three local environment files. Each has a different purpose.

| File | Used by | Contains |
| --- | --- | --- |
| `.env` | Docker Compose | PostgreSQL user, password, database name, and published host port |
| `backend/.env` | FastAPI and Alembic | Application name, database URL, and permitted frontend origins |
| `frontend/.env` | Vite | Public backend API address |

Real `.env` files are excluded from Git. The `.env.example` files document the required configuration and must contain placeholders rather than real credentials.

### Root environment

Create a root `.env` using `.env.example` as the starting point:

```dotenv
POSTGRES_USER=opsintelligence
POSTGRES_PASSWORD=replace-with-a-unique-local-password
POSTGRES_DB=opsintelligence
POSTGRES_PORT=55432
```

The password is for local development and should be unique to this project.

### Backend environment

Create `backend/.env`:

```dotenv
APP_NAME=OpsIntelligence
DATABASE_URL=postgresql+psycopg://opsintelligence:URL_ENCODED_PASSWORD@localhost:55432/opsintelligence
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
```

Replace `URL_ENCODED_PASSWORD` with the URL-encoded form of the password configured for PostgreSQL.

The database user, password, database name, and host port must agree with the root environment configuration.

If a password contains symbols, encode only the password when placing it in `DATABASE_URL`. Keep the original password in the root `.env`.

This command prompts for the password without echoing the input, then prints its encoded form:

```powershell
py -3.13 -c "from getpass import getpass; from urllib.parse import quote; print(quote(getpass('Database password (hidden): '), safe=''))"
```

The printed result is still a credential. Do not share it or include it in screenshots.

If the raw password contains `$`, use a single-quoted value in the root Compose `.env` so Compose treats it literally:

```dotenv
POSTGRES_PASSWORD='your-original-password'
```

The surrounding quotes are configuration syntax and are not part of the password.

### Frontend environment

Create `frontend/.env`:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Vite exposes variables prefixed with `VITE_` to browser code. Never put database passwords, private tokens, or other secrets in those variables.

Restart the Vite development server after changing its environment file.

## First-time installation

These instructions are for a fresh local copy of the repository. If the application is already configured and running, skip to “Running the application” rather than replacing existing environment files.

Open PowerShell in the repository root.

### 1. Create the local environment files

```powershell
Copy-Item .env.example .env
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
```

Edit the copied files using the configuration described above. Confirm the published database port and backend URL both use `55432`.

Do not run these copy commands over an existing configured installation unless you intend to replace its settings.

### 2. Start PostgreSQL

Start Docker Desktop and wait for the engine to run, then execute:

```powershell
docker compose up -d --wait
docker compose ps
```

The database service should report `healthy`.

### 3. Create the Python environment and install dependencies

```powershell
Set-Location backend

py -3.13 -m venv .venv

.\.venv\Scripts\python.exe -m pip install -r requirements-dev-windows.lock
.\.venv\Scripts\python.exe -m pip install --no-deps -e ".[dev]"
.\.venv\Scripts\python.exe -m pip check
```

The first installation command uses the recorded Windows dependency versions. The second registers the local backend package in editable mode without resolving those dependencies again.

The final command should report:

```text
No broken requirements found.
```

For a different operating system, resolve dependencies from `pyproject.toml` and verify that environment separately.

### 4. Apply migrations

While still inside `backend`:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
```

The current baseline should be:

```text
0001 (head)
```

The baseline contains no business tables. Alembic creates its own version-tracking table to record which migrations have been applied.

### 5. Install frontend dependencies

```powershell
Set-Location ../frontend
npm ci
```

Use `npm ci` for an existing checkout with a committed lockfile. It installs the versions recorded in `package-lock.json`.

## Running the application

Keep PostgreSQL, FastAPI, and Vite running while using the application.

### Database

From the repository root:

```powershell
docker compose up -d --wait
```

Docker runs the database in the background, so this terminal does not need to stay occupied.

### Backend terminal

Open a terminal in `backend`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8000
```

Wait for:

```text
Application startup complete.
```

Leave this terminal running. The `--reload` option restarts the application when Python source files change.

### Frontend terminal

Open another terminal in `frontend`:

```powershell
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

The page should show the application shell and an API connection card. With FastAPI running, the card should change from “Checking connection” to “Backend connected”.

The frontend uses a strict development port. If port `5173` is already occupied, Vite reports an error instead of silently choosing a different address.

### Optional virtual environment activation

The commands above call the virtual environment’s Python executable directly, so activation is not required.

To activate it manually from `backend`:

```powershell
.\.venv\Scripts\Activate.ps1
```

The prompt should then begin with `(.venv)`.

To confirm the interpreter:

```powershell
python -c "import sys; print(sys.executable)"
```

The path should end with:

```text
backend\.venv\Scripts\python.exe
```

## API endpoints

Interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

### Process health

```http
GET /api/v1/health
```

Successful response:

```json
{
  "status": "healthy"
}
```

This endpoint confirms that FastAPI can answer a request. It does not connect to PostgreSQL.

### Database readiness

```http
GET /api/v1/ready
```

Successful response:

```json
{
  "status": "ready",
  "database": "connected"
}
```

The readiness check obtains a database connection and executes `SELECT 1`.

If the database cannot be reached, it returns HTTP `503`:

```json
{
  "status": "unavailable",
  "database": "unavailable"
}
```

Readiness confirms connectivity. It does not verify migration currency, business data quality, or the health of future integrations.

You can check both endpoints from PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
Invoke-RestMethod http://127.0.0.1:8000/api/v1/ready
```

## Testing and code quality

Use a separate terminal for checks so the application servers can keep running.

### Backend

Run from `backend`:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
```

To apply Python formatting:

```powershell
.\.venv\Scripts\python.exe -m ruff format .
```

The current three backend tests cover:

1. Process health without a database dependency.
2. Successful database readiness.
3. Failed database readiness returning `503`, while process health remains available.

The tests substitute a fake database engine. They do not require Docker or a running PostgreSQL instance. Live connectivity has been checked separately through the readiness endpoint.

### Frontend

Run from `frontend`:

```powershell
npm run format:check
npm run lint
npm run build
npm test
```

To apply formatting:

```powershell
npm run format
```

For tests that rerun as files change:

```powershell
npm run test:watch
```

The current five frontend tests cover:

1. A healthy API response.
2. A failed network request.
3. Successful retry after failure.
4. An unsuccessful HTTP response.
5. A response that does not match the expected health contract.

These tests simulate Fetch responses in a browser-like test environment. They do not require the backend or database.

A passing production build confirms TypeScript compilation and frontend bundling. It does not replace browser testing, accessibility checks, or backend integration testing.

## Checking failure and recovery manually

The API status card has been checked against a running local backend and a stopped backend.

To repeat that check:

1. Keep Vite and PostgreSQL running.
2. Stop FastAPI with Ctrl+C in its terminal.
3. Select “Check again” on the page.
4. Confirm the card shows “Backend unavailable”.
5. Restart FastAPI.
6. Select “Check again”.
7. Confirm the card returns to “Backend connected”.

The frontend gives the health request five seconds before aborting it. It also cancels the request when the component unmounts.

A connected API status does not mean the database is ready. Use `/api/v1/ready` for that separate check.

## Logging

Application logs are written as JSON with these fields:

- `timestamp`
- `level`
- `logger`
- `message`

The application records startup, shutdown, and failed database readiness checks.

Database exception details are intentionally excluded from readiness logs because connection errors can contain credentials or other connection information.

Uvicorn maintains its own server and access logs, which currently retain Uvicorn’s standard format.

## Database migrations

Alembic tracks database changes in:

```text
backend/alembic/versions/
```

Run migration commands from `backend` so the application loads the correct `.env`.

Apply pending migrations:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Inspect the current database revision:

```powershell
.\.venv\Scripts\python.exe -m alembic current
```

Inspect migration history:

```powershell
.\.venv\Scripts\python.exe -m alembic history
```

Future business models must be registered with the shared SQLAlchemy metadata before generating migrations. Generated migration files must be reviewed before they are applied.

The application does not create business tables automatically at startup.

## Dependency maintenance

Frontend dependency versions are recorded in `frontend/package-lock.json`.

Backend dependency constraints are declared in `backend/pyproject.toml`. The current Windows environment is recorded in `backend/requirements-dev-windows.lock`.

After an intentional backend dependency update, regenerate the Windows snapshot from the tested environment:

```powershell
.\.venv\Scripts\python.exe -m pip freeze --exclude opsintelligence-backend |
    Set-Content -Encoding ascii requirements-dev-windows.lock
```

This is an exact-version snapshot, not a hash-verified or cross-platform lockfile.

### Temporary minimatch override

During frontend setup, npm reported a moderate denial-of-service advisory affecting `minimatch` through the TypeScript ESLint dependency chain.

The installed TypeScript ESLint release requested `minimatch` 10.x. A targeted override was added to use `minimatch` 11.0.8 instead.

After rebuilding the dependency tree:

- npm reported zero vulnerabilities at that point in time.
- The dependency tree resolved to the overridden version.
- ESLint passed.
- The production build passed.

The override crosses a major version and should be revisited when TypeScript ESLint adopts a patched dependency range upstream. Passing the current checks supports this setup, but does not guarantee compatibility with every future linting configuration.

Do not remove the override or apply `npm audit fix --force` without reviewing the resulting dependency changes.

Audit results change as new advisories are published. Recheck with:

```powershell
npm audit
```

## Stopping local services

Stop the frontend and backend by pressing Ctrl+C in each server terminal.

From the repository root, stop PostgreSQL with:

```powershell
docker compose down
```

The database volume is retained, so data survives normal container shutdown and recreation.

Adding `--volumes` removes the project’s database volume. That is a destructive reset and is not part of the normal shutdown procedure.

Changing `POSTGRES_PASSWORD` in `.env` does not change the password stored in an already-initialised PostgreSQL volume. Existing database credentials must be changed through PostgreSQL or handled through a deliberate reset.

## Troubleshooting

### Docker reports that the Linux engine pipe cannot be found

The Docker client is installed, but its engine is not available.

Open Docker Desktop, wait for “Engine running”, and retry:

```powershell
docker info
```

### Docker cannot bind to port 5432

Another service may be using the port, or Windows may have reserved it.

This project uses host port `55432`. Check that the root `.env` contains:

```dotenv
POSTGRES_PORT=55432
```

The backend database URL must use the same host port.

### Compose says “volumes must be a mapping”

Check the indentation in `compose.yaml`.

The top-level volume declaration should be:

```yaml
volumes:
  postgres_data: {}
```

The top-level `volumes:` starts at the far left. It is separate from the database service’s volume mount.

Validate the file without printing resolved environment values:

```powershell
docker compose config --quiet
```

### FastAPI cannot find configuration

Start backend commands from the `backend` directory.

The configured `.env` path is relative to the working directory. Starting from the repository root may load the wrong file or leave required settings missing.

### The API card says “Backend unavailable”

Check:

1. FastAPI is running on port `8000`.
2. `frontend/.env` points to that API address.
3. The browser origin is included in `CORS_ORIGINS`.
4. Vite was restarted after changing frontend environment variables.
5. `/api/v1/health` responds directly in the browser.

A frontend running on `127.0.0.1` and one running on `localhost` have different origins. Both are included in the documented development configuration.

### Vite cannot resolve a component import

Check the actual file location against the import.

For the current layout:

```tsx
import { AppShell } from './components/layout/AppShell'
import { ApiStatus } from './components/layout/ApiStatus'
```

File names and capitalisation must match. A path that works on Windows can still fail on a case-sensitive deployment filesystem if the capitalisation differs.

### VS Code shows folders together, such as components/layout

VS Code can compact nested folders into one Explorer row when each folder has only one child directory.

The row represents a directory hierarchy, not a single folder whose name contains a slash.

When creating a file inside `src`, use a path relative to `src`. For example:

```text
components/layout/AppShell.tsx
```

Do not enter `frontend/src` again inside the existing `src` folder.

### Project files appear inside .venv

The `.venv` directory contains installed tools and libraries. Application code and migration configuration belong outside it.

The correct migration locations are:

```text
backend/alembic.ini
backend/alembic/env.py
backend/alembic/versions/
```

Do not edit the installed Alembic package under `.venv/Lib/site-packages`.

### Backend tests show an HTTPX deprecation warning

The current Starlette test client emits a warning that its HTTPX integration is deprecated and recommends HTTPX2.

The current backend tests pass with this warning. It remains an open dependency-maintenance item; the warning has not been suppressed.

### PowerShell shows >> before pasted commands

PowerShell may display continuation prompts while accepting multiline input.

If it appears to be waiting because a quote or bracket was left open, press Ctrl+C and retry the complete command.

Run development checks in a separate terminal that has an available PowerShell prompt. A terminal currently running FastAPI or Vite is occupied by that process.

## Configuration and repository safety

The repository excludes:

- Real `.env` files.
- Python virtual environments.
- Installed frontend dependencies.
- Build output.
- Python caches.
- Test and lint caches.
- Generated package metadata.

Before staging files, review:

```powershell
git status --short
git check-ignore .env backend/.env frontend/.env backend/.venv frontend/node_modules
```

Environment examples should contain placeholders. Database credentials, encoded passwords, and private tokens must not appear in source files, screenshots, or documentation.

CORS controls which browser origins can read API responses. It is not authentication or authorisation.

The current application has no user accounts and is intended for local development. Authentication and deployment security need explicit design before the application is exposed beyond that environment.

## Budget and deployment

The project has a maximum budget of $0 AUD.

The local stack does not require:

- Paid cloud resources.
- Paid API subscriptions.
- Purchased domains.
- Cloud database accounts.
- A hosted language model.

Cloudflare Pages, Render, and Supabase are provisional deployment options. Their current free-tier terms, resource limits, and account requirements must be verified at deployment time.

No external deployment is part of the current setup. Deployment requires a separate review and explicit approval.

## What comes next

The planned development sequence is:

1. Application foundation.
2. Operational domain models and synthetic data.
3. Operational visibility and dashboards.
4. Data engineering and validated imports.
5. Delivery-delay prediction.
6. Evidence-based recommendations and decision support.
7. Hardening, CI, and an explicitly approved deployment.

Only Phase 1 is currently in scope.

Before marking Phase 1 complete, the remaining review includes checking strict TypeScript configuration, exercising mobile and keyboard navigation, completing the architecture and development-plan documents, and confirming the final repository contents.

The current implementation is a working local foundation. It should not yet be described as a production deployment or a finished operations platform.
## Phase 4 — Industry & Scenario Studio

The Dashboard includes **Industry & scenarios** and **Data connections** sections. The new local APIs support industry/KPI discovery, scenario configuration validation, and bounded CSV schema preview. Industry detection is tentative and requires human confirmation. **Only warehouse logistics has a real solver.** For API-key, database and MCP integrations, the UI deliberately shows security prerequisites instead of accepting credentials in an unauthenticated demo. Read `docs/phase4-decision-workspace.md` before attempting company data connections.

## Phase 4A: Industry contracts and registry (new)

The decision workspace now reads a versioned industry registry and displays detailed
Technology, Agriculture/AgriTech, and Logistics data contracts. Additional industry
families are explicitly marked catalogue-only; they do not have executable solvers.
The shared `/api/v1/workspace/decision/validate` contract checks sub-industry,
objective, metric units, and duplicate constraints without executing optimisation.
See [`docs/phase4a-industry-registry.md`](docs/phase4a-industry-registry.md) for API
examples, acceptance criteria, AgriTech capstone integration prerequisites and
security limits. No API keys or confidential company data are accepted in this phase.

## Phase 4B.1 — Local organisation security prototype

New authenticated organisations, member roles and tenant-scoped project metadata are available at `#enterprise-workspace`. Read [Phase 4B.1 identity setup and limitations](docs/phase4b1-identity.md) before using the feature. The original warehouse and industry demonstration endpoints remain shared and synthetic; **do not upload confidential company data or real API/MCP keys**.

### Phase 4B.3 — Connector governance update

See [`docs/phase4b3-connector-governance.md`](docs/phase4b3-connector-governance.md) for additive migration `0005`, audited connector metadata review, role restrictions, sidebar navigation and smoke-test commands. **Live database and cloud connections, real credential storage and enterprise data ingestion are not enabled.**


## Phase 4C: opt-in read-only PostgreSQL synthetic-data preview

See [Phase 4C connector boundaries and operator setup](docs/phase4c-readonly-postgres.md). Off by default. Requires approved metadata, exact organisation/connector provisioning and a restricted synthetic database account. No arbitrary SQL, credentials in UI, or live enterprise integration claims.


## Multi-industry mathematical pilot (Phase 4C.2)

Three bounded, reproducible assignment MILPs for Logistics, Agriculture and Technology are available in **Industry solver lab**. All built-in values are **synthetic assumptions**, not sourced company measurements, and no live company uploads are authorised. See [model equations, reproducibility and dataset research](docs/phase4c2-industry-pilots.md) and the [example CSVs](examples/industry-pilots/). Existing warehouse optimisation remains unchanged.
