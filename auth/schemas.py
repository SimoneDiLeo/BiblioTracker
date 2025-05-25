from pydantic import BaseModel, EmailStr
from typing import Optional

# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserInDBBase(UserBase):
    id: int
    hashed_password: str

    class Config:
        from_attributes = True # Pydantic V2

class UserPublic(UserBase):
    id: int

    class Config:
        from_attributes = True # Pydantic V2

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Researcher Schemas
class ResearcherBase(BaseModel):
    first_name: str
    last_name: str
    affiliation: Optional[str] = None
    openalex_id: Optional[str] = None

class ResearcherCreate(ResearcherBase):
    pass

class ResearcherUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    affiliation: Optional[str] = None
    openalex_id: Optional[str] = None

class ResearcherPublic(ResearcherBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True # Pydantic V2
