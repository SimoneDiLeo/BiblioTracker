from sqlalchemy.orm import Session
# Correcting the import for models to point to database.models
from database import models # Assuming models.py is in the database directory
from . import schemas, security

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User( # This will now correctly refer to database.models.User
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Researcher CRUD functions
def get_researcher_by_user_id(db: Session, user_id: int):
    return db.query(models.Researcher).filter(models.Researcher.user_id == user_id).first()

def create_researcher_profile(db: Session, researcher: schemas.ResearcherCreate, user_id: int):
    db_researcher = models.Researcher(**researcher.model_dump(), user_id=user_id)
    db.add(db_researcher)
    db.commit()
    db.refresh(db_researcher)
    return db_researcher

def get_researcher_by_id(db: Session, researcher_id: int):
    return db.query(models.Researcher).filter(models.Researcher.id == researcher_id).first()

def update_researcher_profile(db: Session, researcher: models.Researcher, researcher_update_data: schemas.ResearcherUpdate):
    update_data = researcher_update_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(researcher, key, value)
    db.add(researcher)
    db.commit()
    db.refresh(researcher)
    return researcher

def delete_researcher_profile(db: Session, researcher: models.Researcher):
    db.delete(researcher)
    db.commit()
    # The 'researcher' object is no longer valid after deletion from the session.
    # Depending on the use case, you might return the object as it was before deletion,
    # or simply return None or a success status. For now, returning the object.
    # However, accessing its attributes after commit might lead to errors if not handled carefully.
    return researcher
