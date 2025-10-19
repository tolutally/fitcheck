// FitScore AI Analysis Types
// Matching backend schemas/pydantic/analysis.py

export interface AIAnalysisScores {
  overall_score: number;
  ats_compatibility: number;
  keyword_optimization: number;
  structure_quality: number;
  content_relevance: number;
  experience_alignment: number;
  skills_match: number;
  education_relevance: number;
}

export interface AIFeedback {
  strengths: string[];
  improvements: string[];
  critical_issues: string[];
  keyword_suggestions: string[];
  formatting_recommendations: string[];
}

export interface MatchAnalysis {
  skills_match: number;
  experience_match: number;
  education_match: number;
  keyword_coverage: number;
  missing_keywords: string[];
  matched_keywords: string[];
  improvement_priority: 'low' | 'medium' | 'high' | 'critical';
}

export interface ImprovementSuggestion {
  category: 'skills' | 'experience' | 'education' | 'formatting' | 'keywords' | 'content';
  priority: 'low' | 'medium' | 'high' | 'critical';
  suggestion: string;
  impact_score: number;
  specific_changes?: string[];
}

export interface ResumeJobMatchResult {
  match_score: number;
  detailed_analysis: MatchAnalysis;
  recommendations: ImprovementSuggestion[];
  ai_insights: string;
  confidence_score: number;
}

export interface ProcessingStatus {
  status: 'processing' | 'completed' | 'failed';
  progress?: number;
  message?: string;
  error_details?: string;
}

export interface AIProcessingMetadata {
  processing_time: number;
  model_used: string;
  confidence_score: number;
  analysis_version: string;
  processing_date: string;
}