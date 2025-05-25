from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import auth_handler, crud as auth_crud
from database import models as db_models
from database.database_setup import SessionLocal
from services import bibliometric_service, bibliometric_schemas as b_schemas # Aliased to avoid conflict
from config import OPENALEX_POLITE_EMAIL

bibliometric_router = APIRouter(prefix="/api/bibliometrics", tags=["Bibliometrics"])

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@bibliometric_router.get("/researchers/me/summary", response_model=b_schemas.BibliometricSummaryPublic)
async def get_my_bibliometric_summary(
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
            detail="OpenAlex ID not set for this researcher profile. Cannot generate bibliometric summary."
        )

    # For now, always regenerate the summary as per subtask instruction (Simpler Option 2)
    # Later, we could add logic to check if an existing summary is recent enough.
    
    email_for_api = OPENALEX_POLITE_EMAIL # Or pass current_user.email if that's preferred

    summary_model = await bibliometric_service.generate_researcher_bibliometric_summary(
        db=db, researcher=researcher_profile, openalex_email=email_for_api
    )

    if not summary_model:
        # This could be due to various reasons: OpenAlex ID invalid, API error, no works, etc.
        # The service layer should log more details.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, # Or 404 if no data from OpenAlex
            detail="Could not generate or retrieve bibliometric summary for the researcher."
        )
    
    # The summary_model is an SQLAlchemy model instance.
    # Pydantic's from_attributes (orm_mode) will handle the conversion.
    return summary_model
