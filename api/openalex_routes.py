from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import auth_handler, crud as auth_crud # For getting current user and their researcher profile
from database import models as db_models
from database.database_setup import SessionLocal
from services import openalex_service, openalex_schemas # OpenAlex service and schemas
from config import OPENALEX_POLITE_EMAIL # For providing an email to OpenAlex API

openalex_router = APIRouter(prefix="/api/openalex", tags=["OpenAlex Integration"])

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@openalex_router.get("/researchers/me/openalex-profile", response_model=openalex_schemas.OpenAlexAuthor)
async def get_my_openalex_profile(
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
            detail="OpenAlex ID not set for this researcher profile. Please update the profile."
        )

    # Use the polite email from config if available, or let the service use its default
    email_for_api = OPENALEX_POLITE_EMAIL 

    author_data_dict = await openalex_service.fetch_and_cache_researcher_openalex_profile(
        db=db, researcher=researcher_profile, email=email_for_api
    )
    
    if not author_data_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not fetch OpenAlex profile for ID: {researcher_profile.openalex_id}"
        )
    
    # Validate and return using Pydantic model
    # The service returns a dict, which Pydantic can parse
    return openalex_schemas.OpenAlexAuthor(**author_data_dict)


@openalex_router.get("/researchers/me/openalex-works", response_model=list[openalex_schemas.OpenAlexWork])
async def get_my_openalex_works(
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(auth_handler.get_current_active_user),
    per_page: int = 25, # Allow client to suggest pagination, with service defaults
    max_pages: int = 1   # Allow client to suggest pagination, with service defaults
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
            detail="OpenAlex ID not set for this researcher profile. Please update the profile."
        )

    email_for_api = OPENALEX_POLITE_EMAIL

    works_data_list = await openalex_service.fetch_and_cache_researcher_openalex_works(
        db=db, 
        researcher=researcher_profile, 
        email=email_for_api,
        per_page=per_page,
        max_pages=max_pages
    )

    if works_data_list is None: # Service returns None on error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, # Or 404 if ID was valid but no works/error during fetch
            detail=f"Could not fetch works from OpenAlex for ID: {researcher_profile.openalex_id}"
        )
    
    # Validate and return list of Pydantic models
    return [openalex_schemas.OpenAlexWork(**work) for work in works_data_list]
