from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import crud, schemas, auth_handler # Using existing auth_handler for current_user
from database import models as db_models # Using the same alias as in auth_routes
from database.database_setup import SessionLocal

router = APIRouter()

# Dependency to get DB session (can be shared or defined in a common place)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.ResearcherPublic, status_code=status.HTTP_201_CREATED)
def create_researcher_profile_for_current_user(
    researcher_data: schemas.ResearcherCreate,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(auth_handler.get_current_active_user)
):
    # Check if a researcher profile already exists for this user
    existing_researcher = crud.get_researcher_by_user_id(db, user_id=current_user.id)
    if existing_researcher:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Researcher profile already exists for this user."
        )
    
    created_researcher = crud.create_researcher_profile(db=db, researcher=researcher_data, user_id=current_user.id)
    return created_researcher

@router.get("/me", response_model=schemas.ResearcherPublic)
def read_researcher_profile_me(
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(auth_handler.get_current_active_user)
):
    researcher_profile = crud.get_researcher_by_user_id(db, user_id=current_user.id)
    if not researcher_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Researcher profile not found for the current user."
        )
    return researcher_profile

@router.get("/{researcher_id}", response_model=schemas.ResearcherPublic)
def read_researcher_profile_by_id(
    researcher_id: int,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(auth_handler.get_current_active_user) # Authenticated user check
):
    # TODO: Add more granular permissions if needed (e.g., admin or owner)
    researcher = crud.get_researcher_by_id(db, researcher_id=researcher_id)
    if not researcher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Researcher profile with ID {researcher_id} not found."
        )
    return researcher

@router.put("/me", response_model=schemas.ResearcherPublic)
def update_researcher_profile_me(
    researcher_update_data: schemas.ResearcherUpdate,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(auth_handler.get_current_active_user)
):
    researcher_profile = crud.get_researcher_by_user_id(db, user_id=current_user.id)
    if not researcher_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Researcher profile not found for the current user to update."
        )
    
    updated_profile = crud.update_researcher_profile(
        db=db, researcher=researcher_profile, researcher_update_data=researcher_update_data
    )
    return updated_profile

@router.delete("/me", response_model=schemas.ResearcherPublic) # Or perhaps a status code 204 with no content
def delete_researcher_profile_me(
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(auth_handler.get_current_active_user)
):
    researcher_profile = crud.get_researcher_by_user_id(db, user_id=current_user.id)
    if not researcher_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Researcher profile not found for the current user to delete."
        )
    
    deleted_profile = crud.delete_researcher_profile(db=db, researcher=researcher_profile)
    # Note: Accessing attributes of deleted_profile after this point might be problematic
    # if the session has expired or the object is no longer managed.
    # Returning the object as is, but for a DELETE, often a 204 No Content is preferred.
    return deleted_profile
