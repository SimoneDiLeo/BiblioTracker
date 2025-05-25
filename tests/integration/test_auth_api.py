import pytest
from fastapi.testclient import TestClient

# Test User Registration
def test_register_user_success(client: TestClient, test_user_data):
    response = client.post("/api/users/register", json=test_user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == test_user_data["username"]
    assert data["email"] == test_user_data["email"]
    assert "id" in data
    assert "hashed_password" not in data # Ensure password is not returned

def test_register_user_duplicate_username(client: TestClient, test_user_data, registered_test_user):
    # registered_test_user fixture already created a user with test_user_data
    # Attempt to register again with the same username
    duplicate_username_data = {"username": test_user_data["username"], "email": "new_email@example.com", "password": "newpassword"}
    response = client.post("/api/users/register", json=duplicate_username_data)
    assert response.status_code == 400
    assert "Username already registered" in response.json()["detail"]

def test_register_user_duplicate_email(client: TestClient, test_user_data, registered_test_user):
    # registered_test_user fixture already created a user with test_user_data
    # Attempt to register again with the same email
    duplicate_email_data = {"username": "newuser", "email": test_user_data["email"], "password": "newpassword"}
    response = client.post("/api/users/register", json=duplicate_email_data)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

# Test User Login
def test_login_success(client: TestClient, test_user_data, registered_test_user):
    # registered_test_user ensures the user exists
    login_data = {"username": test_user_data["username"], "password": test_user_data["password"]}
    response = client.post("/api/users/login", data=login_data) # Login uses form data
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_incorrect_username(client: TestClient, test_user_data, registered_test_user):
    login_data = {"username": "wronguser", "password": test_user_data["password"]}
    response = client.post("/api/users/login", data=login_data)
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

def test_login_incorrect_password(client: TestClient, test_user_data, registered_test_user):
    login_data = {"username": test_user_data["username"], "password": "wrongpassword"}
    response = client.post("/api/users/login", data=login_data)
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

# Test Fetching Current User (/api/users/me)
def test_read_users_me_success(client: TestClient, authenticated_headers, registered_test_user):
    response = client.get("/api/users/me", headers=authenticated_headers)
    assert response.status_code == 200
    data = response.json()
    # registered_test_user is the user whose token is in authenticated_headers
    assert data["username"] == registered_test_user["username"]
    assert data["email"] == registered_test_user["email"]
    assert data["id"] == registered_test_user["id"]

def test_read_users_me_no_token(client: TestClient):
    response = client.get("/api/users/me")
    assert response.status_code == 401 # Expecting unauthorized
    assert "Not authenticated" in response.json()["detail"] # Or "Could not validate credentials" depending on FastAPI

def test_read_users_me_invalid_token(client: TestClient):
    headers = {"Authorization": "Bearer invalidtoken"}
    response = client.get("/api/users/me", headers=headers)
    assert response.status_code == 401 # Expecting unauthorized
    assert "Could not validate credentials" in response.json()["detail"]
