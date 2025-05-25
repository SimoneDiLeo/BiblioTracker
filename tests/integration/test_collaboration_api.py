import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock # For mocking httpx.AsyncClient
import httpx # Required for creating mock response objects
import json

# Mock OpenAlex data for two researchers
MOCK_OA_ID_1 = "A1001"
MOCK_OA_PROFILE_1 = {
    "id": f"https://openalex.org/{MOCK_OA_ID_1}", "display_name": "Researcher One",
    "x_concepts": [
        {"id": "C1", "display_name": "Topic Alpha", "level": 0, "score": 0.9},
        {"id": "C2", "display_name": "Topic Beta", "level": 1, "score": 0.8}
    ]
}

MOCK_OA_ID_2 = "A1002"
MOCK_OA_PROFILE_2 = {
    "id": f"https://openalex.org/{MOCK_OA_ID_2}", "display_name": "Researcher Two",
    "x_concepts": [
        {"id": "C2", "display_name": "Topic Beta", "level": 1, "score": 0.85}, # Shared with R1
        {"id": "C3", "display_name": "Topic Gamma", "level": 0, "score": 0.7}
    ]
}

MOCK_OA_ID_3 = "A1003" # A third researcher for more complex scenarios if needed
MOCK_OA_PROFILE_3 = {
    "id": f"https://openalex.org/{MOCK_OA_ID_3}", "display_name": "Researcher Three",
    "x_concepts": [
        {"id": "C4", "display_name": "Topic Delta", "level": 0, "score": 0.9}
    ]
}


@pytest.fixture
def setup_collaboration_test_environment(client: TestClient, authenticated_headers, db_session_test):
    """
    Helper to register multiple users and their researcher profiles with specific OpenAlex IDs.
    Returns the main test user's ID and their auth headers.
    """
    main_user_data = {"username": "collab_user_main", "email": "main_collab@example.com", "password": "password"}
    client.post("/api/users/register", json=main_user_data)
    login_resp = client.post("/api/users/login", data={"username": main_user_data["username"], "password": main_user_data["password"]})
    main_auth_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}
    main_user_id = client.get("/api/users/me", headers=main_auth_headers).json()["id"]
    
    # Main user's researcher profile
    client.post("/api/researchers/", json={"first_name": "Main", "last_name": "Collab", "openalex_id": MOCK_OA_ID_1}, headers=main_auth_headers)

    # Create a second user and their researcher profile
    user2_data = {"username": "collab_user_2", "email": "user2_collab@example.com", "password": "password"}
    client.post("/api/users/register", json=user2_data)
    login_resp2 = client.post("/api/users/login", data={"username": user2_data["username"], "password": user2_data["password"]})
    auth_headers2 = {"Authorization": f"Bearer {login_resp2.json()['access_token']}"}
    client.post("/api/researchers/", json={"first_name": "Second", "last_name": "Collab", "openalex_id": MOCK_OA_ID_2}, headers=auth_headers2)

    # Create a third user and their researcher profile (no shared topics with main user initially by concept ID)
    user3_data = {"username": "collab_user_3", "email": "user3_collab@example.com", "password": "password"}
    client.post("/api/users/register", json=user3_data)
    login_resp3 = client.post("/api/users/login", data={"username": user3_data["username"], "password": user3_data["password"]})
    auth_headers3 = {"Authorization": f"Bearer {login_resp3.json()['access_token']}"}
    client.post("/api/researchers/", json={"first_name": "Third", "last_name": "Collab", "openalex_id": MOCK_OA_ID_3}, headers=auth_headers3)

    return main_user_id, main_auth_headers


def test_extract_my_research_topics_success(
    client: TestClient, mock_httpx_client, setup_collaboration_test_environment
):
    main_user_id, main_auth_headers = setup_collaboration_test_environment

    # Configure mock_httpx_client for main user's OpenAlex profile
    async def mock_get_collab(url, params=None):
        response_mock = AsyncMock(spec=httpx.Response)
        response_mock.status_code = 200
        if MOCK_OA_ID_1 in url: response_mock.json.return_value = MOCK_OA_PROFILE_1
        elif MOCK_OA_ID_2 in url: response_mock.json.return_value = MOCK_OA_PROFILE_2
        elif MOCK_OA_ID_3 in url: response_mock.json.return_value = MOCK_OA_PROFILE_3
        else:
            response_mock.status_code = 404
            response_mock.json.return_value = {"error": "Not Found"}
            response_mock.raise_for_status = MagicMock(side_effect=httpx.HTTPStatusError("Not Found", request=MagicMock(), response=response_mock))
        return response_mock
    mock_httpx_client.get = mock_get_collab

    response = client.post("/api/collaborations/researchers/me/extract-topics", headers=main_auth_headers)
    assert response.status_code == 200
    topics = response.json()
    assert len(topics) == len(MOCK_OA_PROFILE_1["x_concepts"])
    assert topics[0]["topic_name"] == MOCK_OA_PROFILE_1["x_concepts"][0]["display_name"]
    assert topics[0]["openalex_concept_id"] == MOCK_OA_PROFILE_1["x_concepts"][0]["id"].split("/")[-1] # Ensure ID part is extracted

