import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock # For mocking httpx.AsyncClient
import httpx # Required for creating mock response objects
import json # For loading/dumping JSON

# Mock OpenAlex data
MOCK_OPENALEX_AUTHOR_ID = "A123"
MOCK_OPENALEX_AUTHOR_DATA = {
    "id": f"https://openalex.org/{MOCK_OPENALEX_AUTHOR_ID}",
    "display_name": "Test Author",
    "works_count": 10,
    "cited_by_count": 100,
    "ids": {"openalex": f"https://openalex.org/{MOCK_OPENALEX_AUTHOR_ID}", "orcid": "https://orcid.org/0000-0000-0000-0001"},
    "last_known_institution": {"display_name": "Test University"},
    "x_concepts": [
        {"id": "https://openalex.org/C1", "display_name": "Concept 1", "level": 0, "score": 0.8},
        {"id": "https://openalex.org/C2", "display_name": "Concept 2", "level": 1, "score": 0.7}
    ]
}
MOCK_OPENALEX_WORKS_DATA = [
    {"id": "https://openalex.org/W1", "title": "Work 1", "publication_year": 2020, "cited_by_count": 10, "authorships": [{"author": {"id": MOCK_OPENALEX_AUTHOR_ID}}]},
    {"id": "https://openalex.org/W2", "title": "Work 2", "publication_year": 2021, "cited_by_count": 20, "authorships": [{"author": {"id": MOCK_OPENALEX_AUTHOR_ID}}]}
]

@pytest.fixture
def mock_httpx_client(mocker):
    """Mocks the httpx.AsyncClient used in openalex_service.py"""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    
    # Configure the mock .get() method
    async def mock_get(url, params=None):
        response_mock = MagicMock(spec=httpx.Response)
        response_mock.status_code = 200 # Default success
        
        if MOCK_OPENALEX_AUTHOR_ID in url and "authors" in url:
            response_mock.json.return_value = MOCK_OPENALEX_AUTHOR_DATA
        elif "works" in url and params and params.get('filter') == f'author.id:{MOCK_OPENALEX_AUTHOR_ID}':
            response_mock.json.return_value = {"results": MOCK_OPENALEX_WORKS_DATA, "meta": {"count": len(MOCK_OPENALEX_WORKS_DATA)}}
        else:
            response_mock.status_code = 404
            response_mock.json.return_value = {"error": "Not Found"}
            # Simulate raise_for_status for non-2xx codes
            response_mock.raise_for_status = MagicMock(side_effect=httpx.HTTPStatusError("Not Found", request=MagicMock(), response=response_mock))

        return response_mock

    mock_client.get = mock_get
    # Patch the client instance in the openalex_service module
    mocker.patch('services.openalex_service.client', new=mock_client)
    return mock_client


# Fixture to create a researcher profile with an OpenAlex ID for the authenticated user
@pytest.fixture
def researcher_profile_with_openalex_id(client: TestClient, authenticated_headers, registered_test_user):
    profile_data = {
        "first_name": "OA Test",
        "last_name": "User",
        "affiliation": "OpenAlex Uni",
        "openalex_id": MOCK_OPENALEX_AUTHOR_ID # Use the ID that mock_httpx_client expects
    }
    response = client.post("/api/researchers/", json=profile_data, headers=authenticated_headers)
    assert response.status_code == 201
    return response.json()


def test_get_my_openalex_profile_success(
    client: TestClient, authenticated_headers, mock_httpx_client, researcher_profile_with_openalex_id
):
    # researcher_profile_with_openalex_id ensures the user has a profile with the correct OpenAlex ID
    response = client.get("/api/openalex/researchers/me/openalex-profile", headers=authenticated_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == MOCK_OPENALEX_AUTHOR_DATA["id"]
    assert data["display_name"] == MOCK_OPENALEX_AUTHOR_DATA["display_name"]
    
    # Verify httpx.get was called for author profile
    mock_httpx_client.get.assert_any_call(f"/authors/{MOCK_OPENALEX_AUTHOR_ID}", params={'mailto': 'default.email@example.com'})


def test_get_my_openalex_profile_caching(
    client: TestClient, authenticated_headers, mock_httpx_client, researcher_profile_with_openalex_id, db_session_test
):
    # First call - should call API
    client.get("/api/openalex/researchers/me/openalex-profile", headers=authenticated_headers)
    call_count_after_first = mock_httpx_client.get.call_count
    
    # Second call - should use cache
    response = client.get("/api/openalex/researchers/me/openalex-profile", headers=authenticated_headers)
    assert response.status_code == 200 # Still get data
    # Assert that mock_httpx_client.get was NOT called again for the author profile
    # The exact number of calls depends on whether other calls are made by other fixtures/setups.
    # We expect no *new* calls for the author profile.
    # Check if the number of calls for the specific URL has not increased.
    
    # Filter calls to the specific author URL
    author_url_calls = [
        call for call in mock_httpx_client.get.call_args_list 
        if call[0][0] == f"/authors/{MOCK_OPENALEX_AUTHOR_ID}"
    ]
    assert len(author_url_calls) == 1 # Should only be one call to this specific URL across both API calls


def test_get_my_openalex_profile_no_openalex_id(
    client: TestClient, authenticated_headers, registered_test_user # User exists, but no researcher profile / OA ID
):
    # Create researcher profile but without an OpenAlex ID
    profile_data = {"first_name": "NoOA", "last_name": "User", "affiliation": "NoOA Uni", "openalex_id": None}
    client.post("/api/researchers/", json=profile_data, headers=authenticated_headers)

    response = client.get("/api/openalex/researchers/me/openalex-profile", headers=authenticated_headers)
    assert response.status_code == 400 # Bad Request
    assert "OpenAlex ID not set" in response.json()["detail"]


def test_get_my_openalex_works_success(
    client: TestClient, authenticated_headers, mock_httpx_client, researcher_profile_with_openalex_id
):
    response = client.get("/api/openalex/researchers/me/openalex-works", headers=authenticated_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == len(MOCK_OPENALEX_WORKS_DATA)
    assert data[0]["id"] == MOCK_OPENALEX_WORKS_DATA[0]["id"]
    
    # Verify httpx.get was called for works
    expected_works_params = {
        'filter': f'author.id:{MOCK_OPENALEX_AUTHOR_ID}', 
        'per_page': 25, # Default in endpoint
        'page': 1,      # Default in endpoint
        'mailto': 'default.email@example.com'
    }
    mock_httpx_client.get.assert_any_call("/works", params=expected_works_params)

# Add more tests for caching of works, error handling from OpenAlex, etc.
# For example, test what happens if OpenAlex returns a 404 or 500 error.
# The mock_httpx_client fixture can be extended to simulate these.
