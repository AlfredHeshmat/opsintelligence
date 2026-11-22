"""Independent small-case enumeration verifies mathematical outputs, not merely statuses."""
from itertools import product

import pytest
from pydantic import ValidationError

from app.services.industry_pilots import PRESETS, PilotSpec, parse_csv_scenario, solve_pilot


def exact_enumeration(spec):
    groups = {item: [o for o in spec.options if o.item_id == item] for item in sorted({o.item_id for o in spec.options})}
    outcomes = []
    for choices in product(*groups.values()):
        if all(sum(o.resources.get(resource, 0) for o in choices) <= limit + 1e-9 for resource, limit in spec.capacities.items()):
            outcomes.append(sum(o.objective_value for o in choices))
    return (max if spec.objective == 'maximize_margin' else min)(outcomes) if outcomes else None


@pytest.mark.parametrize('industry', ['logistics', 'agriculture', 'technology'])
def test_pilots_are_optimal_against_independent_enumeration(industry):
    spec = PilotSpec(**PRESETS[industry])
    expected = exact_enumeration(spec)
    out = solve_pilot(spec)
    assert out['status'] == 'optimal'
    assert out['objective_value'] == expected
    assert out['item_count'] == len({o.item_id for o in spec.options})
    assert out['input_provenance'] == 'synthetic_demo'
    for key, usage in out['constraint_usage'].items():
        assert usage['used'] <= usage['limit'] + 1e-8, key
    assert solve_pilot(spec)['decisions'] == out['decisions']


def test_infeasible_case_does_not_claim_optimum():
    data = PRESETS['logistics'].copy()
    data['capacities'] = {'handling_units': 0, 'express_slots': 0}
    out = solve_pilot(PilotSpec(**data))
    assert out['status'] == 'infeasible'
    assert out['objective_value'] is None
    assert out['decisions'] == []


def test_invalid_inputs_are_rejected():
    data = PRESETS['technology'].copy()
    with pytest.raises(ValidationError):
        PilotSpec(**{**data, 'capacities': {'cpu_units': -1, 'region_a_slots': 2}})
    with pytest.raises(ValidationError):
        PilotSpec(**{**data, 'options': data['options'] + [data['options'][0]]})
    with pytest.raises(ValidationError):
        PilotSpec(**{**data, 'capacities': {'cpu_units': 100, 'region_a_slots': 2, 'secret_param': 1}})
    with pytest.raises(ValidationError):
        PilotSpec(**{**data, 'options': [{**data['options'][0], 'resources': {'cpu_units': -10}}] + data['options'][1:]})


def test_restricted_csv_round_trip():
    spec = parse_csv_scenario('technology', 'item_id,option_id,objective_value,cpu_units,region_a_slots\na,a1,20,1,1\na,a2,25,2,0\nb,b1,12,2,1\nb,b2,18,1,0\n', {'cpu_units': 3, 'region_a_slots': 1})
    assert spec.input_provenance == 'user_supplied_unverified'
    out = solve_pilot(spec)
    assert out['status'] == 'optimal'
    assert out['objective_value'] == 38
    with pytest.raises(ValueError):
        parse_csv_scenario('technology', 'item_id,option_id,objective_value,extra\na,a1,20,10\n', {'cpu_units': 3, 'region_a_slots': 1})


def test_http_pilot_api_uses_bounded_nonpersistent_models():
    # Isolated router contract test: no DB connection required for public synthetic demos.
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.api.industry_pilots import router

    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as client:
        cat = client.get('/api/v1/industry-pilots/catalogue')
        assert cat.status_code == 200
        assert len(cat.json()['data_sources']) == 3
        preset = client.get('/api/v1/industry-pilots/presets/agriculture')
        assert preset.status_code == 200
        assert 'synthetic' in preset.json()['warning'].lower()
        result = client.post('/api/v1/industry-pilots/solve', json=preset.json()['scenario'])
        assert result.status_code == 200
        assert result.json()['status'] == 'optimal'
        malformed = client.post('/api/v1/industry-pilots/solve-csv', json={'industry': 'logistics', 'capacities': {'handling_units': 3,'express_slots': 1}, 'csv_text': 'not,csv\n1,2'})
        assert malformed.status_code == 422
        assert client.post('/api/v1/industry-pilots/solve', json={'industry': 'finance', 'objective': 'minimize_cost', 'capacities': {}, 'options': []}).status_code == 422
