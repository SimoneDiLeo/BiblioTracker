from sqlalchemy.orm import Session
from database import models # This should correctly point to database/models.py
from datetime import datetime, timedelta, timezone

def get_cached_openalex_data(db: Session, researcher_id: int, data_type: str) -> models.OpenAlexDataCache | None:
    """
    Retrieves cached OpenAlex data if it exists and has not expired.
    """
    current_time = datetime.now(timezone.utc)
    cache_entry = db.query(models.OpenAlexDataCache).filter(
        models.OpenAlexDataCache.researcher_id == researcher_id,
        models.OpenAlexDataCache.data_type == data_type,
        models.OpenAlexDataCache.expires_at > current_time
    ).first()
    return cache_entry

def store_openalex_data(
    db: Session, 
    researcher_id: int, 
    data_type: str, 
    data: str, # JSON string data
    cache_duration_seconds: int
) -> models.OpenAlexDataCache:
    """
    Stores or updates OpenAlex data in the cache.
    Sets fetched_at to current time and calculates expires_at.
    """
    fetched_at = datetime.now(timezone.utc)
    expires_at = fetched_at + timedelta(seconds=cache_duration_seconds)

    # Check if an entry already exists to update it (upsert logic)
    cache_entry = db.query(models.OpenAlexDataCache).filter(
        models.OpenAlexDataCache.researcher_id == researcher_id,
        models.OpenAlexDataCache.data_type == data_type
    ).first()

    if cache_entry:
        cache_entry.openalex_json_data = data
        cache_entry.fetched_at = fetched_at
        cache_entry.expires_at = expires_at
    else:
        cache_entry = models.OpenAlexDataCache(
            researcher_id=researcher_id,
            data_type=data_type,
            openalex_json_data=data,
            fetched_at=fetched_at,
            expires_at=expires_at
        )
        db.add(cache_entry)
    
    db.commit()
    db.refresh(cache_entry)
    return cache_entry
