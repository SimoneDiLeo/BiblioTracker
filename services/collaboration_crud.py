from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_ # for querying researcher1_id or researcher2_id
from database import models # This correctly points to database/models.py
from typing import List

def add_collaboration_suggestion(
    db: Session, 
    researcher1_id: int, 
    researcher2_id: int, 
    common_topic_id: int, 
    reason: str
) -> models.CollaborationSuggestion | None:
    """
    Adds a new collaboration suggestion if it doesn't already exist.
    Ensures researcher1_id < researcher2_id to avoid duplicate suggestions
    with IDs swapped.
    """
    # Ensure consistent ordering of researcher IDs to prevent duplicates
    if researcher1_id == researcher2_id:
        return None # Cannot suggest collaboration with oneself
    
    # Ensure r1_id < r2_id for storage to simplify uniqueness checks
    r1_id, r2_id = min(researcher1_id, researcher2_id), max(researcher1_id, researcher2_id)

    # Check if this suggestion already exists
    existing_suggestion = db.query(models.CollaborationSuggestion).filter_by(
        researcher1_id=r1_id,
        researcher2_id=r2_id,
        common_topic_id=common_topic_id
    ).first()

    if existing_suggestion:
        return existing_suggestion # Return existing if found

    new_suggestion = models.CollaborationSuggestion(
        researcher1_id=r1_id,
        researcher2_id=r2_id,
        common_topic_id=common_topic_id,
        suggestion_reason=reason
    )
    db.add(new_suggestion)
    try:
        db.commit()
        db.refresh(new_suggestion)
        return new_suggestion
    except IntegrityError: # Handles race condition or other integrity issues
        db.rollback()
        # Attempt to fetch again in case of race condition
        return db.query(models.CollaborationSuggestion).filter_by(
            researcher1_id=r1_id,
            researcher2_id=r2_id,
            common_topic_id=common_topic_id
        ).first()

def get_collaboration_suggestions(
    db: Session, 
    researcher_id: int, 
    limit: int = 10
) -> List[models.CollaborationSuggestion]:
    """
    Fetches collaboration suggestions for a given researcher.
    Includes suggestions where the researcher is either researcher1 or researcher2.
    """
    suggestions = db.query(models.CollaborationSuggestion).filter(
        or_(
            models.CollaborationSuggestion.researcher1_id == researcher_id,
            models.CollaborationSuggestion.researcher2_id == researcher_id
        )
    ).order_by(models.CollaborationSuggestion.generated_at.desc()).limit(limit).all()
    
    return suggestions
