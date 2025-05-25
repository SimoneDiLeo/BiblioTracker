from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any

class OpenAlexBase(BaseModel):
    id: HttpUrl # OpenAlex ID is a URL

class InstitutionBrief(BaseModel):
    id: Optional[HttpUrl] = None
    display_name: Optional[str] = None
    ror: Optional[HttpUrl] = None
    country_code: Optional[str] = None
    type: Optional[str] = None

class ConceptBrief(BaseModel):
    id: Optional[HttpUrl] = None
    wikidata: Optional[HttpUrl] = None
    display_name: Optional[str] = None
    level: Optional[int] = None
    score: Optional[float] = None

class OpenAlexIds(BaseModel):
    openalex: Optional[HttpUrl] = None
    orcid: Optional[HttpUrl] = None
    scopus: Optional[str] = None # Scopus ID is usually like "authid/xxxx"
    twitter: Optional[HttpUrl] = None
    wikipedia: Optional[HttpUrl] = None
    mag: Optional[str] = None # Microsoft Academic Graph ID

class OpenAlexAuthor(OpenAlexBase):
    display_name: str
    works_count: Optional[int] = None
    cited_by_count: Optional[int] = None
    ids: Optional[OpenAlexIds] = None
    last_known_institution: Optional[InstitutionBrief] = None
    x_concepts: Optional[List[ConceptBrief]] = [] # List of concepts associated with the author
    orcid: Optional[str] = None # Often available directly
    
    class Config:
        from_attributes = True

class Authorship(BaseModel):
    author_position: Optional[str] = None # e.g. "first", "last", "middle"
    author: Optional[OpenAlexAuthor] = None # Simplified author representation
    institutions: Optional[List[InstitutionBrief]] = []
    raw_affiliation_string: Optional[str] = None

class Source(BaseModel): # Simplified representation of a journal or repository
    id: Optional[HttpUrl] = None
    display_name: Optional[str] = None
    issn_l: Optional[str] = None
    issn: Optional[List[str]] = None
    type: Optional[str] = None

class PrimaryLocation(BaseModel):
    source: Optional[Source] = None
    landing_page_url: Optional[HttpUrl] = None
    pdf_url: Optional[HttpUrl] = None
    is_oa: Optional[bool] = None
    version: Optional[str] = None
    license: Optional[str] = None

class OpenAlexWork(OpenAlexBase):
    title: str
    publication_year: Optional[int] = None
    type: Optional[str] = None
    cited_by_count: Optional[int] = None
    authorships: Optional[List[Authorship]] = []
    primary_location: Optional[PrimaryLocation] = None
    # Add other fields as needed, e.g., concepts, grants, referenced_works

    class Config:
        from_attributes = True
