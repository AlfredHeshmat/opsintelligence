# Phase 4D.2 — Guided analytics and operational data exploration

## Implemented scope

- Added an **Insight → Explore → Optimise → Compare → Extend** workflow guide to the public demo. Links use the existing route hashes; the user can visit any supported section in any order.
- Replaced the static overview volume bars with `TrendExplorer`: switch between recorded orders and recorded delays, adjust the last 7/14/30 available dates, inspect a selected day, and read period totals and peak counts. All values come from the existing synthetic `operations/overview` response, without interpolation or fabricated data.
- Replaced the static orders table with `OrdersExplorer`: client-side search, status filter, column sorting, 10-row pagination, filter reset, CSV export of **only the currently filtered loaded records**, and explicit bounded-data messaging. The original API requests only the first 30 orders; there is **no claim** of full-database search.
- Added inline definitions and scope limitations for business-intelligence metrics, improved shared control styling, responsive workflow layout and semantic chart labels.
- Added component tests for guided navigation, charts, order filtering/sorting, and CSV spreadsheet-injection escaping.
- Existing optimiser, pilot solver, prediction and simulation algorithms and API contracts are unchanged. No paid services or new frontend dependencies were added.

## UX / enterprise notes

- The current publicly accessible demo uses synthetic and hypothetical records. No enterprise data should flow into the demo.
- CSV exports are browser-generated and filter-scoped. Spreadsheet formula-like values are prefixed before serialization, quotes are escaped. Treat all externally provided spreadsheet data as untrusted.
- Browser filters are not a security boundary. Enterprise-wide queries require backend-enforced organisation membership, dataset access grants, per-user permissions, query limits and auditing before they can be called production-ready.
- The workflow guide describes a typical user story: observe KPI signals, inspect relevant products, specify feasible model constraints, run the optimisation, and compare scenario uncertainty. Comparing simulation results must not be represented as realised cost savings.
- This increment does not implement enterprise file uploads, live Power BI, third-party credentials, persistent sessions, full historical pagination, or production-qualified multi-tenant data security.

## Verify on Windows

From `frontend`:

```powershell
npm ci
npm run build
npm test
npm run lint
```

From `backend`, with the existing virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

From the repository root:

```powershell
docker compose -f compose.full.yaml up -d --build
docker compose -f compose.full.yaml ps -a
Invoke-RestMethod http://127.0.0.1:8080/api/v1/health
Invoke-RestMethod http://127.0.0.1:8080/api/v1/ready
```

Browser checks: `Explore interactive demo` → Overview (change measure/date and choose a bar) → Operational orders (search, sort, filter, paginate and export CSV) → Business intelligence (check definitions, reporting period and product selection) → Optimisation → What-if simulator. Verify Exit demo returns to the welcome screen. Test responsive widths and keyboard navigation. Do not commit before all required local and GitHub Actions checks are green.

## Execution limitations in the artifact-building environment

TypeScript/JSX syntax parsing was executed with the global TypeScript compiler and passed. Python backend sources compiled. `npm ci --offline` could not complete because `zod-validation-error@4.0.2` was unavailable in the offline cache; therefore `npm run build`, `npm test` and `npm run lint` were **not** executed here. They require verification on the user's development machine. A successful Docker rebuild and smoke checks are also required before merging.
