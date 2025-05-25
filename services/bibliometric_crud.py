from sqlalchemy.orm import Session
from database import models # This points to database/models.py
from datetime import datetime, timezone

def get_bibliometric_summary(db: Session, researcher_id: int) -> models.BibliometricSummary | None:
    """
    Fetches an existing bibliometric summary for a researcher.
    """
    return db.query(models.BibliometricSummary).filter(
        models.BibliometricSummary.researcher_id == researcher_id
    ).first()

def create_or_update_bibliometric_summary(
    db: Session, 
    researcher_id: int, 
    summary_data: dict, # Contains h_index, i10_index, total_publications, total_citations
    cache_id: int | None
) -> models.BibliometricSummary:
    """
    Creates a new bibliometric summary or updates an existing one for the researcher.
    """
    existing_summary = get_bibliometric_summary(db, researcher_id)

    if existing_summary:
        # Update existing summary
        existing_summary.h_index = summary_data.get('h_index')
        existing_summary.i10_index = summary_data.get('i10_index')
        existing_summary.total_publications = summary_data.get('total_publications')
        existing_summary.total_citations = summary_data.get('total_citations')
        existing_summary.last_updated_from_cache_id = cache_id
        existing_summary.summary_generated_at = datetime.now(timezone.utc) # Update timestamp
        summary_to_save = existing_summary
    else:
        # Create new summary
        new_summary = models.BibliometricSummary(
            researcher_id=researcher_id,
            h_index=summary_data.get('h_index'),
            i10_index=summary_data.get('i10_index'),
            total_publications=summary_data.get('total_publications'),
            total_citations=summary_data.get('total_citations'),
            last_updated_from_cache_id=cache_id,
            summary_generated_at=datetime.now(timezone.utc) # Set current timestamp
        )
        db.add(new_summary)
        summary_to_save = new_summary
    
    db.commit()
    db.refresh(summary_to_save)
    return summary_to_save
