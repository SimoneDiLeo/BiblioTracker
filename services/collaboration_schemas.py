from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ResearchTopicPublic(BaseModel):
    id: int
    topic_name: str
    openalex_concept_id: Optional[str] = None

    class Config:
        from_attributes = True

# For a more detailed suggestion, we might want to include researcher names and topic name
# This would require more complex query logic in the CRUD or service layer.
# For now, sticking to the basic model structure.
class CollaborationSuggestionResearcherInfo(BaseModel): # Sub-model for clarity
    id: int
    # Assuming we'll fetch basic info like username or full name for the researcher
    # For now, let's use ID, can be expanded later.
    # username: str # Example if User model is easily accessible
    # first_name: Optional[str] = None # Example if Researcher model is easily accessible
    # last_name: Optional[str] = None  # Example if Researcher model is easily accessible

class CollaborationSuggestionPublic(BaseModel):
    id: int
    researcher1_id: int
    researcher2_id: int
    common_topic_id: int
    # Optional: Include nested models for researcher1, researcher2, and common_topic
    # researcher1: Optional[CollaborationSuggestionResearcherInfo] = None
    # researcher2: Optional[CollaborationSuggestionResearcherInfo] = None
    # common_topic: Optional[ResearchTopicPublic] = None
    suggestion_reason: Optional[str] = None
    generated_at: datetime

    class Config:
        from_attributes = True
