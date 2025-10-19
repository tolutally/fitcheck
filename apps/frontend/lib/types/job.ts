// FitScore Job Types
// Enhanced job description data structures

import { AIProcessingMetadata } from './analysis';

export interface CompanyProfile {
  name: string;
  industry?: string;
  size?: string;
  location?: string;
  description?: string;
  culture?: string[];
  benefits?: string[];
}

export interface JobRequirement {
  category: 'required' | 'preferred' | 'nice_to_have';
  requirement: string;
  importance_score?: number;
  skill_type?: 'technical' | 'soft' | 'experience' | 'education' | 'certification';
}

export interface SalaryRange {
  min?: number;
  max?: number;
  currency: string;
  period: 'hourly' | 'monthly' | 'yearly';
  negotiable?: boolean;
}

// Core job structure
export interface StructuredJob {
  job_title: string;
  company_profile: CompanyProfile;
  job_summary: string;
  key_responsibilities: string[];
  qualifications: JobRequirement[];
  preferred_qualifications?: JobRequirement[];
  benefits?: string[];
  salary_range?: SalaryRange;
  employment_type: 'full_time' | 'part_time' | 'contract' | 'internship' | 'remote';
  location?: string;
  remote_policy?: 'remote' | 'hybrid' | 'on_site';
  extracted_keywords: string[];
}

// Enhanced job with AI analysis
export interface ProcessedJob extends StructuredJob {
  job_id: string;
  resume_id?: string;
  ai_analysis?: {
    complexity_score: number;
    experience_level: 'entry' | 'mid' | 'senior' | 'executive';
    technical_depth: number;
    growth_potential: number;
    market_competitiveness: number;
  };
  analysis_metadata?: AIProcessingMetadata;
  processed_at: string;
}

// Job upload response
export interface JobUploadResponse {
  status: 'success' | 'error';
  job_id: string;
  message: string;
  data?: ProcessedJob;
  error_details?: string;
}

// Job search and filtering
export interface JobSearchFilters {
  job_title?: string;
  company?: string;
  location?: string;
  employment_type?: string[];
  salary_min?: number;
  salary_max?: number;
  remote_policy?: string[];
  experience_level?: string[];
  skills?: string[];
}

export interface JobSearchResult {
  jobs: ProcessedJob[];
  total_count: number;
  page: number;
  per_page: number;
  filters_applied: JobSearchFilters;
}