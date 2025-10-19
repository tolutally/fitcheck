// FitScore Job API Client
// Enhanced job processing and management functions

import {
  JobUploadResponse,
  ProcessedJob,
  JobSearchResult,
  JobSearchFilters
} from '@/lib/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

/** Upload and process multiple job descriptions */
export async function uploadJobs(
  jobDescriptions: string[],
  resumeId?: string
): Promise<JobUploadResponse[]> {
  const promises = jobDescriptions.map(description =>
    fetch(`${API_URL}/api/v1/jobs/process-enhanced`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        job_description: description,
        resume_id: resumeId
      }),
    }).then(async response => {
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Job upload failed: ${response.status} - ${errorText}`);
      }
      return response.json();
    })
  );

  return Promise.all(promises);
}

/** Search jobs with filters */
export async function searchJobs(
  filters: JobSearchFilters,
  page: number = 1,
  perPage: number = 20
): Promise<JobSearchResult> {
  const queryParams = new URLSearchParams();
  
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      if (Array.isArray(value)) {
        queryParams.append(key, value.join(','));
      } else {
        queryParams.append(key, value.toString());
      }
    }
  });
  
  queryParams.append('page', page.toString());
  queryParams.append('per_page', perPage.toString());

  const response = await fetch(`${API_URL}/api/v1/jobs/search?${queryParams.toString()}`);

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Job search failed: ${response.status} - ${errorText}`);
  }

  return response.json();
}

/** Get all jobs for a resume */
export async function getResumeJobs(resumeId: string): Promise<ProcessedJob[]> {
  const response = await fetch(`${API_URL}/api/v1/jobs?resume_id=${resumeId}`);

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to get resume jobs: ${response.status} - ${errorText}`);
  }

  const data = await response.json();
  return data.jobs || [];
}

/** Delete a job */
export async function deleteJob(jobId: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/v1/jobs/${jobId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to delete job: ${response.status} - ${errorText}`);
  }
}

/** Update job data */
export async function updateJob(
  jobId: string, 
  updates: Partial<ProcessedJob>
): Promise<ProcessedJob> {
  const response = await fetch(`${API_URL}/api/v1/jobs/${jobId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to update job: ${response.status} - ${errorText}`);
  }

  return response.json();
}