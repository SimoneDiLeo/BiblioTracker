import pytest
from fastapi.testclient import TestClient

# Test Researcher Profile Creation
def test_create_researcher_profile_success(client: TestClient, authenticated_headers, registered_test_user):
    researcher_data = {
        "first_name": "Test",
        "last_name": "User",
        "affiliation": "Test University",
        "openalex_id": "A123456789"
    }
    response = client.post("/api/researchers/", json=researcher_data, headers=authenticated_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == researcher_data["first_name"]
    assert data["user_id"] == registered_test_user["id"] # Check if linked to correct user
    assert data["openalex_id"] == researcher_data["openalex_id"]

def test_create_researcher_profile_no_auth(client: TestClient):
    researcher_data = {"first_name": "Test", "last_name": "User"}
    response = client.post("/api/researchers/", json=researcher_data)
    assert response.status_code == 401 # Expecting unauthorized

def test_create_researcher_profile_already_exists(client: TestClient, authenticated_headers, registered_test_user):
    # First profile creation
    researcher_data = {"first_name": "Test", "last_name": "User", "affiliation": "Test University"}
    response1 = client.post("/api/researchers/", json=researcher_data, headers=authenticated_headers)
    assert response1.status_code == 201

    # Attempt to create another profile for the same user
    researcher_data2 = {"first_name": "Another", "last_name": "Profile"}
    response2 = client.post("/api/researchers/", json=researcher_data2, headers=authenticated_headers)
    assert response2.status_code == 400 # Bad request
    assert "Researcher profile already exists" in response2.json()["detail"]

# Test Getting Own Researcher Profile
def test_get_researcher_profile_me_success(client: TestClient, authenticated_headers):
    # Create profile first
    researcher_data = {"first_name": "MyProfile", "last_name": "User", "affiliation": "My Uni"}
    client.post("/api/researchers/", json=researcher_data, headers=authenticated_headers)

    response = client.get("/api/researchers/me", headers=authenticated_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == researcher_data["first_name"]

def test_get_researcher_profile_me_no_profile(client: TestClient, authenticated_headers):
    # User is authenticated, but no researcher profile created for them yet
    response = client.get("/api/researchers/me", headers=authenticated_headers)
    assert response.status_code == 404
    assert "Researcher profile not found" in response.json()["detail"]

# Test Updating Researcher Profile
def test_update_researcher_profile_me_success(client: TestClient, authenticated_headers):
    # Create profile
    initial_data = {"first_name": "Initial", "last_name": "Name", "affiliation": "Old Uni", "openalex_id": "OA1"}
    create_response = client.post("/api/researchers/", json=initial_data, headers=authenticated_headers)
    assert create_response.status_code == 201
    
    update_data = {"first_name": "UpdatedFirst", "affiliation": "New Uni"} # Partial update
    response = client.put("/api/researchers/me", json=update_data, headers=authenticated_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == update_data["first_name"]
    assert data["last_name"] == initial_data["last_name"] # Should remain unchanged
    assert data["affiliation"] == update_data["affiliation"]
    assert data["openalex_id"] == initial_data["openalex_id"] # Should remain unchanged

def test_update_researcher_profile_me_no_profile(client: TestClient, authenticated_headers):
    update_data = {"first_name": "UpdatedFirst"}
    response = client.put("/api/researchers/me", json=update_data, headers=authenticated_headers)
    assert response.status_code == 404
    assert "Researcher profile not found" in response.json()["detail"]

# Test Getting Researcher by ID
def test_get_researcher_profile_by_id_success(client: TestClient, authenticated_headers):
    # Create a profile to fetch
    researcher_data = {"first_name": "FetchMe", "last_name": "ByID", "affiliation": "ID Uni"}
    create_response = client.post("/api/researchers/", json=researcher_data, headers=authenticated_headers)
    assert create_response.status_code == 201
    profile_id = create_response.json()["id"]

    response = client.get(f"/api/researchers/{profile_id}", headers=authenticated_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == profile_id
    assert data["first_name"] == researcher_data["first_name"]

def test_get_researcher_profile_by_id_not_found(client: TestClient, authenticated_headers):
    non_existent_id = 99999
    response = client.get(f"/api/researchers/{non_existent_id}", headers=authenticated_headers)
    assert response.status_code == 404
    assert f"Researcher profile with ID {non_existent_id} not found" in response.json()["detail"]

# Test Deleting Researcher Profile
def test_delete_researcher_profile_me_success(client: TestClient, authenticated_headers):
    # Create profile to delete
    researcher_data = {"first_name": "ToDelete", "last_name": "User"}
    create_response = client.post("/api/researchers/", json=researcher_data, headers=authenticated_headers)
    assert create_response.status_code == 201
    created_profile_id = create_response.json()["id"]

    delete_response = client.delete("/api/researchers/me", headers=authenticated_headers)
    assert delete_response.status_code == 200 # Endpoint returns the deleted profile data
    deleted_data = delete_response.json()
    assert deleted_data["id"] == created_profile_id

    # Verify profile is actually deleted (GET /me should now be 404)
    get_response = client.get("/api/researchers/me", headers=authenticated_headers)
    assert get_response.status_code == 404

def test_delete_researcher_profile_me_no_profile(client: TestClient, authenticated_headers):
    response = client.delete("/api/researchers/me", headers=authenticated_headers)
    assert response.status_code == 404
    assert "Researcher profile not found" in response.json()["detail"]
