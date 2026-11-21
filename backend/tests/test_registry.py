import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.api.workspace import decision_registry, industry_definition, validate_decision, solver_capabilities, preview_csv, CSVPreviewRequest
from app.services.decision_contracts import DecisionSpec, ConstraintSpec


def test_registry_contains_technology_and_agritech_without_fake_solvers():
    industries = {i['id']: i for i in decision_registry()['industries']}
    assert len(industries) >= 20
    assert industries['logistics']['support_level'] == 'solver_demo'
    assert industries['logistics']['adapter_id'] == 'warehouse_milp_v1'
    assert industries['technology']['solver_available'] is False
    assert industries['agriculture']['solver_available'] is False
    assert 'crop_production' in industries['agriculture']['subindustries']
    assert 'saas' in industries['technology']['subindustries']


def test_agriculture_contract_contains_capstone_inputs():
    item = industry_definition('agriculture')['industry']
    for field in ('soil_type', 'rainfall_mm', 'forecast_yield_t_ha'):
        assert field in item['required_fields']
    assert any(m['unit'] == 't/ha' for m in item['metrics'])


def test_wrong_subindustry_and_objective_rejected():
    with pytest.raises(ValidationError):
        DecisionSpec(industry='agriculture', subindustry='saas', objective='maximize_margin')
    with pytest.raises(ValidationError):
        DecisionSpec(industry='technology', subindustry='saas', objective='maximize_yield')


def test_unit_mismatch_blocks_scenario_but_does_not_execute():
    spec = DecisionSpec(industry='technology', subindustry='cloud_infrastructure',
                        objective='minimize_cost', constraints=[
                            ConstraintSpec(metric_id='latency_sla', operator='<=', value=200, unit='hours')])
    response = validate_decision(spec)
    assert response['specification_valid'] is False
    assert 'unit' in response['errors'][0].lower()
    assert response['solver_executable_for_this_spec'] is False


def test_valid_decision_contract_never_claims_optimum():
    spec = DecisionSpec(industry='agriculture', subindustry='crop_production',
                        objective='maximize_margin', constraints=[
                            ConstraintSpec(metric_id='water_allocation', operator='<=', value=100, unit='ML')])
    response = validate_decision(spec)
    assert response['specification_valid'] is True
    assert response['decision_status'] == 'contract_validated_not_solved'
    assert response['solver_executable_for_this_spec'] is False


def test_duplicate_constraints_not_accepted():
    with pytest.raises(ValidationError):
        DecisionSpec(industry='technology', subindustry='saas', objective='minimize_cost',
                     constraints=[ConstraintSpec(metric_id='latency_sla', operator='<=', value=100, unit='ms'),
                                  ConstraintSpec(metric_id='latency_sla', operator='>=', value=30, unit='ms')])


def test_registry_unknown_industry_404():
    with pytest.raises(HTTPException) as exc:
        industry_definition('not-real')
    assert exc.value.status_code == 404


def test_solver_capabilities_are_explicit_and_safe():
    capabilities = solver_capabilities()
    assert capabilities['auto_execute'] is False
    assert len(capabilities['adapters']) == 1
    assert capabilities['adapters'][0]['verified_for_company_data'] is False


def test_weak_csv_classification_new_domains():
    for header, industry in [('ndvi,rainfall,soil', 'agriculture'),
                             ('cloud,latency,gpu', 'technology')]:
        data = preview_csv(CSVPreviewRequest(filename='schema.csv', csv_text=header+'\n1,2,3\n'))
        assert data['candidate_industry'] == industry
        assert data['industry_confirmation_required'] is True
