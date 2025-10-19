from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class AIAnalysisScores(BaseModel):
    """AI analysis scores for resume processing"""
    ats_compatibility: Optional[int] = Field(None, ge=0, le=100, description="ATS compatibility score")
    keyword_density: Optional[int] = Field(None, ge=0, le=100, description="Keyword density score")
    structure_quality: Optional[int] = Field(None, ge=0, le=100, description="Resume structure score")
    content_relevance: Optional[int] = Field(None, ge=0, le=100, description="Content relevance score")
    overall_score: Optional[int] = Field(None, ge=0, le=100, description="Overall AI analysis score")


class AIFeedback(BaseModel):
    """AI-generated feedback and suggestions"""
    strengths: List[str] = Field(default_factory=list, description="Resume strengths identified by AI")
    weaknesses: List[str] = Field(default_factory=list, description="Areas for improvement")
    suggestions: List[str] = Field(default_factory=list, description="Specific improvement suggestions")
    missing_elements: List[str] = Field(default_factory=list, description="Missing resume elements")
    ats_recommendations: List[str] = Field(default_factory=list, description="ATS optimization recommendations")


class AnalysisMetadata(BaseModel):
    """Metadata about the analysis process"""
    analysis_version: Optional[str] = Field(None, description="Version of analysis algorithm")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    ai_model_used: Optional[str] = Field(None, description="AI model used for analysis")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence in analysis")
    error_messages: List[str] = Field(default_factory=list, description="Any errors during processing")


class MatchAnalysis(BaseModel):
    """Detailed analysis of resume-job matching"""
    skills_analysis: Dict[str, Any] = Field(default_factory=dict, description="Skills matching analysis")
    experience_analysis: Dict[str, Any] = Field(default_factory=dict, description="Experience matching analysis")
    education_analysis: Dict[str, Any] = Field(default_factory=dict, description="Education matching analysis")
    keyword_analysis: Dict[str, Any] = Field(default_factory=dict, description="Keyword matching analysis")
    gap_analysis: Dict[str, Any] = Field(default_factory=dict, description="Gap analysis between resume and job")


class ImprovementSuggestion(BaseModel):
    """Individual improvement suggestion"""
    category: str = Field(..., description="Category of improvement (skills, experience, etc.)")
    priority: str = Field(..., description="Priority level (high, medium, low)")
    suggestion: str = Field(..., description="Detailed improvement suggestion")
    impact_score: Optional[int] = Field(None, ge=0, le=100, description="Expected impact of this improvement")
    examples: List[str] = Field(default_factory=list, description="Examples of how to implement this improvement")


class ResumeJobMatchResult(BaseModel):
    """Complete resume-job matching result"""
    resume_id: str
    job_id: str
    overall_match_score: float = Field(..., ge=0.0, le=1.0, description="Overall compatibility score")
    skills_match_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    experience_match_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    education_match_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    keywords_match_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    match_analysis: MatchAnalysis
    improvement_suggestions: List[ImprovementSuggestion]
    missing_skills: List[str] = Field(default_factory=list)
    matching_skills: List[str] = Field(default_factory=list)
    
    created_at: datetime
    analysis_version: Optional[str] = None


class ProcessedResumeWithAnalysis(BaseModel):
    """Enhanced processed resume with AI analysis"""
    resume_id: str
    personal_data: Dict[str, Any]
    experiences: Optional[List[Dict[str, Any]]] = None
    projects: Optional[List[Dict[str, Any]]] = None
    skills: Optional[List[Dict[str, Any]]] = None
    research_work: Optional[List[Dict[str, Any]]] = None
    achievements: Optional[List[str]] = None
    education: Optional[List[Dict[str, Any]]] = None
    extracted_keywords: Optional[List[str]] = None
    
    # AI analysis fields
    ai_analysis_scores: Optional[AIAnalysisScores] = None
    ai_feedback: Optional[AIFeedback] = None
    ats_compatibility_score: Optional[int] = Field(None, ge=0, le=100)
    keyword_density_score: Optional[int] = Field(None, ge=0, le=100)
    structure_score: Optional[int] = Field(None, ge=0, le=100)
    analysis_metadata: Optional[AnalysisMetadata] = None
    
    processed_at: datetime


class ProcessedJobWithAnalysis(BaseModel):
    """Enhanced processed job with AI analysis"""
    job_id: str
    job_title: str
    company_profile: Optional[str] = None
    location: Optional[str] = None
    date_posted: Optional[str] = None
    employment_type: Optional[str] = None
    job_summary: str
    key_responsibilities: Optional[List[str]] = None
    qualifications: Optional[Dict[str, List[str]]] = None
    compensation_and_benefits: Optional[Dict[str, Any]] = None
    application_info: Optional[Dict[str, str]] = None
    extracted_keywords: Optional[List[str]] = None
    
    # AI analysis fields
    ai_analysis_scores: Optional[Dict[str, Any]] = None
    requirements_clarity_score: Optional[int] = Field(None, ge=0, le=100)
    keyword_complexity_score: Optional[int] = Field(None, ge=0, le=100)
    match_potential_score: Optional[int] = Field(None, ge=0, le=100)
    analysis_metadata: Optional[AnalysisMetadata] = None
    
    processed_at: datetime