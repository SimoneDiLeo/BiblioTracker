from pydantic import BaseModel, Json
from typing import Optional, List
from datetime import datetime

# Pydantic model for the data stored in result_data for concept summary
class ConceptSummaryData(BaseModel):
    concept_id: str # This will be the OpenAlex ID URL
    display_name: str
    level: int
    score: float

class ResearcherConceptSummaryResult(BaseModel):
    concepts: List[ConceptSummaryData]

# Pydantic model for the ProfileAnalysisResult table
class ProfileAnalysisResultPublic(BaseModel):
    id: int
    researcher_id: int
    analysis_type: str
    result_data: Json[ResearcherConceptSummaryResult] # Specify that result_data is JSON and can be parsed into ResearcherConceptSummaryResult
    generated_at: datetime

    class Config:
        from_attributes = True # For Pydantic V2 compatibility with ORM models

# If you want an endpoint to return the raw JSON string instead of parsed:
class ProfileAnalysisResultRawPublic(BaseModel):
    id: int
    researcher_id: int
    analysis_type: str
    result_data: str # Raw JSON string
    generated_at: datetime

    class Config:
        from_attributes = True
