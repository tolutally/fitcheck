'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
  DialogClose,
} from '@/components/ui/dialog';
import type { ResumeJobMatchWithContext } from '@/lib/types/matching';
import type { ProcessedJob } from '@/lib/types/job';
import type { ImprovementSuggestion, ResumeJobMatchResult } from '@/lib/types/analysis';

export interface JobMatchCardProps {
  matchResult: ResumeJobMatchResult;
  jobData: ProcessedJob;
  onApplyToJob?: (jobId: string) => void;
  onSaveJob?: (jobId: string) => void;
  className?: string;
}

const JobMatchCard: React.FC<JobMatchCardProps> = ({
  matchResult,
  jobData,
  onApplyToJob,
  onSaveJob,
  className = '',
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const getMatchColor = (score: number) => {
    if (score >= 80) return 'text-green-500';
    if (score >= 60) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getMatchBadgeColor = (score: number) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getMatchText = (score: number) => {
    if (score >= 90) return 'Excellent Match';
    if (score >= 80) return 'Very Good Match';
    if (score >= 70) return 'Good Match';
    if (score >= 60) return 'Fair Match';
    return 'Needs Improvement';
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'critical': return '🚨';
      case 'high': return '⚠️';
      case 'medium': return '📋';
      default: return '💡';
    }
  };

  const prioritySuggestions = matchResult.recommendations?.filter((r: ImprovementSuggestion) => 
    r.priority === 'critical' || r.priority === 'high'
  ) || [];

  const salaryRange = jobData.salary_range;
  const salaryText = salaryRange 
    ? `$${salaryRange.min?.toLocaleString() || '?'} - $${salaryRange.max?.toLocaleString() || '?'} ${salaryRange.period}`
    : 'Salary not specified';

  return (
    <div className={`bg-gray-900/80 rounded-lg shadow-xl border border-gray-700 hover:border-blue-500 transition-all duration-300 ${className}`}>
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogTrigger asChild>
          <div className="p-6 cursor-pointer">
            {/* Header */}
            <div className="flex justify-between items-start mb-4">
              <div className="flex-1">
                <h3 className="text-xl font-semibold text-gray-100 mb-1">{jobData.job_title}</h3>
                <p className="text-gray-400 text-sm">{jobData.company_profile.name}</p>
                <p className="text-gray-500 text-xs">{jobData.location || 'Location not specified'} • {jobData.employment_type.replace('_', ' ')}</p>
              </div>
              <div className="text-right ml-4">
                <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getMatchBadgeColor(matchResult.match_score)} text-white mb-2`}>
                  {matchResult.match_score}% Match
                </div>
                <div className="text-xs text-gray-400">{getMatchText(matchResult.match_score)}</div>
              </div>
            </div>

            {/* Quick Metrics */}
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="text-center">
                <div className={`text-lg font-bold ${getMatchColor(matchResult.detailed_analysis.skills_match)}`}>
                  {matchResult.detailed_analysis.skills_match}%
                </div>
                <div className="text-xs text-gray-400">Skills</div>
              </div>
              <div className="text-center">
                <div className={`text-lg font-bold ${getMatchColor(matchResult.detailed_analysis.experience_match)}`}>
                  {matchResult.detailed_analysis.experience_match}%
                </div>
                <div className="text-xs text-gray-400">Experience</div>
              </div>
              <div className="text-center">
                <div className={`text-lg font-bold ${getMatchColor(matchResult.detailed_analysis.keyword_coverage)}`}>
                  {matchResult.detailed_analysis.keyword_coverage}%
                </div>
                <div className="text-xs text-gray-400">Keywords</div>
              </div>
            </div>

            {/* Salary & Priority Issues */}
            <div className="flex justify-between items-center mb-4">
              <div className="text-sm text-gray-400">
                💰 {salaryText}
              </div>
              {prioritySuggestions.length > 0 && (
                <div className="text-sm text-orange-400">
                  ⚠️ {prioritySuggestions.length} Priority Issues
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                size="sm"
                className="flex-1 text-blue-400 border-blue-400 hover:bg-blue-400 hover:text-white"
                onClick={(e) => {
                  e.stopPropagation();
                  setIsModalOpen(true);
                }}
              >
                View Details
              </Button>
              {onSaveJob && (
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    onSaveJob(jobData.job_id);
                  }}
                  className="text-gray-400 border-gray-400 hover:bg-gray-400 hover:text-gray-900"
                >
                  Save
                </Button>
              )}
              {onApplyToJob && (
                <Button 
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    onApplyToJob(jobData.job_id);
                  }}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  Apply
                </Button>
              )}
            </div>
          </div>
        </DialogTrigger>

        {/* Detailed Modal */}
        <DialogContent className="bg-gray-900 border-gray-700 text-gray-100 sm:max-w-[800px] lg:max-w-[1000px] p-0 max-h-[90vh]">
          <DialogHeader className="p-6 border-b border-gray-700">
            <DialogTitle className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-green-400">
              🎯 Job Match Analysis: {jobData.job_title}
            </DialogTitle>
            <p className="text-gray-400 mt-2">{jobData.company_profile.name}</p>
          </DialogHeader>

          <div className="p-6 max-h-[70vh] overflow-y-auto">
            {/* Match Score Overview */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-gray-800 p-4 rounded-lg text-center">
                <h4 className="text-sm font-semibold text-blue-400 mb-2">Overall Match</h4>
                <div className={`text-4xl font-bold ${getMatchColor(matchResult.match_score)}`}>
                  {matchResult.match_score}%
                </div>
                <div className="text-xs text-gray-400 mt-1">{getMatchText(matchResult.match_score)}</div>
              </div>

              <div className="bg-gray-800 p-4 rounded-lg text-center">
                <h4 className="text-sm font-semibold text-green-400 mb-2">Skills Match</h4>
                <div className={`text-4xl font-bold ${getMatchColor(matchResult.detailed_analysis.skills_match)}`}>
                  {matchResult.detailed_analysis.skills_match}%
                </div>
                <div className="text-xs text-gray-400 mt-1">Technical Fit</div>
              </div>

              <div className="bg-gray-800 p-4 rounded-lg text-center">
                <h4 className="text-sm font-semibold text-purple-400 mb-2">Experience</h4>
                <div className={`text-4xl font-bold ${getMatchColor(matchResult.detailed_analysis.experience_match)}`}>
                  {matchResult.detailed_analysis.experience_match}%
                </div>
                <div className="text-xs text-gray-400 mt-1">Level Match</div>
              </div>

              <div className="bg-gray-800 p-4 rounded-lg text-center">
                <h4 className="text-sm font-semibold text-orange-400 mb-2">Keywords</h4>
                <div className={`text-4xl font-bold ${getMatchColor(matchResult.detailed_analysis.keyword_coverage)}`}>
                  {matchResult.detailed_analysis.keyword_coverage}%
                </div>
                <div className="text-xs text-gray-400 mt-1">Coverage</div>
              </div>
            </div>

            {/* Job Details */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div className="bg-gray-800 p-4 rounded-lg">
                <h4 className="text-lg font-semibold text-blue-400 mb-3">📋 Job Details</h4>
                <div className="space-y-2 text-sm">
                  <p><span className="text-gray-400">Position:</span> <span className="text-gray-200">{jobData.job_title}</span></p>
                  <p><span className="text-gray-400">Company:</span> <span className="text-gray-200">{jobData.company_profile.name}</span></p>
                  <p><span className="text-gray-400">Location:</span> <span className="text-gray-200">{jobData.location || 'Remote/Not specified'}</span></p>
                  <p><span className="text-gray-400">Type:</span> <span className="text-gray-200">{jobData.employment_type.replace('_', ' ')}</span></p>
                  <p><span className="text-gray-400">Salary:</span> <span className="text-gray-200">{salaryText}</span></p>
                </div>
              </div>

              <div className="bg-gray-800 p-4 rounded-lg">
                <h4 className="text-lg font-semibold text-green-400 mb-3">✅ Matched Keywords</h4>
                <div className="flex flex-wrap gap-2">
                  {matchResult.detailed_analysis.matched_keywords?.slice(0, 10).map((keyword: string, idx: number) => (
                    <span key={idx} className="bg-green-600 text-white px-2 py-1 rounded text-xs">
                      {keyword}
                    </span>
                  )) || <span className="text-gray-400 text-sm">No matched keywords available</span>}
                </div>
              </div>
            </div>

            {/* Missing Keywords */}
            {matchResult.detailed_analysis.missing_keywords && matchResult.detailed_analysis.missing_keywords.length > 0 && (
              <div className="bg-gray-800 p-4 rounded-lg mb-6">
                <h4 className="text-lg font-semibold text-red-400 mb-3">🔍 Missing Keywords</h4>
                <div className="flex flex-wrap gap-2">
                  {matchResult.detailed_analysis.missing_keywords.slice(0, 15).map((keyword: string, idx: number) => (
                    <span key={idx} className="bg-red-600 text-white px-2 py-1 rounded text-xs">
                      {keyword}
                    </span>
                  ))}
                </div>
                <p className="text-gray-400 text-sm mt-3">
                  Consider adding these keywords to your resume to improve your match score.
                </p>
              </div>
            )}

            {/* AI Improvement Recommendations */}
            {matchResult.recommendations && matchResult.recommendations.length > 0 && (
              <div className="mb-6">
                <h4 className="text-xl font-semibold text-purple-400 mb-3">🎯 AI Recommendations</h4>
                <div className="space-y-3">
                  {matchResult.recommendations.slice(0, 8).map((recommendation: ImprovementSuggestion, idx: number) => (
                    <div key={idx} className="bg-gray-800 p-4 rounded-md border-l-4 border-purple-500">
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex items-center gap-2">
                          <span>{getPriorityIcon(recommendation.priority)}</span>
                          <span className={`text-xs px-2 py-1 rounded ${
                            recommendation.priority === 'critical' ? 'bg-red-500 text-white' :
                            recommendation.priority === 'high' ? 'bg-orange-500 text-white' :
                            recommendation.priority === 'medium' ? 'bg-yellow-500 text-black' :
                            'bg-green-500 text-white'
                          }`}>
                            {recommendation.priority.toUpperCase()}
                          </span>
                        </div>
                        <span className="text-xs text-gray-400">Impact: {recommendation.impact_score}%</span>
                      </div>
                      <p className="text-gray-200 text-sm">{recommendation.suggestion}</p>
                      <div className="text-xs text-gray-500 mt-2">
                        Category: {recommendation.category.charAt(0).toUpperCase() + recommendation.category.slice(1)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* AI Insights */}
            {matchResult.ai_insights && (
              <div className="bg-blue-900/30 p-4 rounded-lg border border-blue-600">
                <h4 className="text-lg font-semibold text-blue-400 mb-3">🤖 AI Insights</h4>
                <p className="text-gray-300 text-sm leading-relaxed">{matchResult.ai_insights}</p>
                {matchResult.confidence_score && (
                  <div className="mt-3 text-xs text-gray-400">
                    Confidence Score: {matchResult.confidence_score}%
                  </div>
                )}
              </div>
            )}
          </div>

          <DialogFooter className="p-6 border-t border-gray-700 flex gap-2">
            {onSaveJob && (
              <Button 
                variant="outline" 
                onClick={() => onSaveJob(jobData.job_id)}
                className="text-gray-400 border-gray-400 hover:bg-gray-400 hover:text-gray-900"
              >
                Save Job
              </Button>
            )}
            {onApplyToJob && (
              <Button 
                onClick={() => onApplyToJob(jobData.job_id)}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                Apply Now
              </Button>
            )}
            <DialogClose asChild>
              <Button variant="outline" className="text-gray-100 bg-gray-700 hover:bg-gray-600 border-gray-600">
                Close
              </Button>
            </DialogClose>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default JobMatchCard;