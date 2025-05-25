import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock # For mocking httpx.AsyncClient
import httpx # Required for creating mock response objects
import json

# Using the same mock data as in test_openalex_api.py or define specific for analysis
MOCK_OA_ID_FOR_ANALYSIS = "A123" # Must match the ID used in researcher_profile_with_openalex_id
MOCK_OA_PROFILE_FOR_ANALYSIS = {
    "id": f"https://openalex.org/{MOCK_OA_ID_FOR_ANALYSIS}",
    "display_name": "Test Author Analysis",
    "works_count": 5,
    "cited_by_count": 50,
    "ids": {"openalex": f"https://openalex.org/{MOCK_OA_ID_FOR_ANALYSIS}"},
    "x_concepts": [
        {"id": "https://openalex.org/C101", "display_name": "AI Ethics", "level": 1, "score": 0.95},
        {"id": "https://openalex.org/C102", "display_name": "Machine Learning", "level": 0, "score": 0.88},
        {"id": "https://openalex.org/C103", "display_name": "Data Science", "level": 1, "score": 0.76}
    ]
}

# This test relies on the mock_httpx_client fixture from conftest.py (or test_openalex_api.py)
# and researcher_profile_with_openalex_id which sets the OpenAlex ID.

def test_get_my_concept_summary_success(
    client: TestClient, 
    authenticated_headers, 
    mock_httpx_client, # This fixture should ensure that openalex_service.client is mocked
    researcher_profile_with_openalex_id # Ensures user has a profile with MOCK_OPENALEX_AUTHOR_ID
):
    # Configure the mock_httpx_client to return specific data for this test
    async def mock_get_custom_for_analysis(url, params=None):
        response_mock = AsyncMock(spec=httpx.Response)
        response_mock.status_code = 200
        
        if MOCK_OA_ID_FOR_ANALYSIS in url and "authors" in url: # Assuming ID is A123 from researcher_profile fixture
            response_mock.json.return_value = MOCK_OA_PROFILE_FOR_ANALYSIS
        else:
            response_mock.status_code = 404
            response_mock.json.return_value = {"error": "Not Found For Analysis Test"}
            response_mock.raise_for_status = MagicMock(side_effect=httpx.HTTPStatusError("Not Found", request=MagicMock(), response=response_mock))
        return response_mock
    
    mock_httpx_client.get = mock_get_custom_for_analysis

    response = client.get("/api/analysis/researchers/me/concept-summary", headers=authenticated_headers)
    
    assert response.status_code == 200
    analysis_result = response.json()

    assert analysis_result["analysis_type"] == "researcher_concept_summary"
    assert "researcher_id" in analysis_result # Should match the researcher's ID
    
    # result_data is JSON parsed into a Pydantic model by the response_model
    result_data_content = analysis_result["result_data"] # This is now a dict (parsed JSON)
    
    assert "concepts" in result_data_content
    concepts_in_result = result_data_content["concepts"]
    assert len(concepts_in_result) == len(MOCK_OA_PROFILE_FOR_ANALYSIS["x_concepts"])
    
    # Verify content of one concept
    expected_concept = MOCK_OA_PROFILE_FOR_ANALYSIS["x_concepts"][0]
    actual_concept = concepts_in_result[0]
    
    assert actual_concept["concept_id"] == expected_concept["id"]
    assert actual_concept["display_name"] == expected_concept["display_name"]
    assert actual_concept["level"] == expected_concept["level"]
    assert actual_concept["score"] == expected_concept["score"]

def test_get_my_concept_summary_no_openalex_id(
    client: TestClient, authenticated_headers, registered_test_user
):
    # Create researcher profile but without an OpenAlex ID
    profile_data = {"first_name": "NoOA", "last_name": "UserAnalysis", "affiliation": "NoOA UniAnalysis", "openalex_id": None}
    client.post("/api/researchers/", json=profile_data, headers=authenticated_headers)

    response = client.get("/api/analysis/researchers/me/concept-summary", headers=authenticated_headers)
    assert response.status_code == 400 # Bad Request
    assert "OpenAlex ID not set" in response.json()["detail"]

def test_get_my_concept_summary_openalex_fetch_fails(
    client: TestClient, authenticated_headers, mock_httpx_client, researcher_profile_with_openalex_id
):
    # Configure mock to simulate OpenAlex API failure for author profile
    async def mock_get_failure(url, params=None):
        response_mock = AsyncMock(spec=httpx.Response)
        response_mock.status_code = 500
        response_mock.json.return_value = {"error": "Internal Server Error"}
        response_mock.raise_for_status = MagicMock(side_effect=httpx.HTTPStatusError("Server Error", request=MagicMock(), response=response_mock))
        return response_mock

    mock_httpx_client.get = mock_get_failure

    response = client.get("/api/analysis/researchers/me/concept-summary", headers=authenticated_headers)
    assert response.status_code == 404 # Based on current error handling in service
    assert "Could not generate or retrieve concept summary" in response.json()["detail"]

def test_get_my_concept_summary_no_concepts_in_profile(
    client: TestClient, authenticated_headers, mock_httpx_client, researcher_profile_with_openalex_id
):
    profile_no_concepts = MOCK_OA_PROFILE_FOR_ANALYSIS.copy()
    profile_no_concepts["x_concepts"] = [] # Empty list of concepts

    async def mock_get_no_concepts(url, params=None):
        response_mock = AsyncMock(spec=httpx.Response)
        response_mock.status_code = 200
        if MOCK_OA_ID_FOR_ANALYSIS in url and "authors" in url:
            response_mock.json.return_value = profile_no_concepts
        else:
            response_mock.status_code = 404 # Should not happen if ID matches
        return response_mock
    
    mock_httpx_client.get = mock_get_no_concepts

    response = client.get("/api/analysis/researchers/me/concept-summary", headers=authenticated_headers)
    # The service currently returns None if no concepts, leading to 404 from API if not handled differently
    assert response.status_code == 404 
    assert "Could not generate or retrieve concept summary" in response.json()["detail"]
    # If we wanted to store an empty result, the service and API would need adjustment.
    # For example, store `{"concepts": []}` and return 200.
    # Current implementation expects concepts to be present for a "successful" generation.
