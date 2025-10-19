'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import ResumeAnalysis from './resume-analysis';
import JobMatchCard from './job-match-card';
import { getDashboardData, getBulkAnalysis, analyzeResumeJobMatch } from '@/lib/api/resume';
import { getResumeJobs } from '@/lib/api/job';
import type { DashboardData, BulkAnalysisResult } from '@/lib/types/dashboard';
import type { ProcessedJob } from '@/lib/types/job';
import type { ResumeJobMatchResult } from '@/lib/types/analysis';

export interface FitScoreDashboardProps {
  resumeId: string;
  className?: string;
}

const FitScoreDashboard: React.FC<FitScoreDashboardProps> = ({
  resumeId,
  className = '',
}) => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [bulkAnalysis, setBulkAnalysis] = useState<BulkAnalysisResult | null>(null);
  const [recentJobs, setRecentJobs] = useState<ProcessedJob[]>([]);
  const [jobMatches, setJobMatches] = useState<{ [jobId: string]: ResumeJobMatchResult }>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'matches' | 'analytics'>('overview');

  // Load dashboard data
  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true);
        const [dashboard, jobs, bulk] = await Promise.all([
          getDashboardData(resumeId).catch(() => null),
          getResumeJobs(resumeId).catch(() => []),
          getBulkAnalysis(resumeId).catch(() => null),
        ]);

        setDashboardData(dashboard);
        setRecentJobs(jobs.slice(0, 6)); // Show recent 6 jobs
        setBulkAnalysis(bulk);

        // Load match analysis for recent jobs
        if (jobs.length > 0) {
          const matchPromises = jobs.slice(0, 6).map(async (job: ProcessedJob) => {
            try {
              const match = await analyzeResumeJobMatch({
                resume_id: resumeId,
                job_id: job.job_id,
                include_recommendations: true,
                include_ai_insights: true,
              });
              return { jobId: job.job_id, match };
            } catch (error) {
              console.error(`Failed to analyze match for job ${job.job_id}:`, error);
              return null;
            }
          });

          const matchResults = await Promise.all(matchPromises);
          const matchMap: { [jobId: string]: ResumeJobMatchResult } = {};
          matchResults.forEach((result: { jobId: string; match: ResumeJobMatchResult } | null) => {
            if (result) {
              matchMap[result.jobId] = result.match;
            }
          });
          setJobMatches(matchMap);
        }
      } catch (err) {
        console.error('Failed to load dashboard:', err);
        setError('Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, [resumeId]);

  const handleApplyToJob = (jobId: string) => {
    // Handle apply to job logic
    console.log('Applying to job:', jobId);
    // This would typically open an external link or redirect
  };

  const handleSaveJob = (jobId: string) => {
    // Handle save job logic
    console.log('Saving job:', jobId);
    // This would typically save to user's saved jobs list
  };

  if (loading) {
    return (
      <div className={`space-y-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-8 bg-gray-700 rounded mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="h-64 bg-gray-700 rounded"></div>
            <div className="h-64 bg-gray-700 rounded"></div>
            <div className="h-64 bg-gray-700 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-red-900/20 border border-red-500 rounded-lg p-6 ${className}`}>
        <h3 className="text-red-400 font-semibold mb-2">Dashboard Error</h3>
        <p className="text-gray-300">{error}</p>
        <Button 
          onClick={() => window.location.reload()} 
          className="mt-4 bg-red-600 hover:bg-red-700"
        >
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">
            🎯 FitScore Dashboard
          </h1>
          {dashboardData?.overview?.resume_summary?.name && (
            <p className="text-gray-400 mt-1">Welcome back, {dashboardData.overview.resume_summary.name}!</p>
          )}
        </div>

        {/* Tab Navigation */}
        <div className="flex bg-gray-800 rounded-lg p-1">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
              activeTab === 'overview' 
                ? 'bg-blue-600 text-white' 
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('matches')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
              activeTab === 'matches' 
                ? 'bg-blue-600 text-white' 
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            Job Matches
          </button>
          <button
            onClick={() => setActiveTab('analytics')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
              activeTab === 'analytics' 
                ? 'bg-blue-600 text-white' 
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            Analytics
          </button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Performance Metrics */}
          {dashboardData?.overview?.performance_metrics && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="bg-gray-900/80 p-6 rounded-lg shadow-xl">
                <h3 className="text-lg font-semibold text-blue-400 mb-2">Total Applications</h3>
                <div className="text-3xl font-bold text-gray-100">
                  {dashboardData.overview.performance_metrics.total_applications}
                </div>
                <p className="text-gray-400 text-sm mt-1">Job applications tracked</p>
              </div>

              <div className="bg-gray-900/80 p-6 rounded-lg shadow-xl">
                <h3 className="text-lg font-semibold text-green-400 mb-2">Avg Match Score</h3>
                <div className="text-3xl font-bold text-gray-100">
                  {Math.round(dashboardData.overview.performance_metrics.average_match_score)}%
                </div>
                <p className="text-gray-400 text-sm mt-1">
                  <span className={`${
                    dashboardData.overview.performance_metrics.improvement_trend === 'improving' ? 'text-green-400' :
                    dashboardData.overview.performance_metrics.improvement_trend === 'declining' ? 'text-red-400' :
                    'text-yellow-400'
                  }`}>
                    {dashboardData.overview.performance_metrics.improvement_trend === 'improving' ? '📈' :
                     dashboardData.overview.performance_metrics.improvement_trend === 'declining' ? '📉' : '➡️'} 
                    {dashboardData.overview.performance_metrics.improvement_trend}
                  </span>
                </p>
              </div>

              <div className="bg-gray-900/80 p-6 rounded-lg shadow-xl">
                <h3 className="text-lg font-semibold text-purple-400 mb-2">Best Match</h3>
                <div className="text-3xl font-bold text-gray-100">
                  {Math.round(dashboardData.overview.performance_metrics.best_match_score)}%
                </div>
                <p className="text-gray-400 text-sm mt-1">Highest compatibility</p>
              </div>

              <div className="bg-gray-900/80 p-6 rounded-lg shadow-xl">
                <h3 className="text-lg font-semibold text-orange-400 mb-2">ATS Score</h3>
                <div className="text-3xl font-bold text-gray-100">
                  {Math.round(dashboardData.overview.performance_metrics.ats_compatibility_average)}%
                </div>
                <p className="text-gray-400 text-sm mt-1">Average compatibility</p>
              </div>
            </div>
          )}

          {/* Resume Analysis */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <ResumeAnalysis 
                resume_id={resumeId}
                resumeData={dashboardData?.resume}
              />
            </div>
            
            {/* Recent Activity */}
            <div className="bg-gray-900/80 p-6 rounded-lg shadow-xl">
              <h3 className="text-xl font-semibold text-gray-100 mb-4">📊 Recent Activity</h3>
              {dashboardData?.overview?.recent_activity && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400 text-sm">This Week</span>
                    <span className="text-blue-400 font-semibold">
                      {dashboardData.overview.recent_activity.matches_this_week} matches
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400 text-sm">Jobs Analyzed</span>
                    <span className="text-green-400 font-semibold">
                      {dashboardData.overview.recent_activity.jobs_analyzed}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400 text-sm">Improvements</span>
                    <span className="text-purple-400 font-semibold">
                      {dashboardData.overview.recent_activity.improvements_generated}
                    </span>
                  </div>
                  <div className="pt-2 border-t border-gray-700">
                    <span className="text-gray-400 text-xs">
                      Last Analysis: {new Date(dashboardData.overview.recent_activity.last_analysis).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'matches' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold text-gray-100">🎯 Job Matches</h2>
            <p className="text-gray-400">
              {recentJobs.length} recent job{recentJobs.length !== 1 ? 's' : ''} analyzed
            </p>
          </div>

          {recentJobs.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {recentJobs.map((job) => {
                const matchResult = jobMatches[job.job_id];
                if (!matchResult) return null;

                return (
                  <JobMatchCard
                    key={job.job_id}
                    matchResult={matchResult}
                    jobData={job}
                    onApplyToJob={handleApplyToJob}
                    onSaveJob={handleSaveJob}
                  />
                );
              })}
            </div>
          ) : (
            <div className="bg-gray-900/80 p-12 rounded-lg text-center">
              <div className="text-6xl mb-4">📋</div>
              <h3 className="text-xl font-semibold text-gray-300 mb-2">No Job Matches Yet</h3>
              <p className="text-gray-400 mb-6">Upload some job descriptions to see AI-powered match analysis</p>
              <Button className="bg-blue-600 hover:bg-blue-700">
                Upload Job Descriptions
              </Button>
            </div>
          )}
        </div>
      )}

      {activeTab === 'analytics' && (
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-gray-100">📈 Advanced Analytics</h2>
          
          {bulkAnalysis ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* Analysis Summary */}
              <div className="bg-gray-900/80 p-6 rounded-lg shadow-xl">
                <h3 className="text-lg font-semibold text-blue-400 mb-2">Jobs Analyzed</h3>
                <div className="text-3xl font-bold text-gray-100">
                  {bulkAnalysis.analysis_summary.total_jobs_analyzed}
                </div>
                <p className="text-gray-400 text-sm mt-1">
                  {new Date(bulkAnalysis.analysis_summary.analysis_date).toLocaleDateString()}
                </p>
              </div>

              {/* Match Distribution */}
              <div className="bg-gray-900/80 p-6 rounded-lg shadow-xl">
                <h3 className="text-lg font-semibold text-green-400 mb-2">Excellent Matches</h3>
                <div className="text-3xl font-bold text-gray-100">
                  {bulkAnalysis.analysis_summary.jobs_by_match_score.excellent}
                </div>
                <p className="text-gray-400 text-sm mt-1">90-100% match</p>
              </div>

              <div className="bg-gray-900/80 p-6 rounded-lg shadow-xl">
                <h3 className="text-lg font-semibold text-yellow-400 mb-2">Good Matches</h3>
                <div className="text-3xl font-bold text-gray-100">
                  {bulkAnalysis.analysis_summary.jobs_by_match_score.good}
                </div>
                <p className="text-gray-400 text-sm mt-1">75-89% match</p>
              </div>

              <div className="bg-gray-900/80 p-6 rounded-lg shadow-xl">
                <h3 className="text-lg font-semibold text-orange-400 mb-2">Fair Matches</h3>
                <div className="text-3xl font-bold text-gray-100">
                  {bulkAnalysis.analysis_summary.jobs_by_match_score.fair}
                </div>
                <p className="text-gray-400 text-sm mt-1">60-74% match</p>
              </div>
            </div>
          ) : (
            <div className="bg-gray-900/80 p-12 rounded-lg text-center">
              <div className="text-6xl mb-4">📊</div>
              <h3 className="text-xl font-semibold text-gray-300 mb-2">No Analytics Data</h3>
              <p className="text-gray-400">Analyze some jobs to see detailed analytics</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default FitScoreDashboard;