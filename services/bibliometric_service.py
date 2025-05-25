import json
from sqlalchemy.orm import Session
from database import models as db_models # Renamed to avoid conflict
from services import openalex_service, bibliometric_utils, bibliometric_crud, cache_crud
from config import OPENALEX_POLITE_EMAIL

async def generate_researcher_bibliometric_summary(
    db: Session, 
    researcher: db_models.Researcher, 
    openalex_email: str = None
) -> db_models.BibliometricSummary | None:
    """
    Generates (or updates) a bibliometric summary for a researcher using OpenAlex data.
    """
    if not researcher.openalex_id:
        # Log this or raise specific exception
        print(f"Researcher {researcher.id} has no OpenAlex ID. Cannot generate summary.")
        return None

    email_for_api = openalex_email or OPENALEX_POLITE_EMAIL

    # 1. Fetch OpenAlex author profile data
    # Assuming fetch_and_cache_researcher_openalex_profile returns the data and stores cache entry
    # We need the cache entry ID for linking the summary.
    
    # First, fetch the raw data (this function handles caching internally)
    author_profile_dict = await openalex_service.fetch_and_cache_researcher_openalex_profile(
        db=db, researcher=researcher, email=email_for_api
    )
    if not author_profile_dict:
        print(f"Could not fetch OpenAlex profile for researcher {researcher.id} (OpenAlex ID: {researcher.openalex_id}).")
        return None
    
    # Retrieve the cache entry that was just created/updated for the profile
    profile_cache_entry = cache_crud.get_cached_openalex_data(db, researcher.id, "author_profile")
    profile_cache_id = profile_cache_entry.id if profile_cache_entry else None


    # 2. Fetch OpenAlex works data
    # Similar logic for works data
    works_data_list = await openalex_service.fetch_and_cache_researcher_openalex_works(
        db=db, researcher=researcher, email=email_for_api, max_pages=5 # Fetch more pages for better summary
    )
    if works_data_list is None: # Could be an empty list for no works, None for error
        print(f"Could not fetch OpenAlex works for researcher {researcher.id} (OpenAlex ID: {researcher.openalex_id}).")
        # Depending on requirements, we might proceed with only profile data or return None
        return None # For now, require works data for full summary

    works_cache_entry = cache_crud.get_cached_openalex_data(db, researcher.id, "author_works")
    works_cache_id = works_cache_entry.id if works_cache_entry else None

    # Determine the most recent cache ID to link. Could be more sophisticated.
    # For simplicity, we can pick one, e.g., works_cache_id if available, else profile_cache_id.
    # Or, if we want to be precise, store both or have a separate linkage.
    # The current model `last_updated_from_cache_id` takes one. Let's use works_cache_id as it's often more dynamic.
    linked_cache_id = works_cache_id or profile_cache_id

    # 3. Extract and Calculate Metrics
    # Total publications and citations from profile (as per OpenAlex definitions)
    total_publications = author_profile_dict.get('works_count', 0)
    total_citations_from_profile = author_profile_dict.get('cited_by_count', 0)

    # Extract citation counts from each work for h-index and i10-index calculation
    citation_counts_from_works = []
    for work in works_data_list:
        if isinstance(work, dict) and work.get('cited_by_count') is not None:
            citation_counts_from_works.append(work['cited_by_count'])
        # else: print(f"Warning: Work item format unexpected or missing cited_by_count: {work}")


    h_index = bibliometric_utils.calculate_h_index(citation_counts_from_works)
    i10_index = bibliometric_utils.calculate_i10_index(citation_counts_from_works)
    
    # We can also sum citations from works if preferred over profile's cited_by_count
    # total_citations_from_works = sum(citation_counts_from_works)

    summary_data = {
        'h_index': h_index,
        'i10_index': i10_index,
        'total_publications': total_publications,
        'total_citations': total_citations_from_profile, # Using profile's count
    }

    # 4. Store the summary
    db_summary = bibliometric_crud.create_or_update_bibliometric_summary(
        db=db, 
        researcher_id=researcher.id, 
        summary_data=summary_data,
        cache_id=linked_cache_id 
    )
    
    return db_summary
