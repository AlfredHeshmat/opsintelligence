"""Invitation lifecycle and tenancy tests use isolated in-memory SQLite."""
from datetime import timedelta
from hashlib import sha256
from sqlalchemy import select
from sqlalchemy.orm import Session

from test_enterprise_security import fixture_client, login, auth
from app.api.enterprise import now
from app.models.identity import Membership, SecurityAudit, User
from app.models.invitations import OrganisationInvitation


def endpoint(org):
    return f'/api/v1/enterprise/organisations/{org}/invitations'


def owner_token(client):
    return login(client, 'alpha@example.com', 'correct-horse-unique-one').json()['access_token']


def test_new_employee_invite_one_time_and_hash_not_exposed(fixture_client):
    client, engine, (alpha, beta) = fixture_client
    token = owner_token(client)
    created = client.post(endpoint(alpha), headers=auth(token), json={
        'email': ' NewHire@Example.com ', 'role': 'analyst'
    })
    assert created.status_code == 201, created.text
    code = created.json()['code']
    assert len(code) >= 40
    listing = client.get(endpoint(alpha), headers=auth(token)).json()
    assert listing[0]['email'] == 'newhire@example.com'
    assert listing[0]['status'] == 'pending'
    assert code not in str(listing)
    with Session(engine) as db:
        stored = db.scalar(select(OrganisationInvitation).where(
            OrganisationInvitation.organisation_id == alpha))
        assert stored.code_digest == sha256(code.encode()).hexdigest()
        assert code not in str(db.scalars(select(SecurityAudit)).all())
    assert client.post('/api/v1/enterprise/auth/invitations/accept',json={
        'code': code, 'email': 'wrong@example.com', 'password': 'my-unique-long-password'
    }).status_code == 400
    result = client.post('/api/v1/enterprise/auth/invitations/accept', json={
        'code': code, 'email': 'newhire@example.com', 'password': 'my-unique-long-password'
    })
    assert result.status_code == 200, result.text
    assert result.json()['role'] == 'analyst'
    assert client.post('/api/v1/enterprise/auth/invitations/accept', json={
        'code': code, 'email': 'newhire@example.com', 'password': 'my-unique-long-password'
    }).status_code == 400
    employee = login(client, 'newhire@example.com', 'my-unique-long-password').json()['access_token']
    assert client.get(f'/api/v1/enterprise/organisations/{alpha}/projects', headers=auth(employee)).status_code == 200
    assert client.get(f'/api/v1/enterprise/organisations/{beta}/projects', headers=auth(employee)).status_code == 404
    assert client.get(f'/api/v1/enterprise/organisations/{alpha}/audit', headers=auth(employee)).status_code == 403
    assert [i['status'] for i in client.get(endpoint(alpha), headers=auth(token)).json()] == ['accepted']
    actions = [a['action'] for a in client.get(f'/api/v1/enterprise/organisations/{alpha}/audit',headers=auth(token)).json()]
    assert 'invitation.created' in actions and 'invitation.accepted' in actions


def test_invites_need_admin_and_owner_for_admin_role(fixture_client):
    client, engine, (alpha, beta) = fixture_client
    owner = owner_token(client)
    viewer = login(client, 'viewer@example.com', 'correct-horse-unique-viewer').json()['access_token']
    other = login(client, 'beta@example.com', 'correct-horse-unique-two').json()['access_token']
    body = {'email':'newhire@example.com','role':'analyst'}
    assert client.post(endpoint(alpha),json=body).status_code == 401
    assert client.post(endpoint(alpha),headers=auth(viewer),json=body).status_code == 403
    assert client.post(endpoint(alpha),headers=auth(other),json=body).status_code == 404
    assert client.get(endpoint(alpha),headers=auth(other)).status_code == 404
    assert client.post(endpoint(alpha),headers=auth(owner),json={**body,'role':'admin'}).status_code == 201
    assert client.post(endpoint(alpha),headers=auth(owner),json=body).status_code == 409
    # Admin actor can invite viewers/analysts but cannot grant or revoke admin invitations.
    assert client.post(f'/api/v1/enterprise/organisations/{alpha}/members',headers=auth(owner),json={
        'email':'beta@example.com','role':'admin'
    }).status_code == 201
    admin = other
    invite_id = client.get(endpoint(alpha),headers=auth(owner)).json()[0]['id']
    assert client.delete(f'{endpoint(alpha)}/{invite_id}',headers=auth(admin)).status_code == 403
    assert client.post(endpoint(alpha),headers=auth(admin),json={
        'email':'second@example.com','role':'admin'
    }).status_code == 403
    assert client.post(endpoint(alpha),headers=auth(admin),json={
        'email':'second@example.com','role':'viewer'
    }).status_code == 201
    assert client.get(endpoint(beta),headers=auth(owner)).status_code == 404


def test_revoke_expire_and_reissue(fixture_client):
    client, engine, (alpha, _) = fixture_client
    owner = owner_token(client)
    payload = {'email':'person@example.com','role':'viewer'}
    create = client.post(endpoint(alpha),headers=auth(owner),json=payload).json()
    assert client.delete(f'{endpoint(alpha)}/{create["id"]}',headers=auth(owner)).status_code == 204
    assert client.delete(f'{endpoint(alpha)}/{create["id"]}',headers=auth(owner)).status_code == 409
    assert client.post('/api/v1/enterprise/auth/invitations/accept',json={
        'code':create['code'],'email':payload['email'],'password':'long-secure-demo-password'
    }).status_code == 400
    reissue = client.post(endpoint(alpha),headers=auth(owner),json=payload).json()
    assert reissue['code'] != create['code']
    with Session(engine) as db:
        record = db.get(OrganisationInvitation, reissue['id'])
        record.expires_at = now()-timedelta(minutes=1)
        db.commit()
    assert client.post('/api/v1/enterprise/auth/invitations/accept',json={
        'code':reissue['code'],'email':payload['email'],'password':'long-secure-demo-password'
    }).status_code == 400
    assert client.get(endpoint(alpha),headers=auth(owner)).json()[0]['status'] == 'expired'
    assert client.post(endpoint(alpha),headers=auth(owner),json=payload).status_code == 201


def test_existing_accounts_must_authenticate_as_invited_email(fixture_client):
    client, engine, (alpha, beta) = fixture_client
    owner = owner_token(client)
    beta_user = login(client,'beta@example.com','correct-horse-unique-two').json()['access_token']
    viewer = login(client,'viewer@example.com','correct-horse-unique-viewer').json()['access_token']
    invite = client.post(endpoint(alpha), headers=auth(owner), json={
        'email':'beta@example.com','role':'viewer'
    }).json()
    accept = '/api/v1/enterprise/auth/invitations/accept'
    data = {'code':invite['code'],'email':'beta@example.com'}
    assert client.post(accept,json={**data,'password':'attempt-takeover-password'}).status_code == 401
    assert client.post(accept,headers=auth(viewer),json=data).status_code == 403
    assert client.post(accept,headers=auth(beta_user),json=data).status_code == 200
    with Session(engine) as db:
        memberships = db.scalars(select(Membership).where(Membership.organisation_id == alpha)).all()
        assert any(m.role == 'viewer' and db.get(User,m.user_id).email == 'beta@example.com' for m in memberships)
    # Reusing an accepted code is rejected.
    assert client.post(accept,headers=auth(beta_user),json=data).status_code == 400
