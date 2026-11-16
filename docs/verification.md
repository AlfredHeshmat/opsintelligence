# Phase 1 verification

These results describe the local Windows setup. They record checks performed
during development rather than claiming that the application is ready for
production deployment.

## Local environment

- Python 3.13.5.
- Node.js 24.7.0 and npm 11.6.2.
- Git available and the local repository initialised.
- Docker engine running.
- PostgreSQL 16 running through Docker Compose.
- Published database address: localhost:55432.

## Application checks

| Check | Result |
| --- | --- |
| PostgreSQL container health | Healthy |
| FastAPI startup | Successful |
| GET /api/v1/health | Returned healthy |
| GET /api/v1/ready | Returned ready and database connected |
| Alembic baseline | Applied; current revision is 0001 (head) |
| Frontend startup | Successful |
| Browser-to-API communication | Backend connected displayed |
| Backend unavailable state | Verified after stopping FastAPI |
| Connection recovery | Retry succeeded after restarting FastAPI |
| Mobile navigation | Opening, dismissal, and section navigation verified |
| Keyboard navigation | Visible focus, modal focus cycling, and Escape verified |
| VS Code diagnostics | No problems reported after enabling Tailwind language support |
| Strict TypeScript and production build | Passed |

The readiness endpoint was checked against a live PostgreSQL connection.
Its failure behaviour is covered by automated tests. A live database-outage
exercise has not been recorded for this Windows setup.

## Automated checks

- Backend: 3 tests passed.
- Frontend: 5 tests passed.
- Backend Ruff lint and formatting checks passed.
- Frontend ESLint and production build passed.
- Prettier configuration was moved to the frontend root and formatting rerun.
- npm reported zero vulnerabilities at the last reported dependency installation.

The automated tests use substituted database engines and Fetch responses.
Live connectivity checks complement those tests.

## Configuration and dependencies

Git ignore checks confirmed exclusion of:

- Root, backend, and frontend .env files.
- The backend virtual environment.
- Frontend node_modules.

Frontend versions are recorded in package-lock.json. The backend has an
exact-version Windows dependency snapshot, requirements-dev-windows.lock.

The Windows snapshot is not a cross-platform or hash-verified lockfile.

## Known maintenance items

- Starlette emits a deprecation warning about the HTTPX test-client integration.
  All three backend tests pass with this warning.
- TypeScript ESLint uses a targeted minimatch 11.0.8 override. Linting and
  building passed after applying it. Revisit the override when upstream
  dependencies adopt a patched version range.
- npm audit results describe a point in time and should be checked again
  during dependency updates.

## Scope

No external deployment, paid service, or mandatory language-model integration
was introduced.

Business tables, operational workflows, dashboards, ETL, predictions, and
recommendations remain outside Phase 1.