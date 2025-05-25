import json
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import models # This correctly points to database/models.py
from datetime import datetime, timezone

def create_or_update_profile_analysis(
    db: Session, 
    researcher_id: int, 
    analysis_type: str, 
    result_data: dict # Python dictionary to be serialized to JSON
) -> models.ProfileAnalysisResult:
    """
    Creates a new profile analysis result or updates an existing one 
    for the given researcher and analysis type.
    """
    existing_analysis = db.query(models.ProfileAnalysisResult).filter_by(
        researcher_id=researcher_id,
        analysis_type=analysis_type
    ).first()

    json_result_data = json.dumps(result_data) # Serialize dict to JSON string

    if existing_analysis:
        existing_analysis.result_data = json_result_data
        existing_analysis.generated_at = datetime.now(timezone.utc) # Update timestamp
        analysis_to_save = existing_analysis
    else:
        new_analysis = models.ProfileAnalysisResult(
            researcher_id=researcher_id,
            analysis_type=analysis_type,
            result_data=json_result_data,
            generated_at=datetime.now(timezone.utc) # Set current timestamp
        )
        db.add(new_analysis)
        analysis_to_save = new_analysis
    
    try:
        db.commit()
        db.refresh(analysis_to_save)
        return analysis_to_save
    except IntegrityError: # Should ideally not happen if unique constraint is handled by prior check
        db.rollback()
        # Re-fetch in case of a race condition, though the first query should handle most cases
        return db.query(models.ProfileAnalysisResult).filter_by(
            researcher_id=researcher_id,
            analysis_type=analysis_type
        ).first()


def get_profile_analysis(
    db: Session, 
    researcher_id: int, 
    analysis_type: str
) -> models.ProfileAnalysisResult | None:
    """
    Retrieves a specific profile analysis result for a researcher.
    """
    return db.query(models.ProfileAnalysisResult).filter_by(
        researcher_id=researcher_id,
        analysis_type=analysis_type
    ).first()
