from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from auth import crud, models as auth_models, schemas, security, auth_handler # models is database.models
from database import models as db_models # Renamed to avoid confusion
from database.database_setup import SessionLocal

router = APIRouter()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/users/register", response_model=schemas.UserPublic, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user_by_username = crud.get_user_by_username(db, username=user.username)
    if db_user_by_username:
        raise HTTPException(status_code=400, detail="Username already registered")
    db_user_by_email = crud.get_user_by_email(db, email=user.email)
    if db_user_by_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Correctly pass db_models.User to crud.create_user if it expects the SQLAlchemy model
    # However, crud.create_user is defined to use auth_models.User (which is database.models.User)
    # so the import structure in crud.py needs to be aligned.
    # For now, assuming crud.create_user uses the User model from its own 'models' import.
    created_user = crud.create_user(db=db, user=user)
    return created_user

@router.post("/users/login", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_handler.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=schemas.UserPublic)
async def read_users_me(current_user: db_models.User = Depends(auth_handler.get_current_active_user)):
    # current_user is of type db_models.User (aliased from database.models.User)
    # It should be compatible with schemas.UserPublic Pydantic model
    return current_user

# Placeholder for researcher routes, will be in a separate file
# from . import researcher_routes
# router.include_router(researcher_routes.router, prefix="/researchers", tags=["researchers"])
