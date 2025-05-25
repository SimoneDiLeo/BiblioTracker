from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class BibliometricSummaryPublic(BaseModel):
    id: int
    researcher_id: int
    h_index: Optional[int] = None
    i10_index: Optional[int] = None
    total_publications: Optional[int] = None
    total_citations: Optional[int] = None
    summary_generated_at: datetime
    last_updated_from_cache_id: Optional[int] = None

    class Config:
        from_attributes = True # For Pydantic V2 compatibility with ORM models
