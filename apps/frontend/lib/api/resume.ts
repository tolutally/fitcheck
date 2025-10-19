import { ImprovedResult } from '@/components/common/resume_previewer_context';
import {
  ResumeUploadResponse,
  ProcessedResume,
  JobUploadResponse,
  ProcessedJob,
  ResumeJobMatchResult,
  MatchHistory,
  DashboardData,
  BulkAnalysisResult,
  ComparisonAnalysis,
  MatchAnalysisRequest,
  BulkMatchRequest
} from '@/lib/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

/** Uploads job descriptions and returns a job_id */
export async function uploadJobDescriptions(
    descriptions: string[],
    resumeId: string
): Promise<string> {
    const res = await fetch(`${API_URL}/api/v1/jobs/upload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_descriptions: descriptions, resume_id: resumeId }),
    });
    if (!res.ok) throw new Error(`Upload failed with status ${res.status}`);
    const data = await res.json();
    console.log('Job upload response:', data);
    return data.job_id[0];
}

/** Improves the resume and returns the full preview object */
export async function improveResume(
    resumeId: string,
    jobId: string
): Promise<ImprovedResult> {
    let response: Response;
    try {
        response = await fetch(`${API_URL}/api/v1/resumes/improve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ resume_id: resumeId, job_id: jobId }),
        });
    } catch (networkError) {
        console.error('Network error during improveResume:', networkError);
        throw networkError;
    }

    const text = await response.text();
    if (!response.ok) {
        console.error('Improve failed response body:', text);
        throw new Error(`Improve failed with status ${response.status}: ${text}`);
    }

    let data: ImprovedResult;
    try {
        data = JSON.parse(text) as ImprovedResult;
    } catch (parseError) {
        console.error('Failed to parse improveResume response:', parseError, 'Raw response:', text);
        throw parseError;
    }

    console.log('Resume improvement response:', data);
    return data;
}

// ============================================================================
// ENHANCED FITSCORE API FUNCTIONS
// ============================================================================

/** Enhanced resume processing with AI analysis */
export async function processResumeEnhanced(
    file: File,
    options?: { include_ai_analysis?: boolean }
): Promise<ResumeUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    
    if (options?.include_ai_analysis !== undefined) {
        formData.append('include_ai_analysis', options.include_ai_analysis.toString());
    }

    const response = await fetch(`${API_URL}/api/v1/resumes/process-enhanced`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Enhanced resume processing failed: ${response.status} - ${errorText}`);
    }

    return response.json();
}

/** Enhanced job description processing */
export async function processJobEnhanced(
    jobDescription: string,
    resumeId?: string
): Promise<JobUploadResponse> {
    const response = await fetch(`${API_URL}/api/v1/jobs/process-enhanced`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            job_description: jobDescription,
            resume_id: resumeId
        }),
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Enhanced job processing failed: ${response.status} - ${errorText}`);
    }

    return response.json();
}

/** Analyze resume-job match with AI insights */
export async function analyzeResumeJobMatch(
    request: MatchAnalysisRequest
): Promise<ResumeJobMatchResult> {
    const response = await fetch(`${API_URL}/api/v1/resumes/analyze-match`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Match analysis failed: ${response.status} - ${errorText}`);
    }

    return response.json();
}

/** Get match history for a resume */
export async function getResumeMatches(resumeId: string): Promise<MatchHistory> {
    const response = await fetch(`${API_URL}/api/v1/resumes/${resumeId}/matches`);

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to get match history: ${response.status} - ${errorText}`);
    }

    return response.json();
}

/** Get comprehensive dashboard data */
export async function getDashboardData(resumeId: string): Promise<DashboardData> {
    const response = await fetch(`${API_URL}/api/v1/analysis/dashboard/${resumeId}`);

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to get dashboard data: ${response.status} - ${errorText}`);
    }

    return response.json();
}

/** Perform bulk analysis of resume against multiple jobs */
export async function getBulkAnalysis(
    resumeId: string,
    request?: BulkMatchRequest
): Promise<BulkAnalysisResult> {
    const queryParams = new URLSearchParams();
    if (request?.job_ids) {
        queryParams.append('job_ids', request.job_ids.join(','));
    }
    if (request?.max_jobs) {
        queryParams.append('max_jobs', request.max_jobs.toString());
    }
    if (request?.min_match_score) {
        queryParams.append('min_match_score', request.min_match_score.toString());
    }

    const response = await fetch(
        `${API_URL}/api/v1/analysis/bulk-analysis/${resumeId}?${queryParams.toString()}`
    );

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Bulk analysis failed: ${response.status} - ${errorText}`);
    }

    return response.json();
}

/** Get comparison analysis */
export async function getComparisonAnalysis(
    resumeId: string,
    comparisonType: 'temporal' | 'peer' | 'industry' = 'temporal'
): Promise<ComparisonAnalysis> {
    const response = await fetch(
        `${API_URL}/api/v1/analysis/comparison?resume_id=${resumeId}&comparison_type=${comparisonType}`
    );

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Comparison analysis failed: ${response.status} - ${errorText}`);
    }

    return response.json();
}

/** Get processed resume data */
export async function getProcessedResume(resumeId: string): Promise<ProcessedResume> {
    const response = await fetch(`${API_URL}/api/v1/resumes/${resumeId}`);

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to get resume data: ${response.status} - ${errorText}`);
    }

    return response.json();
}

/** Get processed job data */
export async function getProcessedJob(jobId: string): Promise<ProcessedJob> {
    const response = await fetch(`${API_URL}/api/v1/jobs/${jobId}`);

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to get job data: ${response.status} - ${errorText}`);
    }

    return response.json();
}