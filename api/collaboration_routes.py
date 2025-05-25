from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from auth import auth_handler, crud as auth_crud
from database import models as db_models
from database.database_setup import SessionLocal
from services import (
    collaboration_service, 
    collaboration_crud, 
    topic_crud, # For the optional endpoint to list topics
    collaboration_schemas as c_schemas # Aliased
)
from config import OPENALEX_POLITE_EMAIL

collaboration_router = APIRouter(prefix="/api/collaborations", tags=["Collaborations & Topics"])

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@collaboration_router.post("/researchers/me/extract-topics", response_model=List[c_schemas.ResearchTopicPublic])
async def trigger_extract_my_research_topics(
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
            detail="OpenAlex ID not set for this researcher profile. Cannot extract topics."
        )
    
    email_for_api = OPENALEX_POLITE_EMAIL # Or user's email if preferred and handled for privacy

    # The service function extracts, stores, and returns the topics.
    extracted_db_topics = await collaboration_service.extract_and_store_researcher_topics(
        db=db, researcher=researcher_profile, openalex_email=email_for_api
    )
    
    # Convert SQLAlchemy models to Pydantic models for the response
    # This step is important if the service returns DB models directly.
    # If service already returns Pydantic models, this can be simplified.
    # Assuming extract_and_store_researcher_topics returns a list of db_models.ResearchTopic
    
    # The Pydantic models will be created from the db_topic objects
    # by FastAPI automatically due to response_model.
    return extracted_db_topics


@collaboration_router.get("/researchers/me/suggestions", response_model=List[c_schemas.CollaborationSuggestionPublic])
async def get_my_collaboration_suggestions(
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
            detail="OpenAlex ID not set for this researcher. Cannot generate suggestions."
        )

    email_for_api = OPENALEX_POLITE_EMAIL

    # This service function will internally call extract_and_store_researcher_topics
    # and then populate the suggestions table.
    await collaboration_service.generate_collaboration_suggestions(
        db=db, researcher=researcher_profile, openalex_email=email_for_api
    )

    # After suggestions are generated (or updated), fetch them.
    suggestions_db = collaboration_crud.get_collaboration_suggestions(
        db=db, researcher_id=researcher_profile.id, limit=20 # Example limit
    )
    
    # FastAPI will handle conversion to CollaborationSuggestionPublic due to response_model.
    return suggestions_db
