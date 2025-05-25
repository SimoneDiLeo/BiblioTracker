import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock # For mock_httpx_client if not already imported via conftest or other test files
from services.bibliometric_utils import calculate_h_index, calculate_i10_index # For verification

# Import mock data and fixtures if they are not auto-available via conftest
# For this example, assume MOCK_OPENALEX_AUTHOR_DATA and MOCK_OPENALEX_WORKS_DATA
# are defined as in test_openalex_api.py and mock_httpx_client fixture is available.
# If not, you might need to redefine or import them.
# from .test_openalex_api import MOCK_OPENALEX_AUTHOR_DATA, MOCK_OPENALEX_WORKS_DATA, MOCK_OPENALEX_AUTHOR_ID

# Using the same mock data as in test_openalex_api.py
MOCK_OPENALEX_AUTHOR_ID_FOR_BIBLIO = "A123" # Must match the ID used in researcher_profile_with_openalex_id
MOCK_OPENALEX_AUTHOR_DATA_FOR_BIBLIO = {
    "id": f"https://openalex.org/{MOCK_OPENALEX_AUTHOR_ID_FOR_BIBLIO}",
    "display_name": "Test Author Biblio",
    "works_count": 2, # Based on MOCK_OPENALEX_WORKS_DATA_FOR_BIBLIO
    "cited_by_count": 30, # Sum of citations from works
    "ids": {"openalex": f"https://openalex.org/{MOCK_OPENALEX_AUTHOR_ID_FOR_BIBLIO}"},
    "x_concepts": [{"id": "C1", "display_name": "Concept 1", "level": 0, "score": 0.8}]
}
MOCK_OPENALEX_WORKS_DATA_FOR_BIBLIO = [
    {"id": "W1", "title": "Work 1", "publication_year": 2020, "cited_by_count": 10, "authorships": [{"author": {"id": MOCK_OPENALEX_AUTHOR_ID_FOR_BIBLIO}}]},
    {"id": "W2", "title": "Work 2", "publication_year": 2021, "cited_by_count": 20, "authorships": [{"author": {"id": MOCK_OPENALEX_AUTHOR_ID_FOR_BIBLIO}}]}
]

# This test relies on the mock_httpx_client fixture from conftest.py (or test_openalex_api.py if structured that way)
# and researcher_profile_with_openalex_id which sets the OpenAlex ID.

def test_get_my_bibliometric_summary_success(
    client: TestClient, 
    authenticated_headers, 
    mock_httpx_client, # This fixture should ensure that openalex_service.client is mocked
    researcher_profile_with_openalex_id # Ensures user has a profile with MOCK_OPENALEX_AUTHOR_ID
):
    # Configure the mock_httpx_client to return specific data for this test if not already globally configured
    # This step is crucial if the global mock isn't returning exactly what's needed for bibliometrics
    async def mock_get_custom(url, params=None):
        response_mock = AsyncMock(spec=httpx.Response)
        response_mock.status_code = 200
        
        if MOCK_OPENALEX_AUTHOR_ID_FOR_BIBLIO in url and "authors" in url:
            response_mock.json.return_value = MOCK_OPENALEX_AUTHOR_DATA_FOR_BIBLIO
        elif "works" in url and params and params.get('filter') == f'author.id:{MOCK_OPENALEX_AUTHOR_ID_FOR_BIBLIO}':
            response_mock.json.return_value = {"results": MOCK_OPENALEX_WORKS_DATA_FOR_BIBLIO, "meta": {"count": len(MOCK_OPENALEX_WORKS_DATA_FOR_BIBLIO)}}
        else:
            response_mock.status_code = 404
            response_mock.json.return_value = {"error": "Not Found For Bibliometric Test"}
            response_mock.raise_for_status = MagicMock(side_effect=httpx.HTTPStatusError("Not Found", request=MagicMock(), response=response_mock))
        return response_mock
    
    mock_httpx_client.get = mock_get_custom # Override the mock's get

    response = client.get("/api/bibliometrics/researchers/me/summary", headers=authenticated_headers)
    
    assert response.status_code == 200
    summary_data = response.json()

    # Verify calculations based on MOCK_OPENALEX_DATA
    # total_publications from profile
    assert summary_data["total_publications"] == MOCK_OPENALEX_AUTHOR_DATA_FOR_BIBLIO["works_count"]
    # total_citations from profile
    assert summary_data["total_citations"] == MOCK_OPENALEX_AUTHOR_DATA_FOR_BIBLIO["cited_by_count"]
    
    # h-index and i10-index from works
    citation_counts = [work["cited_by_count"] for work in MOCK_OPENALEX_WORKS_DATA_FOR_BIBLIO]
    expected_h_index = calculate_h_index(citation_counts)
    expected_i10_index = calculate_i10_index(citation_counts)
    
    assert summary_data["h_index"] == expected_h_index
    assert summary_data["i10_index"] == expected_i10_index
    assert "researcher_id" in summary_data
    assert "summary_generated_at" in summary_data

def test_get_my_bibliometric_summary_no_openalex_id(
    client: TestClient, authenticated_headers, registered_test_user # User exists, but no researcher profile / OA ID
):
    # Create researcher profile but without an OpenAlex ID
    profile_data = {"first_name": "NoOA", "last_name": "UserBib", "affiliation": "NoOA UniBib", "openalex_id": None}
    client.post("/api/researchers/", json=profile_data, headers=authenticated_headers)

    response = client.get("/api/bibliometrics/researchers/me/summary", headers=authenticated_headers)
    assert response.status_code == 400 # Bad Request
    assert "OpenAlex ID not set" in response.json()["detail"]

def test_get_my_bibliometric_summary_openalex_fetch_fails(
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

    response = client.get("/api/bibliometrics/researchers/me/summary", headers=authenticated_headers)
    # The exact status code might depend on how the service handles this.
    # Expecting 500 or similar if the data fetch is critical and fails.
    assert response.status_code == 500 # As per current API implementation
    assert "Could not generate or retrieve bibliometric summary" in response.json()["detail"]
