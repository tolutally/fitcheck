'use client';

import React, { useState, useEffect } from 'react';
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
import { getProcessedResume } from '@/lib/api/resume';
import type { ProcessedResume } from '@/lib/types/resume';
import type { AIAnalysisScores, AIFeedback, ImprovementSuggestion } from '@/lib/types/analysis';

// Legacy interface for backward compatibility
interface LegacyImprovementSuggestion {
	suggestion: string;
	lineNumber?: string | number;
}

export interface ResumeAnalysisProps {
	// Enhanced props - can accept resume_id for dynamic loading
	resume_id?: string;
	resumeData?: ProcessedResume;
	
	// Legacy props for backward compatibility
	score?: number;
	details?: string;
	commentary?: string;
	improvements?: LegacyImprovementSuggestion[];
}

const ResumeAnalysis: React.FC<ResumeAnalysisProps> = ({
	resume_id,
	resumeData,
	// Legacy props
	score,
	details,
	commentary,
	improvements,
}) => {
	const [isModalOpen, setIsModalOpen] = useState(false);
	const [resumeAnalysis, setResumeAnalysis] = useState<ProcessedResume | null>(resumeData || null);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);

	// Load resume data if resume_id provided but no resumeData
	useEffect(() => {
		if (resume_id && !resumeData) {
			setLoading(true);
			getProcessedResume(resume_id)
				.then(setResumeAnalysis)
				.catch(err => {
					console.error('Failed to load resume:', err);
					setError('Failed to load resume analysis');
				})
				.finally(() => setLoading(false));
		}
	}, [resume_id, resumeData]);

	const getScoreColor = (value: number) => {
		if (value >= 80) return 'text-green-500';
		if (value >= 60) return 'text-yellow-500';
		return 'text-red-500';
	};

	const getScoreText = (value: number) => {
		if (value >= 90) return 'Excellent';
		if (value >= 80) return 'Very Good';
		if (value >= 70) return 'Good';
		if (value >= 60) return 'Fair';
		return 'Needs Improvement';
	};

	// Enhanced data or fallback to legacy
	const analysisData = resumeAnalysis as ProcessedResume | null;
	const aiScores = analysisData?.ai_analysis_scores;
	const aiFeedback = analysisData?.ai_feedback;
	const overallScore = aiScores?.overall_score || score || 0;
	const atsScore = analysisData?.ats_compatibility_score || 0;

	// Create enhancement suggestions from AI feedback or legacy improvements
	const enhancedSuggestions: ImprovementSuggestion[] = aiFeedback?.improvements?.map(improvement => ({
		category: 'content',
		priority: 'medium',
		suggestion: improvement,
		impact_score: 70
	})) || improvements?.map(item => ({
		category: 'content' as const,
		priority: 'medium' as const,
		suggestion: item.suggestion,
		impact_score: 60
	})) || [];

	// Prepare display text
	const analysisDetails = aiFeedback?.strengths?.join(' ') || details || 'Analysis in progress...';
	const analysisCommentary = aiFeedback?.critical_issues?.join(' ') || commentary || '';
	const truncatedDetails = analysisDetails.length > 100 ? analysisDetails.slice(0, 97) + '...' : analysisDetails;
	const truncatedCommentary = analysisCommentary.length > 100 ? analysisCommentary.slice(0, 97) + '...' : analysisCommentary;

	if (loading) {
		return (
			<div className="bg-gray-900/80 p-6 rounded-lg shadow-xl text-gray-100">
				<div className="animate-pulse">
					<div className="h-6 bg-gray-700 rounded mb-4"></div>
					<div className="h-4 bg-gray-700 rounded mb-2"></div>
					<div className="h-4 bg-gray-700 rounded w-3/4"></div>
				</div>
			</div>
		);
	}

	if (error) {
		return (
			<div className="bg-gray-900/80 p-6 rounded-lg shadow-xl text-gray-100">
				<div className="text-red-400">
					<h3 className="text-xl font-semibold mb-2">Analysis Error</h3>
					<p className="text-sm">{error}</p>
				</div>
			</div>
		);
	}

	return (
		<div className="bg-gray-900/80 p-6 rounded-lg shadow-xl text-gray-100">
			<Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
				<DialogTrigger asChild>
					<div className="cursor-pointer">
						<div className="flex justify-between items-center mb-4">
							<h3 className="text-xl font-semibold text-gray-100">🎯 FitScore Analysis</h3>
							<div className="text-right">
								<div className={`text-3xl font-bold ${getScoreColor(overallScore)}`}>
									{overallScore}
									<span className="text-sm">/100</span>
								</div>
								<div className="text-xs text-gray-400">{getScoreText(overallScore)}</div>
							</div>
						</div>
						
						{/* Enhanced Metrics Row */}
						<div className="grid grid-cols-3 gap-2 mb-3">
							<div className="text-center">
								<div className={`text-lg font-bold ${getScoreColor(atsScore)}`}>{atsScore}%</div>
								<div className="text-xs text-gray-400">ATS Score</div>
							</div>
							<div className="text-center">
								<div className={`text-lg font-bold ${getScoreColor(aiScores?.keyword_optimization || 0)}`}>
									{aiScores?.keyword_optimization || 0}%
								</div>
								<div className="text-xs text-gray-400">Keywords</div>
							</div>
							<div className="text-center">
								<div className={`text-lg font-bold ${getScoreColor(aiScores?.structure_quality || 0)}`}>
									{aiScores?.structure_quality || 0}%
								</div>
								<div className="text-xs text-gray-400">Structure</div>
							</div>
						</div>

						<p className="text-sm text-gray-400 mb-2">{truncatedDetails}</p>
						{truncatedCommentary && (
							<p className="text-sm text-red-400">{truncatedCommentary}</p>
						)}
						<Button variant="link" className="text-blue-400 hover:text-blue-300 p-0 h-auto mt-2 text-sm">
							View Detailed Analysis
						</Button>
					</div>
				</DialogTrigger>

				<DialogContent className="bg-gray-900 border-gray-700 text-gray-100 sm:max-w-[600px] md:max-w-[800px] lg:max-w-[1000px] p-0">
					<DialogHeader className="p-6 border-b border-gray-700">
						<DialogTitle className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">
							🎯 FitScore AI Analysis Report
						</DialogTitle>
						{analysisData?.personal_data?.full_name && (
							<p className="text-gray-400 mt-2">Analysis for {analysisData.personal_data.full_name}</p>
						)}
					</DialogHeader>

					<div className="p-6 max-h-[70vh] overflow-y-auto">
						{/* Enhanced Score Cards */}
						<div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
							<div className="bg-gray-800 p-4 rounded-lg text-center">
								<h4 className="text-sm font-semibold text-blue-400 mb-2">Overall Score</h4>
								<div className={`text-4xl font-bold ${getScoreColor(overallScore)}`}>{overallScore}</div>
								<div className="text-xs text-gray-400 mt-1">{getScoreText(overallScore)}</div>
								<div className="w-full bg-gray-700 rounded-full h-2 mt-2">
									<div 
										className={`h-2 rounded-full transition-all duration-300 ${overallScore >= 80 ? 'bg-green-500' : overallScore >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`}
										style={{ width: `${Math.min(100, Math.max(0, overallScore))}%` }}
									/>
								</div>
							</div>

							<div className="bg-gray-800 p-4 rounded-lg text-center">
								<h4 className="text-sm font-semibold text-green-400 mb-2">ATS Compatible</h4>
								<div className={`text-4xl font-bold ${getScoreColor(atsScore)}`}>{atsScore}%</div>
								<div className="text-xs text-gray-400 mt-1">Pass Rate</div>
							</div>

							<div className="bg-gray-800 p-4 rounded-lg text-center">
								<h4 className="text-sm font-semibold text-purple-400 mb-2">Keywords</h4>
								<div className={`text-4xl font-bold ${getScoreColor(aiScores?.keyword_optimization || 0)}`}>
									{aiScores?.keyword_optimization || 0}%
								</div>
								<div className="text-xs text-gray-400 mt-1">Optimized</div>
							</div>

							<div className="bg-gray-800 p-4 rounded-lg text-center">
								<h4 className="text-sm font-semibold text-orange-400 mb-2">Structure</h4>
								<div className={`text-4xl font-bold ${getScoreColor(aiScores?.structure_quality || 0)}`}>
									{aiScores?.structure_quality || 0}%
								</div>
								<div className="text-xs text-gray-400 mt-1">Quality</div>
							</div>
						</div>

						{/* Detailed Analysis Sections */}
						<div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
							{/* Strengths */}
							{aiFeedback?.strengths && aiFeedback.strengths.length > 0 && (
								<div className="bg-gray-800 p-4 rounded-lg">
									<h4 className="text-lg font-semibold text-green-400 mb-3">✅ Strengths</h4>
									<ul className="space-y-2">
										{aiFeedback.strengths.map((strength, idx) => (
											<li key={idx} className="text-gray-300 text-sm flex items-start">
												<span className="text-green-400 mr-2">•</span>
												{strength}
											</li>
										))}
									</ul>
								</div>
							)}

							{/* Critical Issues */}
							{aiFeedback?.critical_issues && aiFeedback.critical_issues.length > 0 && (
								<div className="bg-gray-800 p-4 rounded-lg">
									<h4 className="text-lg font-semibold text-red-400 mb-3">🚨 Critical Issues</h4>
									<ul className="space-y-2">
										{aiFeedback.critical_issues.map((issue, idx) => (
											<li key={idx} className="text-gray-300 text-sm flex items-start">
												<span className="text-red-400 mr-2">•</span>
												{issue}
											</li>
										))}
									</ul>
								</div>
							)}
						</div>

						{/* AI-Powered Improvement Suggestions */}
						<div>
							<h4 className="text-xl font-semibold text-blue-400 mb-3">🎯 AI Improvement Suggestions</h4>
							{enhancedSuggestions.length > 0 ? (
								<div className="space-y-3">
									{enhancedSuggestions.map((suggestion, idx) => (
										<div key={idx} className="bg-gray-800 p-4 rounded-md border-l-4 border-blue-500">
											<div className="flex justify-between items-start mb-2">
												<span className={`text-xs px-2 py-1 rounded ${
													suggestion.priority === 'critical' ? 'bg-red-500 text-white' :
													suggestion.priority === 'high' ? 'bg-orange-500 text-white' :
													suggestion.priority === 'medium' ? 'bg-yellow-500 text-black' :
													'bg-green-500 text-white'
												}`}>
													{suggestion.priority.toUpperCase()}
												</span>
												<span className="text-xs text-gray-400">Impact: {suggestion.impact_score}%</span>
											</div>
											<p className="text-gray-200 text-sm">{suggestion.suggestion}</p>
											<div className="text-xs text-gray-500 mt-2">
												Category: {suggestion.category.charAt(0).toUpperCase() + suggestion.category.slice(1)}
											</div>
										</div>
									))}
								</div>
							) : (
								<div className="bg-gray-800 p-4 rounded-lg text-center">
									<p className="text-gray-400 text-sm">🎉 Great job! No critical improvements needed at this time.</p>
								</div>
							)}
						</div>

						{/* Keyword Suggestions */}
						{aiFeedback?.keyword_suggestions && aiFeedback.keyword_suggestions.length > 0 && (
							<div className="mt-6">
								<h4 className="text-lg font-semibold text-purple-400 mb-3">🔍 Keyword Suggestions</h4>
								<div className="bg-gray-800 p-4 rounded-lg">
									<div className="flex flex-wrap gap-2">
										{aiFeedback.keyword_suggestions.map((keyword, idx) => (
											<span key={idx} className="bg-purple-600 text-white px-3 py-1 rounded-full text-sm">
												{keyword}
											</span>
										))}
									</div>
								</div>
							</div>
						)}
					</div>

					<DialogFooter className="p-6 border-t border-gray-700">
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

export default ResumeAnalysis;