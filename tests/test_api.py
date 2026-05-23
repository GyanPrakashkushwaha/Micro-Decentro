import pytest
from app import create_app
from models import db, VirtualAccount, Transaction
from config import TestConfig

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def headers():
    return {"X-API-Key": "decentro-secret-key-2026"}

def test_missing_api_key(client):
    response = client.post("/v1/virtual-accounts")
    assert response.status_code == 401
    assert "Invalid or missing API Key" in response.get_json()["message"]

def test_create_virtual_account(client, headers):
    response = client.post("/v1/virtual-accounts", json={"initial_deposit": 500.00}, headers=headers)
    assert response.status_code == 201
    data = response.get_json()
    assert float(data["balance"]) == 500.0
    assert "id" in data
    assert "account_number" in data

def test_payout_success(client, headers, app):
    # Setup two accounts
    sender = client.post("/v1/virtual-accounts", json={"initial_deposit": 1000.00}, headers=headers).get_json()
    receiver = client.post("/v1/virtual-accounts", json={"initial_deposit": 0.00}, headers=headers).get_json()

    payload = {
        "sender_id": sender["id"],
        "receiver_id": receiver["id"],
        "amount": 250.00
    }
    
    response = client.post("/v1/transactions/payout", json=payload, headers=headers)
    assert response.status_code == 201
    
    data = response.get_json()
    assert data["status"] == "SUCCESS"
    assert float(data["amount"]) == 250.0
    
    # Check balances
    sender_bal = client.get(f"/v1/virtual-accounts/{sender['id']}/balance", headers=headers).get_json()
    receiver_bal = client.get(f"/v1/virtual-accounts/{receiver['id']}/balance", headers=headers).get_json()
    
    assert float(sender_bal["balance"]) == 750.0
    assert float(receiver_bal["balance"]) == 250.0

def test_payout_insufficient_balance(client, headers):
    sender = client.post("/v1/virtual-accounts", json={"initial_deposit": 100.00}, headers=headers).get_json()
    receiver = client.post("/v1/virtual-accounts", json={"initial_deposit": 0.00}, headers=headers).get_json()

    payload = {
        "sender_id": sender["id"],
        "receiver_id": receiver["id"],
        "amount": 250.00
    }
    
    response = client.post("/v1/transactions/payout", json=payload, headers=headers)
    assert response.status_code == 400
    assert "Insufficient balance" in response.get_json()["message"]
    
    # Balance should be unchanged
    sender_bal = client.get(f"/v1/virtual-accounts/{sender['id']}/balance", headers=headers).get_json()
    assert float(sender_bal["balance"]) == 100.0

def test_payout_idempotency(client, headers):
    sender = client.post("/v1/virtual-accounts", json={"initial_deposit": 1000.00}, headers=headers).get_json()
    receiver = client.post("/v1/virtual-accounts", json={"initial_deposit": 0.00}, headers=headers).get_json()

    payload = {
        "sender_id": sender["id"],
        "receiver_id": receiver["id"],
        "amount": 200.00
    }
    
    idemp_headers = headers.copy()
    idemp_headers["Idempotency-Key"] = "test-key-12345"
    
    # First request
    response1 = client.post("/v1/transactions/payout", json=payload, headers=idemp_headers)
    assert response1.status_code == 201
    
    # Second request with same idempotency key
    response2 = client.post("/v1/transactions/payout", json=payload, headers=idemp_headers)
    assert response2.status_code == 200 # Returned from cache
    assert response1.get_json()["id"] == response2.get_json()["id"]
    
    # Balance should only be deducted once
    sender_bal = client.get(f"/v1/virtual-accounts/{sender['id']}/balance", headers=headers).get_json()
    assert float(sender_bal["balance"]) == 800.0
