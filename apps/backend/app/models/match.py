from sqlalchemy.types import JSON
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime, text, Float

from .base import Base


class ResumeJobMatch(Base):
    __tablename__ = "resume_job_matches"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(
        String,
        ForeignKey("processed_resumes.resume_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_id = Column(
        String,
        ForeignKey("processed_jobs.job_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Match scoring results
    overall_match_score = Column(Float, nullable=False)  # Overall compatibility score (0.0-1.0)
    skills_match_score = Column(Float, nullable=True)  # Skills compatibility (0.0-1.0)
    experience_match_score = Column(Float, nullable=True)  # Experience compatibility (0.0-1.0)
    education_match_score = Column(Float, nullable=True)  # Education compatibility (0.0-1.0)
    keywords_match_score = Column(Float, nullable=True)  # Keywords compatibility (0.0-1.0)
    
    # Detailed match analysis
    match_analysis = Column(JSON, nullable=True)  # Detailed analysis results
    improvement_suggestions = Column(JSON, nullable=True)  # AI-generated improvement suggestions
    missing_skills = Column(JSON, nullable=True)  # Skills missing from resume
    matching_skills = Column(JSON, nullable=True)  # Skills that match
    gap_analysis = Column(JSON, nullable=True)  # Detailed gap analysis
    
    # Analysis metadata
    analysis_version = Column(String, nullable=True)  # Version of analysis algorithm used
    created_at = Column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
        index=True,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    # Relationships
    resume = relationship("ProcessedResume", foreign_keys=[resume_id])
    job = relationship("ProcessedJob", foreign_keys=[job_id])