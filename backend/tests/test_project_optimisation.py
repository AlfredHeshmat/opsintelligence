"""Project MILP correctness, read/write RBAC, stale dataset and tenant isolation."""
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session

from test_project_data import secure_project, raw_csv, sample_row
from app.models.project_optimisation import ProjectOptimisationRun
from app.models.identity import Membership
from app.models.project_data import ProjectOrder
from app.services.project_optimisation import plan_dispatch


def pending(id, qty, shipping, priority='standard'):
    from types import SimpleNamespace
    return SimpleNamespace(order_id=id, sku='SKU-A', warehouse_id='WH-01', quantity=qty,
                           priority=priority, shipping_cost_aud=Decimal(shipping), status='pending')


def test_model_proves_optimum_and_respects_unit_capacity():
    orders=[pending('A',2,'3'),pending('B',3,'5','priority'),pending('C',1,'40')]
    result=plan_dispatch(orders,3,Decimal('12.00'))
    assert result['status']=='optimal'
    assert result['baseline_cost_aud']==Decimal('108.00')
    # B saves 72 - 5 = 67, A saves 24 - 3 = 21; C costs 40 to save 12.
    assert [d['order_id'] for d in result['decisions'] if d['action']=='dispatch']==['B']
    assert result['objective_cost_aud']==Decimal('41.00')
    zero=plan_dispatch(orders,0,Decimal('12.00'))
    assert zero['objective_cost_aud']==zero['baseline_cost_aud']
    assert all(d['action']=='defer' for d in zero['decisions'])


def test_model_rejects_unsupported_or_unsafe_workloads():
    import pytest
    with pytest.raises(ValueError,match='No pending'):plan_dispatch([],1,Decimal('12'))
    with pytest.raises(ValueError,match='at most'):plan_dispatch([pending(str(i),1,'2') for i in range(151)],1,Decimal('12'))
    with pytest.raises(ValueError,match='Defer penalty'):plan_dispatch([pending('A',1,'2')],1,Decimal('0'))
    with pytest.raises(ValueError,match='Handling capacity'):plan_dispatch([pending('A',1,'2')],-1,Decimal('12'))


def test_project_solve_authorisation_audit_history_and_replacement(secure_project):
    client,engine,(org,project,other_org,other_project),owner,other,viewer=secure_project
    root=f'/api/v1/enterprise/organisations/{org}/projects/{project}'
    solve=root+'/optimisation/solve'
    rows=[dict(sample_row('A'),status='pending',shipped_date='',priority='priority',quantity='2',shipping_cost_aud='3.00'),
          dict(sample_row('B'),status='pending',shipped_date='',priority='standard',quantity='3',shipping_cost_aud='4.00'),
          dict(sample_row('DONE'),status='delivered')]
    assert client.post(solve,headers=owner,json={'handling_capacity':3}).status_code==422
    assert client.post(root+'/orders/import',headers={**owner,'Content-Type':'text/csv','X-Filename':'orders.csv'},content=raw_csv(rows)).status_code==201
    config={'handling_capacity':3,'defer_penalty_aud_per_unit':'12.00'}
    assert client.post(solve,json=config).status_code==401
    assert client.post(solve,headers=viewer,json=config).status_code==403
    assert client.post(solve,headers=other,json=config).status_code==404
    assert client.get(root+'/optimisation/runs',headers=other).status_code==404
    assert client.get(root+'/optimisation/runs',headers=viewer).json()['total']==0
    assert client.post(solve,headers=owner,json={**config,'handling_capacity':-1}).status_code==422
    response=client.post(solve,headers=owner,json=config)
    assert response.status_code==201,response.text
    result=response.json()
    assert result['status']=='optimal' and result['dataset_current']
    assert result['baseline_cost_aud']==84
    # A dispatch => 3 + B deferred 36; versus B dispatch 4 + A defer 48.
    assert result['objective_cost_aud']==39
    assert len(result['decisions'])==2
    # The role is rechecked on every request; this token now belongs to an Analyst.
    with Session(engine) as db:
        member=db.scalar(select(Membership).where(Membership.organisation_id==org, Membership.role=='viewer'))
        member.role='analyst';db.commit()
    assert client.post(solve,headers=viewer,json=config).status_code==201
    run_id=result['id']
    assert client.get(root+f'/optimisation/runs/{run_id}',headers=viewer).status_code==200
    assert client.get(root+f'/optimisation/runs/{run_id}',headers=other).status_code==404
    assert client.get(f'/api/v1/enterprise/organisations/{other_org}/projects/{other_project}/optimisation/runs/{run_id}',headers=other).status_code==404
    # Dataset replacement retains an immutable snapshot but marks earlier runs stale.
    replacement=client.post(root+'/orders/import',headers={**owner,'Content-Type':'text/csv','X-Filename':'new.csv'},content=raw_csv([dict(rows[0],order_id='NEW')]))
    assert replacement.status_code==201,replacement.text
    older=client.get(root+f'/optimisation/runs/{run_id}',headers=viewer).json()
    assert older['dataset_current'] is False and older['decisions']==result['decisions']
    with Session(engine) as db:
        assert db.scalar(select(ProjectOptimisationRun)).dataset_sha256==result['dataset_sha256']
        assert len(db.scalars(select(ProjectOrder)).all())==1
    actions=client.get(f'/api/v1/enterprise/organisations/{org}/audit',headers=owner).json()
    assert any(a['action']=='project.optimisation_run' for a in actions)


def test_legacy_direct_member_assignment_is_disabled_without_flag(secure_project):
    client,engine,(org,project,other_org,other_project),owner,other,viewer=secure_project
    # Tests default to secure mode; no direct membership writes without an invite.
    response=client.post(f'/api/v1/enterprise/organisations/{org}/members',headers=owner,
                         json={'email':'other@test.example','role':'analyst'})
    assert response.status_code==403
    assert 'invitation' in response.json()['detail'].lower()
    assert client.get(f'/api/v1/enterprise/organisations/{org}/projects',headers=other).status_code==404


def test_milp_matches_exhaustive_optimum_on_small_cases():
    from itertools import product
    records=[pending('A',2,'4'),pending('B',4,'7','priority'),pending('C',3,'6'),pending('D',1,'1','express')]
    for cap in (0,1,3,4,6,7,10):
        found=plan_dispatch(records,cap,Decimal('9.00'))
        brute=[]
        for decisions in product((0,1),repeat=len(records)):
            if sum(o.quantity*x for o,x in zip(records,decisions))<=cap:
                total=sum((o.shipping_cost_aud if x else Decimal('9.00')*o.quantity*{'standard':1,'priority':2,'express':3}[o.priority]) for o,x in zip(records,decisions))
                brute.append(total)
        assert found['status']=='optimal'
        assert found['objective_cost_aud']==min(brute)
