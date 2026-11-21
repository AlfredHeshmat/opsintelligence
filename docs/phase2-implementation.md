# Phase 2 implementation — operational intelligence and optimisation

This adds SQLAlchemy tables, Alembic migration `0002`, a deterministic synthetic warehouse seed, live KPIs, explainable threshold alerts, and a persisted SciPy/HiGHS mixed-integer optimisation run. The React command centre displays database-derived figures and actual solver output.

## Apply to existing Windows setup

Keep Docker PostgreSQL running. Stop the backend temporarily, then in `backend` with your Phase 1 virtual environment activated:

```powershell
python -m pip install -e ".[dev]"
python -m alembic upgrade head
python -m pytest -q
python -m uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8000
```

If `python -m pip install -e` fails, use the explicit virtualenv interpreter (`.\.venv\Scripts\python.exe`). `scipy` and `numpy` are newly required; those dependencies are declared in `pyproject.toml`.

In the frontend terminal:

```powershell
npm install
npm run build
npm run dev
```

Open the dashboard and click **Generate demo dataset** once. It safely refuses to overwrite existing orders. Use the **Solve allocation** button to run a real mixed-integer optimiser. Alternatively use `POST /api/v1/data/seed`, `GET /api/v1/operations/overview`, and `POST /api/v1/optimization/solve` through `/docs`.

## Model assumptions

For each pending order choose exactly one of `defer`, `economy`, or `express`. Shipping uses order-specific fixed charges and priority-weighted estimated lateness penalties. Deferrals incur a per-unit priority-weighted penalty. Constraints enforce daily handling units, staffed labour throughput (8 units/hour), and available SKU inventory. `optimal` refers only to this simplified integer model. The baseline is deferring all pending orders; computed improvement **is not realised business savings**. This model assumes one warehouse, daily resources, no multi-day inventory reservation, no workforce shift logic, and static shipping transit times. Do not use it to execute live business decisions without validation.

## Next phases

Delay-risk ML training with temporal holdout and careful leakage prevention; anomaly model benchmarks; Monte Carlo uncertainty simulation; CSV ingestion validation and audit trail; comprehensive auth, observability, CI and end-to-end tests. This delivery is a working Phase 2 milestone, **not a claim that all advanced project phases are complete**.
