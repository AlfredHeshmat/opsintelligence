from app.api.workspace import preview_csv, CSVPreviewRequest, validate_scenario, ScenarioSpec, industry_catalog


def test_catalog_distinguishes_executable_solver_from_templates():
    data = industry_catalog()
    by_id = {v['id']:v for v in data['industries']}
    assert by_id['logistics']['status'] == 'solver_available'
    assert by_id['healthcare']['status'] == 'blueprint_only'


def test_scenario_does_not_fake_an_optimum():
    result = validate_scenario(ScenarioSpec(industry='mining', objective='maximize_margin'))
    assert result['decision_status'] == 'configuration_validated_not_solved'
    assert result['solver_available'] is False


def test_csv_preview_no_data_exfiltration():
    result = preview_csv(CSVPreviewRequest(filename='operations.csv', csv_text='sku,warehouse,private_note\nSKU-A,NSW,secret value\n'))
    assert result['rows'] == 1
    assert result['candidate_industry'] == 'logistics'
    assert result['persisted'] is False
    assert 'secret value' not in str(result)
