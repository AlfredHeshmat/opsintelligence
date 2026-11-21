# Phase 3 — Predictive intelligence and scenario analysis

## Implemented (synthetic warehouse demonstration)

- `GET /api/v1/products/performance?days=30&sku=SKU-A`: filtered product revenue, order quantities, pending demand, stock, observed on-time delivery rate. Accepted windows: 7/30/90/365. Reporting is anchored to latest order date.
- `POST /api/v1/predictions/train`: trains a Random Forest classifier on completed orders with an **80/20 chronological holdout** and saves the model locally under `backend/.model_artifacts/`. Reports holdout accuracy, balanced accuracy, precision, recall, F1, ROC AUC (when defined), and majority-class baseline accuracy.
- `GET /api/v1/predictions/model`: inspect model training report.
- `GET /api/v1/predictions/delays?sku=SKU-A&limit=100`: model-estimated risk for currently pending orders. Train first.
- `POST /api/v1/scenarios/compare`: reproducible Monte Carlo cost scenario for a saved **optimal** warehouse allocation run. Parameters: `optimization_run_id`, `trials`, `seed`, `delay_probability`, `late_penalty_per_unit`, `shipping_cost_multiplier`.
- Frontend: product/SKU filters, reporting windows, product CSV export, model evaluation and high-risk orders, adjustable scenario assumptions and risk distributions.

No extra schema migration is necessary beyond the Phase 2 warehouse migration. Model files are local, ignored by Git, and should never be loaded from untrusted sources. Run `python -m pytest -q` in backend, `npm ci && npm run build` in frontend.

### Suggested local workflow

1. Preserve your current database and working Git branch, then merge this source update into the repository.
2. Restart the FastAPI app using `python -m uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8000` from `backend`.
3. Restart Vite in `frontend` (`npm install`, `npm run build`, `npm run dev`).
4. Use your existing 240-record dataset. There is no need to regenerate or reset data.
5. Open **Business intelligence** to filter by reporting period and SKU.
6. Select **Train delay model** and inspect the actual evaluation metrics. No meaningful accuracy can be guaranteed with a tiny synthetic dataset.
7. Run **Solve allocation** (Phase 2), then **Run scenario comparison** under What-if simulator, adjusting late-risk and cost assumptions.

### Boundaries and limitations

- Reports describe **synthetic demonstration data**, not observed enterprise performance.
- The training split is chronological but the synthetic sample is small and may have distribution artefacts. No cross-organisation generalisation, calibration or production accuracy is claimed.
- `current_report` and model artifacts are local to the backend instance, not versioned in the DB. A production deployment needs a secure model registry, metadata, retraining strategy, monitoring and drift detection.
- Simulation uses independent Bernoulli delay shocks and user-specified probabilities; it is **not** an actuarial forecast or a proof of expected savings. Baseline remains the Phase 2 defer-all model, not an observed business-as-usual operation.
- Changing shipping factor in Phase 3 recomputes **simulation costs for a fixed allocation**; it does not re-optimise the allocation. Rerun the optimiser when capacity/labour assumptions change.
- Production features still needed: CSV/ERP connectors, authentication/authorisation, API rate limits, audit trails, external weather/fuel/economic feeds, observability, calibrated models, robust scenario comparisons, and domain-specific optimisation adapters.

## Future: multi-domain decision intelligence engine

OpsIntelligence's **long-term objective** is a reusable engine for complex, constrained business decision problems, not a warehouse-only dashboard. Extend the system using domain adapters rather than claiming that one solver automatically understands every industry.

A domain adapter must define:

1. **Decision variables** with units and type (binary, integer, continuous), such as aircraft assignment, departure choice, portfolio weights.
2. **Objectives and trade-offs**, such as minimise cost, delays and emissions, or maximise risk-adjusted return. Multi-objective preferences must be explicit (weighted, lexicographic, or Pareto frontier).
3. **Hard constraints**, e.g. route legality, crew hours, runway capacity, regulatory or portfolio limits.
4. **Observed inputs and provenance**, including weather, fuel, demand, exchange rates, country policy announcements, and timestamps.
5. **Uncertain variables and distributions**, with scenario sets, correlations, sensitivity tests and the source of calibration.
6. **Solver family** appropriate to mathematical structure (MILP, constraint programming, nonlinear / stochastic / robust optimisation), budgets and termination status.
7. **Verification:** feasibility checks, objective reconciliation, baselines, alternative scenarios and tests.
8. **Domain-specific UX:** adjustable assumptions, units, filters, audit-ready explanations, and predicted vs observed results clearly separated.

### Aviation example (not yet implemented)

A flight logistics adapter could optimise aircraft assignment and routing for a given day with fuel prices, wind and weather forecasts, airport slot restrictions, aircraft performance, maintenance, crew, demand and emissions assumptions. Weather has time/location uncertainty; each proposed plan must satisfy aviation safety, scheduling and operational rules. Route feasibility must be independently validated against authoritative data.

### Cross-country investment example (not yet implemented)

A portfolio adapter could compare feasible investment allocations under currency risk, country exposure limits, liquidity, transaction costs, events and estimated return distributions. Its optimum would be conditional on forecast assumptions and a specified risk objective, **not** a universal prediction of the best investment or guaranteed return. Include stress scenarios and model uncertainty.

**Claims policy:** report `optimal` only when solver proves optimality for the specified mathematical model and solver tolerances; otherwise say `feasible`, `time-limited`, or `infeasible`. A finite compute budget cannot exhaustively search arbitrary quadrillions of combinations and guarantee universal optimality across unknown business dimensions. Prefer decompositions, heuristics or approximations with quality bounds when necessary.
