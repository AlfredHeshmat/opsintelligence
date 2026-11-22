# Industry solver laboratory — illustrative input models

These CSV files are **wholly synthetic** and contain no public observations or company data.
They are small candidate-choice input models with assumed resource use and costs/margins.
Choose **Industry solver lab** > appropriate industry > **Upload non-confidential decision-options CSV**.
Keep the capacities in the default pilot preset to reproduce the mathematical results.

| Industry | Objective | Resource columns | Resource capacities |
|---|---|---|---|
| Logistics | Minimise assumed costs | `handling_units`, `express_slots` | 9, 2 |
| Agriculture | Maximise assumed gross margin | `water_ml`, `budget_aud` | 13, 1300 |
| Technology | Minimise assumed cloud costs | `cpu_units`, `region_a_slots` | 13, 2 |

`item_id`, `option_id`, `objective_value` are required. Each item must choose one option. A finite 0/1 assignment MILP searches globally optimal assignments **for this specified model only**. A field/crop selection is not a causal crop-response model; a cloud region label is not measured latency or SLA certification. No real source data is bundled here.
