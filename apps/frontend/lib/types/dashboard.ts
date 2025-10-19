// FitScore Dashboard Types
// Analytics and dashboard data structures

import { ProcessedResume } from './resume';
import { ProcessedJob } from './job';
import { ResumeJobMatch, MatchHistory } from './matching';
import { AIAnalysisScores } from './analysis';

// Dashboard overview
export interface DashboardOverview {
  resume_id: string;
  resume_summary: {
    name: string;
    job_title?: string;
    total_experience_years: number;
    key_skills: string[];
    last_updated: string;
  };
  performance_metrics: {
    total_applications: number; 
    average_match_score: number;
    best_match_score: number;
    improvement_trend: 'improving' | 'stable' | 'declining';
    ats_compatibility_average: number;
  };
  recent_activity: {
    matches_this_week: number;
    jobs_analyzed: number;
    improvements_generated: number;
    last_analysis: string;
  };
}

// Performance analytics
export interface PerformanceAnalytics {
  resume_id: string;
  time_series: {
    date: string;
    match_scores: number[];
    average_score: number;
    jobs_analyzed: number;
    ats_score: number;
  }[];
  skill_analysis: {
    skill: string;
    demand_score: number;
    your_proficiency: number;
    market_trend: 'rising' | 'stable' | 'declining';
    job_mentions: number;
  }[];
  improvement_tracking: {
    category: string;
    suggestions_count: number;
    implemented_count: number;
    impact_score: number;
  }[];
}

// Market insights
export interface MarketInsights {
  industry_trends: {
    industry: string;
    growth_rate: number;
    salary_trend: 'increasing' | 'stable' | 'decreasing';
    top_skills: string[];
    job_availability: number;
  }[];
  salary_benchmarks: {
    role: string;
    experience_level: string;
    salary_range: {
      min: number;
      max: number;
      median: number;
      currency: string;
    };
    location_factor: number;
  }[];
  skill_demand: {
    skill: string;
    demand_index: number;
    growth_rate: number;
    avg_salary_boost: number;
  }[];
}

// Comprehensive dashboard data
export interface DashboardData {
  overview: DashboardOverview;
  resume: ProcessedResume;
  match_history: MatchHistory;
  performance_analytics: PerformanceAnalytics;
  market_insights: MarketInsights;
  recommendations: {
    priority_improvements: string[];
    skill_development: string[];
    career_opportunities: string[];
    next_steps: string[];
  };
}

// Bulk analysis results
export interface BulkAnalysisResult {
  resume_id: string;
  analysis_summary: {
    total_jobs_analyzed: number;
    analysis_date: string;
    processing_time: number;
    jobs_by_match_score: {
      excellent: number; // 90-100%
      good: number; // 75-89%
      fair: number; // 60-74%
      poor: number; // <60%
    };
  };
  top_opportunities: ResumeJobMatch[];
  skill_gaps: {
    skill: string;
    importance: number;
    frequency_in_jobs: number;
    current_proficiency: number;
    learning_resources?: string[];
  }[];
  industry_breakdown: {
    industry: string;
    job_count: number;
    average_match_score: number;
    salary_range: {
      min: number;
      max: number;
      currency: string;
    };
  }[];
  geographical_analysis: {
    location: string;
    job_count: number;
    average_match_score: number;
    remote_opportunities: number;
  }[];
}

// Comparison analysis
export interface ComparisonAnalysis {
  base_resume_id: string;
  comparison_type: 'temporal' | 'peer' | 'industry';
  comparison_data: {
    label: string;
    match_scores: number[];
    ats_scores: number[];
    skill_counts: number[];
    experience_years: number[];
  }[];
  insights: string[];
  recommendations: string[];
}