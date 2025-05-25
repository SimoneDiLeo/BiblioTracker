from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError # To handle potential race conditions if a link already exists
from database import models # This correctly points to database/models.py
from typing import List

def get_or_create_topic(db: Session, topic_name: str, openalex_concept_id: str = None) -> models.ResearchTopic:
    """
    Gets a topic by name or OpenAlex concept ID, or creates it if not found.
    Prefers lookup by openalex_concept_id if provided and available.
    """
    topic = None
    if openalex_concept_id:
        topic = db.query(models.ResearchTopic).filter(models.ResearchTopic.openalex_concept_id == openalex_concept_id).first()
    
    if not topic: # If not found by concept_id or concept_id was not provided
        topic = db.query(models.ResearchTopic).filter(models.ResearchTopic.topic_name == topic_name).first()

    if not topic:
        new_topic = models.ResearchTopic(
            topic_name=topic_name,
            openalex_concept_id=openalex_concept_id
        )
        db.add(new_topic)
        try:
            db.commit()
            db.refresh(new_topic)
            return new_topic
        except IntegrityError: # Handles race condition if another session created it
            db.rollback()
            # Try fetching again, as it should exist now
            if openalex_concept_id:
                return db.query(models.ResearchTopic).filter(models.ResearchTopic.openalex_concept_id == openalex_concept_id).first()
            return db.query(models.ResearchTopic).filter(models.ResearchTopic.topic_name == topic_name).first()
    return topic

def link_researcher_to_topic(db: Session, researcher_id: int, topic_id: int):
    """
    Creates an association between a researcher and a topic.
    Ignores if the link already exists due to primary key constraint.
    """
    # Check if association already exists
    existing_link = db.query(models.ResearcherTopic).filter_by(
        researcher_id=researcher_id, 
        topic_id=topic_id
    ).first()

    if not existing_link:
        researcher_topic_link = models.ResearcherTopic(
            researcher_id=researcher_id,
            topic_id=topic_id
        )
        db.add(researcher_topic_link)
        try:
            db.commit()
        except IntegrityError:
            # This can happen if another session created the same link concurrently.
            # The primary key constraint on (researcher_id, topic_id) will prevent duplicates.
            db.rollback() 
            # The link either exists or the commit failed for another reason.
            # No need to re-raise unless specific error handling is needed.
    # If existing_link is found, do nothing.

def get_researcher_topics(db: Session, researcher_id: int) -> List[models.ResearchTopic]:
    """
    Fetches all topics associated with a researcher.
    """
    # Querying through the ResearcherTopic association table
    researcher_topic_associations = db.query(models.ResearcherTopic).filter(
        models.ResearcherTopic.researcher_id == researcher_id
    ).all()
    
    topics = [association.topic for association in researcher_topic_associations if association.topic]
    return topics
