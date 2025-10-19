// FitScore Resume Types
// Enhanced resume data structures with AI analysis

import { AIAnalysisScores, AIFeedback, AIProcessingMetadata } from './analysis';

export interface PersonalData {
  full_name: string;
  email: string;
  phone?: string;
  location?: string;
  linkedin?: string;
  github?: string;
  website?: string;
  summary?: string;
}

export interface Experience {
  job_title: string;
  company: string;
  location?: string;
  start_date: string;
  end_date: string | 'Present';
  responsibilities: string[];
  achievements?: string[];
  technologies?: string[];
}

export interface Education {
  degree: string;
  institution: string;
  location?: string;
  graduation_date: string;
  gpa?: string;
  relevant_coursework?: string[];
  honors?: string[];
}

export interface Project {
  name: string;
  description: string;
  technologies: string[];
  start_date?: string;
  end_date?: string;
  url?: string;
  github_url?: string;
  achievements?: string[];
}

export interface Skill {
  name: string;
  category: 'technical' | 'soft' | 'language' | 'certification' | 'other';
  proficiency?: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  years_experience?: number;
}

export interface Certification {
  name: string;
  issuer: string;
  issue_date: string;
  expiry_date?: string;
  credential_id?: string;
  url?: string;
}

// Core resume structure
export interface StructuredResume {
  personal_data: PersonalData;
  experiences: Experience[];
  education: Education[];
  skills: Skill[];
  projects?: Project[];
  certifications?: Certification[];
  extracted_keywords: string[];
}

// Enhanced resume with AI analysis
export interface ProcessedResume extends StructuredResume {
  resume_id: string;
  ai_analysis_scores?: AIAnalysisScores;
  ai_feedback?: AIFeedback;
  ats_compatibility_score?: number;
  analysis_metadata?: AIProcessingMetadata;
  processed_at: string;
  content_type: string;
  file_size?: number;
}

// Resume upload response
export interface ResumeUploadResponse {
  status: 'success' | 'error';
  resume_id: string;
  message: string;
  data?: ProcessedResume;
  error_details?: string;
}

// Resume processing options
export interface ResumeProcessingOptions {
  include_ai_analysis: boolean;
  generate_improvements: boolean;
  extract_keywords: boolean;
  analyze_ats_compatibility: boolean;
}