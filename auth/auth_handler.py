from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

# Correcting the import for models to point to database.models
from database import models # Assuming models.py is in the database directory
from . import crud, schemas, security
from database.database_setup import SessionLocal

# Configure OAuth2PasswordBearer
# tokenUrl should point to the token generation endpoint, e.g., "/api/users/login"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login") # Adjusted to include /api prefix

# Helper to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15) # Default to 15 mins
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, security.SECRET_KEY, algorithm=security.ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: models.User = Depends(get_current_user)): # models.User will now correctly refer to database.models.User
    # Add any checks for active status here if needed, e.g. current_user.is_active
    return current_user
