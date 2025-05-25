import json
from sqlalchemy.orm import Session
from database import models as db_models # Renamed to avoid conflict
from services import (
    openalex_service, 
    analysis_crud
    # No direct need for openalex_schemas here unless we re-validate OpenAlex data
)
from config import OPENALEX_POLITE_EMAIL
# Import the Pydantic models for structuring the result_data
from .analysis_schemas import ConceptSummaryData, ResearcherConceptSummaryResult

async def generate_researcher_concept_summary(
    db: Session, 
    researcher: db_models.Researcher, 
    openalex_email: str = None
) -> db_models.ProfileAnalysisResult | None:
    """
    Generates a summary of a researcher's concepts based on their OpenAlex profile.
    Stores this summary in the ProfileAnalysisResult table.
    """
    if not researcher.openalex_id:
        print(f"Researcher {researcher.id} has no OpenAlex ID. Cannot generate concept summary.")
        return None

    email_for_api = openalex_email or OPENALEX_POLITE_EMAIL

    # 1. Fetch OpenAlex author profile data (this handles caching)
    author_profile_dict = await openalex_service.fetch_and_cache_researcher_openalex_profile(
        db=db, researcher=researcher, email=email_for_api
    )

    if not author_profile_dict or 'x_concepts' not in author_profile_dict:
        print(f"No concepts found in OpenAlex profile for researcher {researcher.id}.")
        # Optionally, store an empty result or a specific marker if needed
        # For now, return None if no concepts to process
        return None

    # 2. Transform x_concepts data
    concepts_data_list = []
    openalex_concepts = author_profile_dict.get('x_concepts', [])

    for concept in openalex_concepts:
        # Using .get() for safety, though OpenAlex schema is usually consistent
        concept_id_url = concept.get('id')
        display_name = concept.get('display_name')
        level = concept.get('level')
        score = concept.get('score')

        if concept_id_url and display_name is not None and level is not None and score is not None:
            concepts_data_list.append(
                ConceptSummaryData(
                    concept_id=concept_id_url, # Store the full OpenAlex URL as ID
                    display_name=display_name,
                    level=level,
                    score=score
                )
            )
        # else: print(f"Skipping concept due to missing data: {concept}")


    # Prepare the result_data structure
    # The Pydantic model ResearcherConceptSummaryResult ensures the structure
    # .model_dump() converts it to a dict, which will then be JSON serialized by analysis_crud
    structured_result_data = ResearcherConceptSummaryResult(concepts=concepts_data_list)
    
    analysis_type = "researcher_concept_summary"

    # 3. Store this using analysis_crud
    db_analysis_result = analysis_crud.create_or_update_profile_analysis(
        db=db,
        researcher_id=researcher.id,
        analysis_type=analysis_type,
        result_data=structured_result_data.model_dump() # Pass the dict
    )
    
    return db_analysis_result
