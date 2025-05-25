import json
from sqlalchemy.orm import Session
from sqlalchemy.sql import func # For func.now() if needed, though models handle it
from database import models as db_models # Renamed to avoid conflict
from services import (
    openalex_service, 
    topic_crud, 
    collaboration_crud, 
    cache_crud # To potentially get cache entry for OpenAlex profile
)
from config import OPENALEX_POLITE_EMAIL

async def extract_and_store_researcher_topics(
    db: Session, 
    researcher: db_models.Researcher, 
    openalex_email: str = None
):
    """
    Fetches researcher's OpenAlex profile, extracts concepts/topics,
    and stores them, linking them to the researcher.
    """
    if not researcher.openalex_id:
        print(f"Researcher {researcher.id} has no OpenAlex ID. Cannot extract topics.")
        return [] # Return empty list or raise error

    email_for_api = openalex_email or OPENALEX_POLITE_EMAIL

    # Fetch OpenAlex author profile data (this handles caching)
    author_profile_dict = await openalex_service.fetch_and_cache_researcher_openalex_profile(
        db=db, researcher=researcher, email=email_for_api
    )

    if not author_profile_dict or 'x_concepts' not in author_profile_dict:
        print(f"No concepts found in OpenAlex profile for researcher {researcher.id}.")
        return []

    extracted_topics = []
    concepts = author_profile_dict.get('x_concepts', [])
    
    # Filter concepts (e.g., by level or score if desired)
    # For now, let's take concepts with level 0 or 1, or a certain score threshold
    # Example: concepts_to_process = [c for c in concepts if c.get('level') <= 1 and c.get('score', 0) > 0.3]
    # For simplicity, we'll process all concepts returned for now.
    concepts_to_process = concepts

    for concept_data in concepts_to_process:
        topic_name = concept_data.get('display_name')
        openalex_concept_url = concept_data.get('id') # This is the full URL like "https://openalex.org/Cxxxx"
        
        # Extract the concept ID part from the URL if it's a URL
        openalex_concept_id_only = None
        if openalex_concept_url and openalex_concept_url.startswith("https://openalex.org/"):
            openalex_concept_id_only = openalex_concept_url.split("/")[-1]

        if topic_name: # Ensure topic_name is present
            db_topic = topic_crud.get_or_create_topic(
                db, 
                topic_name=topic_name, 
                openalex_concept_id=openalex_concept_id_only # Store only the ID part
            )
            topic_crud.link_researcher_to_topic(db, researcher.id, db_topic.id)
            extracted_topics.append(db_topic)
            
    return extracted_topics


async def generate_collaboration_suggestions(
    db: Session, 
    researcher: db_models.Researcher, 
    openalex_email: str = None
):
    """
    Generates collaboration suggestions for a researcher based on shared topics.
    """
    email_for_api = openalex_email or OPENALEX_POLITE_EMAIL

    # 1. Ensure topics for the current researcher are extracted and stored.
    await extract_and_store_researcher_topics(db, researcher, email_for_api)

    # 2. Get the researcher's topics.
    researcher_topics = topic_crud.get_researcher_topics(db, researcher.id)
    if not researcher_topics:
        print(f"No topics found for researcher {researcher.id} to generate suggestions.")
        return

    # 3. For each topic, find other researchers and create suggestions.
    for topic in researcher_topics:
        # Find other researchers linked to this topic
        # The ResearcherTopic model has 'researcher' and 'topic' relationships.
        # We need to query ResearcherTopic for all entries with topic.id, excluding current researcher.id
        
        # Querying all ResearcherTopic associations for the current topic
        topic_associations = db.query(db_models.ResearcherTopic).filter(
            db_models.ResearcherTopic.topic_id == topic.id,
            db_models.ResearcherTopic.researcher_id != researcher.id # Exclude current researcher
        ).all()

        for association in topic_associations:
            other_researcher_id = association.researcher_id
            
            # Create suggestion
            reason = f"Shared research interest in: {topic.topic_name}"
            collaboration_crud.add_collaboration_suggestion(
                db=db,
                researcher1_id=researcher.id,
                researcher2_id=other_researcher_id,
                common_topic_id=topic.id,
                reason=reason
            )
            # The add_collaboration_suggestion handles uniqueness and ordering of IDs.
            
    # Note: This function doesn't return the suggestions directly,
    # it populates the CollaborationSuggestion table.
    # The API endpoint will then query this table.
