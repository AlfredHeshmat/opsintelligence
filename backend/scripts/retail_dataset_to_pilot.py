"""Convert a local, legally obtained retail CSV into a mixed-provenance pilot.

Source quantities are observed; decision option costs/capacities are assumed.
This script never fetches data and never stores customer identifiers.

Usage (from backend dir):
python -m scripts.retail_dataset_to_pilot --input path/to/OnlineRetail.csv --output path/to/case.json

UCI Online Retail / Online Retail II historical CSV columns:
StockCode, Quantity, UnitPrice (or Price), InvoiceDate (or InvoiceDate), Invoice (optional).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

MAX_FILE_BYTES = 30_000_000
MAX_ROWS = 300_000


def convert(path: Path, top_n: int = 5) -> dict:
    if not 1 <= top_n <= 20:
        raise ValueError("top_n must be between 1 and 20")
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("Export a smaller, <=30 MB source CSV for reproducible local processing")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    quantities: Counter[str] = Counter()
    accepted = rejected = 0
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, strict=True)
        if not reader.fieldnames or not {"StockCode", "Quantity"}.issubset(reader.fieldnames):
            raise ValueError("CSV requires UCI-style StockCode and Quantity columns")
        for idx, row in enumerate(reader):
            if idx >= MAX_ROWS:
                raise ValueError("Source exceeds 300,000 rows; create a bounded sample")
            try:
                sku = (row['StockCode'] or '').strip()
                qty = int(row['Quantity'])
                invoice = (row.get('Invoice') or row.get('InvoiceNo') or '').strip()
                if not sku or len(sku) > 60 or qty <= 0 or invoice.lower().startswith('c'):
                    rejected += 1
                    continue
                # Avoid retaining any personal details, prices, invoices or dates.
                quantities[sku] += qty
                accepted += 1
            except (ValueError, TypeError):
                rejected += 1
    if not quantities:
        raise ValueError("No positive non-cancellation stock quantities found")
    # Deterministic ordering; demands are observations, coefficients below are NOT.
    top = sorted(quantities.items(), key=lambda x: (-x[1], x[0]))[:top_n]
    options = []
    for idx, (sku, units) in enumerate(top, 1):
        # Scenario uses one decision per SKU with two hypothetical logistics alternatives.
        # Normalize resource usage so observed volumes of different magnitudes remain solvable.
        # Synthetic costs are illustrative, not fitted to historical retail prices.
        normalized_units = max(1, min(12, int(math.ceil(units / max(x[1] for x in top) * 10))))
        base = 10 + idx * 2
        for mode, cost, handling, slot in [
            ('economy', base, normalized_units, 0),
            ('express', base + 7, max(1, int(math.ceil(normalized_units * 0.7))), 1),
        ]:
            options.append({'item_id': f'sku_{idx}', 'option_id': mode,
                            'objective_value': float(cost),
                            'resources': {'handling_units': float(handling), 'express_slots': float(slot)}})
    max_economy = sum(x['resources']['handling_units'] for x in options if x['option_id'] == 'economy')
    # Feasible by default; operators should explicitly adjust handling cap to explore tradeoffs.
    scenario = {'industry': 'logistics', 'objective': 'minimize_cost',
                'input_provenance': 'user_supplied_unverified',
                'capacities': {'handling_units': max_economy, 'express_slots': float(top_n)},
                'options': options}
    return {'scenario': scenario,
            'observed_aggregate': [{'item_id': f'sku_{i}', 'stock_code': sku, 'observed_units': qty} for i,(sku,qty) in enumerate(top,1)],
            'data_provenance': {'source': 'User-supplied CSV; designed for UCI Online Retail or Online Retail II export',
                                'source_file_sha256': digest,
                                'rows_accepted': accepted, 'rows_excluded': rejected,
                                'observed_values': 'Aggregated product unit counts only',
                                'assumptions': 'Economy/express cost, handling coefficients, capacity and eligibility are hypothetical; NOT UCI observations',
                                'original_dataset_url': 'https://archive.ics.uci.edu/dataset/502/online+retail+ii',
                                'original_dataset_license': 'CC BY 4.0; credit source in project displays',
                                'personal_data_discarded': 'No customer ID, invoice, geography or price retained'}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--top-n', type=int, default=5)
    args = parser.parse_args()
    result = convert(args.input, args.top_n)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(f"Exported {len(result['scenario']['options'])} options with explicit observed/synthetic provenance")


if __name__ == '__main__':
    main()
