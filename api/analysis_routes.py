from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import json # For parsing the JSON string if needed, though Pydantic can handle it

from auth import auth_handler, crud as auth_crud
from database import models as db_models
from database.database_setup import SessionLocal
from services import (
    analysis_service, 
    analysis_schemas as a_schemas # Aliased
)
from config import OPENALEX_POLITE_EMAIL

analysis_router = APIRouter(prefix="/api/analysis", tags=["Analysis"])

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@analysis_router.get("/researchers/me/concept-summary", response_model=a_schemas.ProfileAnalysisResultPublic)
async def get_my_concept_summary(
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(auth_handler.get_current_active_user)
):
    researcher_profile = auth_crud.get_researcher_by_user_id(db, user_id=current_user.id)
    if not researcher_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Researcher profile not found for the current user."
        )
    if not researcher_profile.openalex_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OpenAlex ID not set for this researcher profile. Cannot generate concept summary."
        )

    email_for_api = OPENALEX_POLITE_EMAIL # Or user's email if preferred

    # This service function generates and stores (or updates) the analysis result.
    analysis_result_db = await analysis_service.generate_researcher_concept_summary(
        db=db, researcher=researcher_profile, openalex_email=email_for_api
    )

    if not analysis_result_db:
        # This could mean no concepts were found, or an error occurred during OpenAlex fetch.
        # The service layer should log specifics.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, # Or 500 if it implies an unexpected error
            detail="Could not generate or retrieve concept summary for the researcher. No concepts found or OpenAlex API error."
        )

    # The analysis_result_db.result_data is a JSON string.
    # The ProfileAnalysisResultPublic schema has result_data typed as Json[ResearcherConceptSummaryResult].
    # FastAPI/Pydantic will automatically parse the JSON string into the nested Pydantic model
    # when serializing the response. So, no manual parsing (json.loads) is needed here if using Pydantic v2 with Json type.
    # If not using Json[] type hint in Pydantic schema, then manual parsing would be:
    # parsed_data = json.loads(analysis_result_db.result_data)
    # return {**analysis_result_db.__dict__, "result_data": parsed_data} # Example, not ideal
    
    return analysis_result_db
