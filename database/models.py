from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database_setup import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    researcher = relationship("Researcher", back_populates="user", uselist=False)

class Researcher(Base):
    __tablename__ = "researchers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False) # A researcher profile is unique to a user
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    affiliation = Column(String, nullable=True)
    openalex_id = Column(String, unique=True, nullable=True, index=True) # Unique, can be added later
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="researcher")
    caches = relationship("OpenAlexDataCache", back_populates="researcher_profile", cascade="all, delete-orphan")
    summary = relationship("BibliometricSummary", back_populates="researcher", uselist=False, cascade="all, delete-orphan") # Added this line

    __table_args__ = (UniqueConstraint('user_id', name='_user_researcher_uc'),)

class OpenAlexDataCache(Base):
    __tablename__ = "openalex_data_cache"

    id = Column(Integer, primary_key=True, index=True)
    researcher_id = Column(Integer, ForeignKey("researchers.id"), nullable=False)
    data_type = Column(String, nullable=False) # E.g., "author_profile", "author_works"
    openalex_json_data = Column(String, nullable=False) # Storing the JSON response as TEXT
    fetched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    researcher_profile = relationship("Researcher", back_populates="caches")

    __table_args__ = (UniqueConstraint('researcher_id', 'data_type', name='uq_researcher_data_type'),)

class BibliometricSummary(Base):
    __tablename__ = "bibliometric_summaries"

    id = Column(Integer, primary_key=True, index=True)
    researcher_id = Column(Integer, ForeignKey("researchers.id"), unique=True, nullable=False, index=True)
    h_index = Column(Integer, nullable=True) # Nullable if calculation is not possible
    i10_index = Column(Integer, nullable=True)
    total_publications = Column(Integer, nullable=True)
    total_citations = Column(Integer, nullable=True)
    summary_generated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_updated_from_cache_id = Column(Integer, ForeignKey("openalex_data_cache.id"), nullable=True)

    researcher = relationship("Researcher", back_populates="summary") # Corrected back_populates
    # cache_entry = relationship("OpenAlexDataCache") # Relationship to the specific cache entry used

# New Models for Collaboration and Topics

class ResearchTopic(Base):
    __tablename__ = "research_topics"

    id = Column(Integer, primary_key=True, index=True)
    topic_name = Column(String, unique=True, nullable=False, index=True) # Changed TEXT to String for broader DB compatibility
    openalex_concept_id = Column(String, unique=True, nullable=True, index=True) # Changed TEXT to String

    # Relationship to ResearcherTopic (many-to-many)
    researchers = relationship("ResearcherTopic", back_populates="topic")

class ResearcherTopic(Base):
    __tablename__ = "researcher_topics"

    researcher_id = Column(Integer, ForeignKey("researchers.id"), primary_key=True)
    topic_id = Column(Integer, ForeignKey("research_topics.id"), primary_key=True)
    
    # Relationships to allow querying from Researcher or ResearchTopic
    researcher = relationship("Researcher", back_populates="topics_associated")
    topic = relationship("ResearchTopic", back_populates="researchers")

class CollaborationSuggestion(Base):
    __tablename__ = "collaboration_suggestions"

    id = Column(Integer, primary_key=True, index=True)
    researcher1_id = Column(Integer, ForeignKey("researchers.id"), nullable=False)
    researcher2_id = Column(Integer, ForeignKey("researchers.id"), nullable=False)
    common_topic_id = Column(Integer, ForeignKey("research_topics.id"), nullable=False)
    suggestion_reason = Column(String, nullable=True) # Changed TEXT to String
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships for easier querying, adjust as needed
    researcher1 = relationship("Researcher", foreign_keys=[researcher1_id])
    researcher2 = relationship("Researcher", foreign_keys=[researcher2_id])
    common_topic = relationship("ResearchTopic")

    __table_args__ = (
        UniqueConstraint('researcher1_id', 'researcher2_id', 'common_topic_id', name='uq_collaboration_suggestion'),
        # Potentially a check constraint to ensure researcher1_id != researcher2_id
        # CheckConstraint('researcher1_id < researcher2_id', name='ck_researcher_order') # To avoid duplicate suggestions in reverse order
    )

class ProfileAnalysisResult(Base):
    __tablename__ = "profile_analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    researcher_id = Column(Integer, ForeignKey("researchers.id"), nullable=False)
    analysis_type = Column(String, nullable=False) # e.g., "researcher_concept_summary"
    result_data = Column(String, nullable=False)  # JSON string
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    researcher = relationship("Researcher", back_populates="analysis_results")

    __table_args__ = (
        UniqueConstraint('researcher_id', 'analysis_type', name='uq_researcher_analysis_type'),
    )
