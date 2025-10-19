// FitScore Matching Types
// Resume-job matching and analysis results

import { MatchAnalysis, ImprovementSuggestion, ResumeJobMatchResult } from './analysis';
import { ProcessedResume } from './resume';
import { ProcessedJob } from './job';

// Resume-Job match tracking
export interface ResumeJobMatch {
  match_id: string;
  resume_id: string;
  job_id: string;
  match_score: number;
  detailed_analysis: MatchAnalysis;
  created_at: string;
  updated_at: string;
  status: 'active' | 'archived' | 'applied';
}

// Match with full context
export interface ResumeJobMatchWithContext extends ResumeJobMatch {
  resume: ProcessedResume;
  job: ProcessedJob;
  recommendations: ImprovementSuggestion[];
  ai_insights: string;
  confidence_score: number;
}

// Match history for a resume
export interface MatchHistory {
  resume_id: string;
  matches: ResumeJobMatchWithContext[];
  total_matches: number;
  average_match_score: number;
  best_match: ResumeJobMatchWithContext | null;
  improvement_trends: {
    date: string;
    average_score: number;
    match_count: number;
  }[];
}

// Bulk matching results
export interface BulkMatchResult {
  resume_id: string;
  job_matches: ResumeJobMatchWithContext[];
  summary: {
    total_jobs_analyzed: number;
    average_match_score: number;
    high_matches: number; // matches > 80%
    medium_matches: number; // matches 60-80%
    low_matches: number; // matches < 60%
  };
  recommendations: {
    top_skills_to_develop: string[];
    career_progression_suggestions: string[];
    industry_insights: string[];
  };
}

// Match request payloads
export interface MatchAnalysisRequest {
  resume_id: string;
  job_id: string;
  include_recommendations?: boolean;
  include_ai_insights?: boolean;
}

export interface BulkMatchRequest {
  resume_id: string;
  job_ids?: string[];
  max_jobs?: number;
  min_match_score?: number;
  include_detailed_analysis?: boolean;
}

// Match comparison
export interface MatchComparison {
  resume_id: string;
  comparisons: {
    job_a: ProcessedJob;
    job_b: ProcessedJob;
    match_a: ResumeJobMatchResult;
    match_b: ResumeJobMatchResult;
    comparison_insights: string[];
    recommendation: 'job_a' | 'job_b' | 'both' | 'neither';
  }[];
  overall_recommendation: string;
}