# Phase 4E.4 + 4E.5 — Project decisions and access hardening

## What this adds

- `/api/v1/enterprise/organisations/{org_id}/projects/{project_id}/optimisation/solve`: authenticated **Analyst+** MILP dispatch planning, only for a validated `logistics` project.
- `/optimisation/runs`: paginated, authorised **Viewer+** run history, latest-first.
- `/optimisation/runs/{run_id}`: authorised, tenant- and project-scoped run retrieval.
- `0008_project_optimisation_runs`: adds persisted versioned project optimisation results. The existing 500-order Acme dataset is not altered by this migration.
- The enterprise `Project optimisation` panel now runs the backend solver and explains results and limits.
- Legacy direct member assignment disabled by default (`OPS_ALLOW_LEGACY_MEMBER_ADD=false`); invitations are now the supported onboarding workflow.
- CI now includes frontend lint.

## Mathematical formulation

Eligible orders: records with `status=pending` from the active, organisation-scoped, imported Logistics CSV. At most 150 pending orders in a run.

For each pending order *i* choose a binary variable `x_i` (1 = dispatch, 0 = defer). Quantity `q_i`, recorded CSV shipping estimate `s_i` (AUD/order), assumed defer penalty `p` (AUD/unit) and priority weight `w_i` (standard 1, priority 2, express 3):

```
minimise  sum_i [x_i * s_i + (1-x_i) * p * w_i * q_i]
subject to sum_i q_i * x_i <= handling_capacity
           x_i in {0,1}
```

Defer-all baseline = `sum_i p*w_i*q_i`. "Modelled difference" is baseline minus optimised objective. The baseline is *constructed*, not observed operational expenditure; the difference is **not realised savings**. Missing warehouse-specific capacities, live inventory, labour, routing, SLAs, fulfilment costs, and demand forecasts limit real-world applicability. Priority weights and penalty are visible assumptions.

SciPy HiGHS MILP runs with an 8-second time limit and exact gap request. An objective is returned only for `optimal` status; partial incumbents from time-limited runs are not advertised as proven optimum. Run decisions are checked against capacity and integrality. Costs are converted to integer cents for model inputs; baseline and persisted totals are Decimal.

## Provenance and lifecycle

Each run persists the project ID, organisation ID, actor ID, model version, dataset SHA-256, parameters, solver status/message, outcomes, and the per-order decision snapshot. A later CSV replacement keeps prior runs as history but marks them **older dataset**. Run records do not trigger real shipments or write to source orders.

## Security scope

- Backend `project_for` checks **current** membership and project ownership on *every* optimisation request.
- `POST /optimisation/solve`: Analyst+, `GET` run history/details: Viewer+; nonmembers receive 404, unauthenticated clients 401.
- Audit `project.optimisation_run` is created after successful solve storage.
- `OPS_ALLOW_LEGACY_MEMBER_ADD` defaults to false. Use one-time invite codes instead of adding arbitrary existing identities without their consent. Do not turn this flag on for a public deployment.
- Self-service company registration is still a local-only feature and remains **disabled by default** in application settings. The local Docker compose sets it on for the test workflow; override `OPS_ENABLE_LOCAL_SIGNUP=false` for any public deployment.

## Deployment and engineering limits

No paid services added. No access to real enterprise data or connectors is claimed safe for the public internet. Before external deployment: review signup/invitation anti-abuse, email ownership verification, MFA, TLS, password-reset process, data retention, vulnerability scans, dependency pinning, full independent tenant penetration tests, per-user/project permissions, CORS/secrets/configuration and rate limits. Public demo and private enterprise workspaces must remain separated.

## Verification on Windows

From project root after extracting the patch:

```
cd frontend
npm run lint
npm run build
npm test
cd ..\backend
.\.venv\Scripts\python.exe -m pytest -q
cd ..
docker compose -f compose.full.yaml up -d --build
docker compose -f compose.full.yaml ps -a
```

Check `migrate` is Exited (0), backend/db healthy, then open local frontend. As Analyst, select Acme Warehouse Optimisation -> Project optimisation, run with capacity=100 and defer penalty=12; verify the run is saved. As Viewer, reading history is allowed but solving is 403. A user in another organisation must receive 404 for another organisation's run. Re-importing a changed CSV should flag the former run as "older dataset".
