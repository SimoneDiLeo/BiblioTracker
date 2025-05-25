import httpx
import json # For converting dict to JSON string for storage
from sqlalchemy.orm import Session
from database import models as db_models # Renamed to avoid conflict with 'models' parameter name
from . import cache_crud, openalex_schemas # Schemas for validation/serialization if needed
from config import OPENALEX_API_BASE_URL, OPENALEX_POLITE_EMAIL

# Initialize a reusable HTTP client
client = httpx.AsyncClient(base_url=OPENALEX_API_BASE_URL, timeout=10.0) # Added timeout

async def get_openalex_author_data(openalex_id: str, email: str = None) -> dict | None:
    """
    Fetches author data from OpenAlex API.
    openalex_id should be the ID only (e.g., A5023888337), not the full URL.
    """
    if not openalex_id:
        return None
        
    # Construct the ID part of the URL if it's a full URL
    if openalex_id.startswith("https://openalex.org/"):
        openalex_id = openalex_id.split("/")[-1]

    url = f"/authors/{openalex_id}"
    params = {}
    actual_email = email or OPENALEX_POLITE_EMAIL
    if actual_email:
        params['mailto'] = actual_email
    
    try:
        response = await client.get(url, params=params)
        response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx responses
        return response.json()
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred while fetching author data for {openalex_id}: {e}") # Basic logging
        return None
    except httpx.RequestError as e:
        print(f"Request error occurred while fetching author data for {openalex_id}: {e}")
        return None

async def get_author_works_from_openalex(
    openalex_author_id: str, 
    email: str = None, 
    per_page: int = 25, 
    max_pages: int = 1 # Limit pages to avoid excessive requests
) -> list[dict] | None:
    """
    Fetches author's works from OpenAlex.
    openalex_author_id should be the ID part (e.g., A5023888337).
    """
    if not openalex_author_id:
        return None

    if openalex_author_id.startswith("https://openalex.org/"):
        openalex_author_id = openalex_author_id.split("/")[-1]

    all_works = []
    current_page = 1
    actual_email = email or OPENALEX_POLITE_EMAIL
    
    while current_page <= max_pages:
        params = {
            'filter': f'author.id:{openalex_author_id}',
            'per_page': per_page,
            'page': current_page
        }
        if actual_email:
            params['mailto'] = actual_email
        
        try:
            response = await client.get("/works", params=params)
            response.raise_for_status()
            data = response.json()
            works_on_page = data.get('results', [])
            all_works.extend(works_on_page)
            
            # Check if there are more results (OpenAlex meta includes total count)
            # For simplicity, we'll just break if fewer than per_page results are returned or if max_pages is reached.
            if len(works_on_page) < per_page or not works_on_page:
                break
            current_page += 1
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred while fetching works for author {openalex_author_id}: {e}")
            return None # Or return partial results if preferred
        except httpx.RequestError as e:
            print(f"Request error occurred while fetching works for author {openalex_author_id}: {e}")
            return None
            
    return all_works

async def fetch_and_cache_researcher_openalex_profile(
    db: Session, 
    researcher: db_models.Researcher, 
    email: str = None, 
    cache_duration_seconds: int = 86400 # 24 hours
) -> dict | None:
    if not researcher.openalex_id:
        return None # Cannot fetch without an OpenAlex ID

    data_type = "author_profile"
    cached_data_entry = cache_crud.get_cached_openalex_data(db, researcher.id, data_type)
    if cached_data_entry:
        return json.loads(cached_data_entry.openalex_json_data) # Deserialize JSON string

    # Data not in cache or expired, fetch from OpenAlex
    author_data = await get_openalex_author_data(researcher.openalex_id, email)
    if author_data:
        cache_crud.store_openalex_data(
            db, researcher.id, data_type, json.dumps(author_data), cache_duration_seconds
        )
    return author_data

async def fetch_and_cache_researcher_openalex_works(
    db: Session, 
    researcher: db_models.Researcher, 
    email: str = None, 
    cache_duration_seconds: int = 86400, # 24 hours
    per_page: int = 25,
    max_pages: int = 1 # Default to fetching only the first page of works
) -> list[dict] | None:
    if not researcher.openalex_id:
        return None

    data_type = "author_works" # Standardized data_type string
    # For works, caching strategy might be more complex if pagination is involved.
    # This basic cache will store the result of the first 'max_pages' call.
    cached_data_entry = cache_crud.get_cached_openalex_data(db, researcher.id, data_type)
    if cached_data_entry:
        return json.loads(cached_data_entry.openalex_json_data)

    works_data = await get_author_works_from_openalex(
        researcher.openalex_id, email, per_page, max_pages
    )
    if works_data is not None: # Check for None, as empty list is a valid result
        cache_crud.store_openalex_data(
            db, researcher.id, data_type, json.dumps(works_data), cache_duration_seconds
        )
    return works_data
