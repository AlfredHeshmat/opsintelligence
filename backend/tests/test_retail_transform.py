from pathlib import Path
import pytest
from scripts.retail_dataset_to_pilot import convert
from app.services.industry_pilots import PilotSpec, solve_pilot


def test_retail_transform_preserves_provenance_and_discards_customer_fields(tmp_path: Path):
    f=tmp_path/'demo.csv'
    f.write_text('Invoice,StockCode,Quantity,Price,Customer ID\n123,SKU-A,10,4.5,person-99\n124,SKU-A,5,4.5,person-98\nC125,SKU-A,-3,4.5,person-98\n126,SKU-B,8,7,person-77\n',encoding='utf-8')
    result=convert(f,top_n=2)
    assert result['data_provenance']['rows_accepted']==3
    assert result['data_provenance']['rows_excluded']==1
    assert result['observed_aggregate'][0]['observed_units']==15
    assert 'person-99' not in str(result)
    spec=PilotSpec(**result['scenario'])
    out=solve_pilot(spec)
    assert out['status']=='optimal'
    assert out['input_provenance']=='user_supplied_unverified'


def test_retail_transform_rejects_wrong_format(tmp_path: Path):
    f=tmp_path/'bad.csv'
    f.write_text('customer,email\na,b\n')
    with pytest.raises(ValueError):
        convert(f)