def test_get_my_collaboration_suggestions_success(
    client: TestClient, mock_httpx_client, setup_collaboration_test_environment, db_session_test # db_session for inspecting DB state
):
    main_user_id, main_auth_headers = setup_collaboration_test_environment

    # Configure mock_httpx_client for all relevant OpenAlex profiles
    async def mock_get_collab(url, params=None):
        response_mock = AsyncMock(spec=httpx.Response)
        response_mock.status_code = 200
        if MOCK_OA_ID_1 in url: response_mock.json.return_value = MOCK_OA_PROFILE_1
        elif MOCK_OA_ID_2 in url: response_mock.json.return_value = MOCK_OA_PROFILE_2
        elif MOCK_OA_ID_3 in url: response_mock.json.return_value = MOCK_OA_PROFILE_3
        else: # Default for any other OpenAlex calls (e.g., works, not tested here)
            response_mock.json.return_value = {"results": []} 
        return response_mock
    mock_httpx_client.get = mock_get_collab
    
    # Trigger suggestion generation (which also extracts topics)
    response = client.get("/api/collaborations/researchers/me/suggestions", headers=main_auth_headers)
    assert response.status_code == 200
    suggestions = response.json()
    
    # Expected: Main user (OA_ID_1) shares "Topic Beta" (C2) with user 2 (OA_ID_2)
    assert len(suggestions) > 0
    
    found_expected_suggestion = False
    for sugg in suggestions:
        # Get researcher2's profile to find their ID
        researcher2_profile_db = db_session_test.query(db_models.Researcher).filter(db_models.Researcher.openalex_id == MOCK_OA_ID_2).first()
        assert researcher2_profile_db is not None

        if (sugg["researcher1_id"] == main_user_id and sugg["researcher2_id"] == researcher2_profile_db.user_id) or \
           (sugg["researcher2_id"] == main_user_id and sugg["researcher1_id"] == researcher2_profile_db.user_id) :
            # Find the topic "Topic Beta"
            topic_beta_db = db_session_test.query(db_models.ResearchTopic).filter(db_models.ResearchTopic.openalex_concept_id == "C2").first()
            assert topic_beta_db is not None
            if sugg["common_topic_id"] == topic_beta_db.id:
                found_expected_suggestion = True
                assert "Topic Beta" in sugg["suggestion_reason"]
                break
                
    assert found_expected_suggestion, "Expected collaboration suggestion for 'Topic Beta' not found."

    # Ensure no suggestion with user 3 (OA_ID_3) as they share no topics with main user by concept ID
    researcher3_profile_db = db_session_test.query(db_models.Researcher).filter(db_models.Researcher.openalex_id == MOCK_OA_ID_3).first()
    assert researcher3_profile_db is not None
    for sugg in suggestions:
        assert not (sugg["researcher1_id"] == researcher3_profile_db.user_id or sugg["researcher2_id"] == researcher3_profile_db.user_id)


def test_extract_topics_no_openalex_id(
    client: TestClient, authenticated_headers, registered_test_user # User has no researcher profile yet
):
    # Create researcher profile WITHOUT openalex_id
    client.post("/api/researchers/", json={"first_name": "NoOA", "last_name": "Topics"}, headers=authenticated_headers)
    
    response = client.post("/api/collaborations/researchers/me/extract-topics", headers=authenticated_headers)
    assert response.status_code == 400
    assert "OpenAlex ID not set" in response.json()["detail"]

def test_get_suggestions_no_openalex_id(
    client: TestClient, authenticated_headers, registered_test_user
):
    client.post("/api/researchers/", json={"first_name": "NoOA", "last_name": "Suggest"}, headers=authenticated_headers)

    response = client.get("/api/collaborations/researchers/me/suggestions", headers=authenticated_headers)
    assert response.status_code == 400
    assert "OpenAlex ID not set" in response.json()["detail"]


# Need to import db_models from database.models for db_session_test queries
from database import models as db_models
