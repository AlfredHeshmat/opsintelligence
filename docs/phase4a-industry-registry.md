# Phase 4A — Versioned industry catalogue and common decision contract

## Scope and maturity

Phase 4A adds *definitions and validation*, **not** production multi-industry optimisation. The only executable solver remains the pre-existing synthetic warehouse MILP. Technology and Agriculture now have explicit candidate data contracts but no runnable domain solver. The other industries are catalogued at metadata-only maturity. A catalogue label must never appear as "solver available".

- `GET /api/v1/workspace/registry`: versioned catalogue and full metadata (20 industry families).
- `GET /api/v1/workspace/registry/{industry_id}`: industry subtypes, metric IDs/units, required fields, objectives, constraints and warnings.
- `GET /api/v1/workspace/decision/solver-capabilities`: the implemented warehouse adapter's *demonstration-only* scope.
- `POST /api/v1/workspace/decision/validate`: structurally validate a typed, explicit decision specification; **does not execute any solver**, accept API secrets, or read company data.
- Existing `/industries` and `/scenario/validate` remain available for compatibility.

## Example Technology decision contract

```json
{
  "industry": "technology", "subindustry": "cloud_infrastructure",
  "objective": "minimize_cost", "horizon_months": 12,
  "risk_appetite": "balanced", "data_source": "synthetic",
  "constraints": [
    {"metric_id": "latency_sla", "operator": "<=", "value": 200, "unit": "ms"},
    {"metric_id": "availability_sla", "operator": ">=", "value": 99.95, "unit": "percent"}
  ]
}
```

This is a **validation contract**, not a business-optimality result. An actual cloud model would require workload profiles, region and compute pricing, availability/failure curves, measured latency-capacity relationships and policy constraints.

## Example Agriculture / capstone pathway

Use industry `agriculture`, subindustry `crop_production`, with objective `maximize_margin`. Required fields include `field_id`, `crop`, `area_ha`, `soil_type`, `rainfall_mm`, `forecast_yield_t_ha`, and `input_cost_aud`. Add feature provenance, timestamps, geospatial resolution, split strategy, missingness controls, and validated management-response estimates before optimising interventions. Predictive wheat yield alone does not justify claims about how changing water or fertiliser causes yield changes.

## Constraints and correctness

- Validation rejects unknown industries, cross-industry subindustries, unsupported goals, duplicate constraint metrics, invalid units for explicitly known metrics, nonfinite numbers and out-of-range CAPEX reductions.
- Industry detection from CSV headers is heuristic; operator confirmation is mandatory.
- Metric unit `industry_defined` denotes an **incomplete** contract, not a validated KPI. No automated solver execution occurs in this phase.
- CAPEX reduction **by** 7% is represented as a percentage reduction constraint, not CAPEX **to** 7% of revenue. The user must approve the meaning and baseline before an executable model is created.
- Before enabling real company data or remote MCP/API execution: implement authentication, tenant isolation, RBAC, encrypted secret handling, audit logging, allowlisted egress and tool permissions, safe data connectors, lineage, and tests of denied access.
- A formal solver adapter contract with feasibility, objective recomputation, certificate/gap reporting, and uncertainty validation is Phase 4C work.

## Verify

From `backend`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q app
```

From `frontend`:

```powershell
npm install
npm run build
```

View `http://127.0.0.1:5173/#decision-workspace`. Try Technology → Cloud Infrastructure, Agriculture → Crop Production, then Logistics → Warehouse. Inspect capabilities and ensure only Logistics shows a solver demo; validation alone must never display savings.
