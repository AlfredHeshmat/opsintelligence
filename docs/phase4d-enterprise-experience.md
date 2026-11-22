# Phase 4D — Enterprise Experience & Decision Clarity

## Scope

A design and interaction improvement over the existing Phase 4C.2 application. Existing solver APIs, data contracts, identity rules, audit logic, mathematical coefficients, Docker topology and migration history are unchanged.

### Delivered

- Grouped, keyboard-accessible sidebar with clear sections, URL-hash active state, local-demo boundary and compact mobile navigation.
- Updated design tokens, typography, focus indicators, spacing and reusable enterprise components; removed unused starter theme styles from the active stylesheet.
- Dashboard quick actions and more legible KPIs.
- Scenario contract feedback appears beside the validation button. The legacy capital-spending parameter is explicitly marked as a **contract-validation-only assumption**, not as an enforced solver target. The backend contract is intentionally unchanged.
- Side-by-side comparison of the **latest and preceding Monte Carlo runs**, with each run's actual submitted assumptions and modelled expected cost, a delta and a baseline comparison chart. Current results remain visible but are marked stale if the user edits assumptions without rerunning.
- Strong warning on the delay prediction panel when holdout recall/F1 is zero or accuracy fails to exceed the majority baseline; no manipulation of measured metrics.
- Distinct optimal and infeasible states in the three-industry Solver Lab with truthful data provenance.
- Additional frontend regression tests for the navigation and industry lab.

## Not delivered / release blockers

This is not a claim of enterprise production readiness. Outstanding work includes independently verified live read-only connectors against separate databases, authenticated tenant isolation for the CSV solver demo, secure persistent document ingestion, comprehensive end-to-end tests, real industry datasets with complete constraint inputs and licences, ML model validation, solver snapshot regression controls, accessibility checks on actual devices and a public secure deployment.

Current public demo endpoints must receive **only synthetic or approved non-confidential data**. The dashboard's local Docker deployment must not be published on the open internet without a separate security review.

## Verification on Windows

From project root:

```powershell
cd frontend
npm ci
npm run build
npm test
npm run lint
cd ..
cd backend
.\.venv\Scripts\python.exe -m pytest -q
cd ..
docker compose -f compose.full.yaml up -d --build
docker compose -f compose.full.yaml ps -a
Invoke-RestMethod http://127.0.0.1:8080/api/v1/ready
```

Browser walkthrough:

1. Navigate using the grouped sidebar and verify the active section indicator.
2. Validate Logistics, Agriculture and Technology contracts. Feedback must appear adjacent to the validation button.
3. Solve built-in Logistics, Agriculture and Technology scenarios and deliberately run infeasible capacity settings. Their objective values must remain the same for unchanged inputs.
4. Train the synthetic delay model; confirm its poor holdout model quality is not hidden.
5. Solve the warehouse demo, then run two Monte Carlo scenarios with different delay probability and the **same** trials and penalty. Compare run assumptions and the resulting expected cost delta. Change an input without running; ensure the panel warns that results are stale.
6. Confirm the Enterprise Workspace and local admin / connector approval continue to work; connector execution remains restricted.
7. Review responsive layouts at mobile, tablet and desktop widths and test keyboard navigation and the skip link.

**Interpretation:** Modelled improvement is relative to an illustrative baseline, not realised savings. Mathematical optimality applies only to the supplied formulation and inputs.
