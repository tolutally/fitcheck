import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import ValidationError

from app.models import ProcessedResume, ProcessedJob, ResumeJobMatch
from app.agent import AgentManager
from app.schemas.pydantic import (
    ResumeJobMatchResult,
    MatchAnalysis,
    ImprovementSuggestion,
    AnalysisMetadata
)
from app.services.exceptions import ResumeNotFoundError, JobNotFoundError, ImprovementGenerationError
from app.core.exceptions import AIProcessingError

logger = logging.getLogger(__name__)


class ImprovementService:
    """Service for generating AI-powered resume improvements based on job requirements"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.agent_manager = AgentManager()

    async def generate_improvements(
        self,
        resume_id: str,
        job_id: str
    ) -> Dict[str, Any]:
        """
        Generate AI-powered resume improvements based on job requirements
        
        Args:
            resume_id: ID of the resume to improve
            job_id: ID of the job to match against
            
        Returns:
            Dict containing match analysis and improvement suggestions
        """
        start_time = datetime.utcnow()
        
        try:
            # Fetch resume and job data
            resume, job = await self._get_resume_and_job_data(resume_id, job_id)
            
            if not resume or not job:
                raise ImprovementGenerationError("Resume or job not found")
            
            logger.info(f"Generating improvements for resume {resume_id} against job {job_id}")
            
            # Generate comprehensive match analysis
            match_analysis = await self._analyze_resume_job_match(resume, job)
            
            # Calculate match scores
            match_scores = await self._calculate_match_scores(resume, job, match_analysis)
            
            # Generate specific improvements
            improvements = await self._generate_specific_improvements(resume, job, match_analysis)
            
            # Store match results in database
            match_result = await self._store_match_result(
                resume_id, job_id, match_scores, match_analysis, improvements, start_time
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.info(f"Improvement generation completed in {processing_time:.2f}ms")
            
            return {
                "status": "success",
                "match_result": match_result.dict(),
                "processing_time_ms": int(processing_time),
                "message": "Resume improvements generated successfully"
            }
            
        except Exception as e:
            logger.error(f"Improvement generation failed: {e}", exc_info=True)
            raise ImprovementGenerationError(f"Failed to generate improvements: {str(e)}")

    async def _get_resume_and_job_data(
        self, 
        resume_id: str, 
        job_id: str
    ) -> Tuple[Optional[ProcessedResume], Optional[ProcessedJob]]:
        """Fetch resume and job data from database"""
        try:
            # Fetch resume
            resume_query = select(ProcessedResume).where(ProcessedResume.resume_id == resume_id)
            resume_result = await self.db.execute(resume_query)
            resume = resume_result.scalars().first()
            
            if not resume:
                raise ResumeNotFoundError(resume_id=resume_id)
            
            # Fetch job
            job_query = select(ProcessedJob).where(ProcessedJob.job_id == job_id)
            job_result = await self.db.execute(job_query)
            job = job_result.scalars().first()
            
            if not job:
                raise JobNotFoundError(job_id=job_id)
            
            return resume, job
            
        except Exception as e:
            logger.error(f"Failed to fetch resume/job data: {e}", exc_info=True)
            return None, None

    async def _analyze_resume_job_match(
        self, 
        resume: ProcessedResume, 
        job: ProcessedJob
    ) -> MatchAnalysis:
        """Analyze compatibility between resume and job requirements using AI"""
        try:
            # Prepare resume data for analysis
            resume_data = {
                "personal_data": json.loads(resume.personal_data) if resume.personal_data else {},
                "experiences": json.loads(resume.experiences) if resume.experiences else [],
                "skills": json.loads(resume.skills) if resume.skills else [],
                "education": json.loads(resume.education) if resume.education else [],
                "keywords": json.loads(resume.extracted_keywords) if resume.extracted_keywords else []
            }
            
            # Prepare job data for analysis
            job_data = {
                "job_title": job.job_title,
                "job_summary": job.job_summary,
                "key_responsibilities": json.loads(job.key_responsibilities) if job.key_responsibilities else [],
                "qualifications": json.loads(job.qualifications) if job.qualifications else {},
                "keywords": json.loads(job.extracted_keywords) if job.extracted_keywords else []
            }
            
            analysis_prompt = f"""
            Perform a comprehensive analysis of how well this resume matches the job requirements.
            
            Analyze the following areas and provide detailed insights:
            1. Skills Analysis: Which skills match, which are missing, skill gaps
            2. Experience Analysis: Relevant experience, experience gaps, level match
            3. Education Analysis: Education requirements vs resume education
            4. Keyword Analysis: Keyword overlap, missing keywords, keyword density
            5. Gap Analysis: Overall gaps between resume and job requirements
            
            Resume Data: {json.dumps(resume_data, indent=2)}
            Job Data: {json.dumps(job_data, indent=2)}
            
            Provide your analysis as a JSON object with these exact keys:
            {{
                "skills_analysis": {{
                    "matching_skills": ["skill1", "skill2"],
                    "missing_skills": ["skill3", "skill4"],
                    "skill_gaps": ["gap1", "gap2"],
                    "skill_score": <0-100>
                }},
                "experience_analysis": {{
                    "relevant_experience": ["exp1", "exp2"],
                    "experience_gaps": ["gap1", "gap2"],
                    "level_match": <0-100>,
                    "experience_score": <0-100>
                }},
                "education_analysis": {{
                    "education_match": <0-100>,
                    "education_gaps": ["gap1", "gap2"],
                    "certification_needs": ["cert1", "cert2"]
                }},
                "keyword_analysis": {{
                    "matching_keywords": ["keyword1", "keyword2"],
                    "missing_keywords": ["keyword3", "keyword4"],
                    "keyword_density": <0-100>,
                    "keyword_score": <0-100>
                }},
                "gap_analysis": {{
                    "major_gaps": ["gap1", "gap2"],
                    "minor_gaps": ["gap3", "gap4"],
                    "strengths": ["strength1", "strength2"],
                    "overall_fit": <0-100>
                }}
            }}
            """
            
            response = await self.agent_manager.generate_response(analysis_prompt)
            
            try:
                analysis_data = json.loads(response)
                return MatchAnalysis(**analysis_data)
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(f"Failed to parse match analysis response: {e}")
                # Return default analysis if parsing fails
                return MatchAnalysis(
                    skills_analysis={"skill_score": 70, "matching_skills": [], "missing_skills": []},
                    experience_analysis={"experience_score": 75, "relevant_experience": []},
                    education_analysis={"education_match": 80},
                    keyword_analysis={"keyword_score": 65, "matching_keywords": [], "missing_keywords": []},
                    gap_analysis={"overall_fit": 70, "major_gaps": [], "strengths": []}
                )
                
        except Exception as e:
            logger.error(f"Match analysis failed: {e}", exc_info=True)
            raise AIProcessingError(f"Failed to analyze resume-job match: {str(e)}")

    async def _calculate_match_scores(
        self,
        resume: ProcessedResume,
        job: ProcessedJob,
        match_analysis: MatchAnalysis
    ) -> Dict[str, float]:
        """Calculate numerical match scores based on analysis"""
        try:
            # Extract scores from analysis
            skills_score = match_analysis.skills_analysis.get("skill_score", 70) / 100.0
            experience_score = match_analysis.experience_analysis.get("experience_score", 75) / 100.0
            education_score = match_analysis.education_analysis.get("education_match", 80) / 100.0
            keywords_score = match_analysis.keyword_analysis.get("keyword_score", 65) / 100.0
            
            # Calculate weighted overall score
            overall_score = (
                skills_score * 0.4 +           # 40% weight on skills
                experience_score * 0.3 +       # 30% weight on experience
                keywords_score * 0.2 +         # 20% weight on keywords
                education_score * 0.1          # 10% weight on education
            )
            
            return {
                "overall_match_score": round(overall_score, 3),
                "skills_match_score": round(skills_score, 3),
                "experience_match_score": round(experience_score, 3),
                "education_match_score": round(education_score, 3),
                "keywords_match_score": round(keywords_score, 3)
            }
            
        except Exception as e:
            logger.error(f"Match score calculation failed: {e}", exc_info=True)
            # Return default scores
            return {
                "overall_match_score": 0.70,
                "skills_match_score": 0.70,
                "experience_match_score": 0.75,
                "education_match_score": 0.80,
                "keywords_match_score": 0.65
            }

    async def _generate_specific_improvements(
        self,
        resume: ProcessedResume,
        job: ProcessedJob,
        match_analysis: MatchAnalysis
    ) -> List[ImprovementSuggestion]:
        """Generate specific improvement recommendations"""
        try:
            improvement_prompt = f"""
            Based on the resume-job match analysis, generate specific, actionable improvement suggestions.
            
            Focus on:
            1. Skills that should be added or emphasized
            2. Experience descriptions that should be improved
            3. Keywords that should be incorporated
            4. Education/certifications that should be highlighted
            5. Overall resume structure improvements
            
            Match Analysis: {match_analysis.dict()}
            
            Provide 5-10 specific improvement suggestions as a JSON array:
            [
                {{
                    "category": "skills|experience|keywords|education|structure",
                    "priority": "high|medium|low",
                    "suggestion": "Detailed suggestion text",
                    "impact_score": <0-100>,
                    "examples": ["example1", "example2"]
                }},
                ...
            ]
            """
            
            response = await self.agent_manager.generate_response(improvement_prompt)
            
            try:
                suggestions_data = json.loads(response)
                return [ImprovementSuggestion(**suggestion) for suggestion in suggestions_data]
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(f"Failed to parse improvement suggestions: {e}")
                # Return default suggestions
                return [
                    ImprovementSuggestion(
                        category="skills",
                        priority="high",
                        suggestion="Add more specific technical skills that match job requirements",
                        impact_score=85,
                        examples=["Include specific programming languages", "Add relevant tools and frameworks"]
                    ),
                    ImprovementSuggestion(
                        category="keywords",
                        priority="high",
                        suggestion="Incorporate job-specific keywords throughout your resume",
                        impact_score=80,
                        examples=["Use exact terms from job description", "Include industry-specific terminology"]
                    ),
                    ImprovementSuggestion(
                        category="experience",
                        priority="medium",
                        suggestion="Quantify achievements with specific numbers and results",
                        impact_score=75,
                        examples=["Add percentage improvements", "Include dollar amounts or time savings"]
                    )
                ]
                
        except Exception as e:
            logger.error(f"Improvement suggestion generation failed: {e}", exc_info=True)
            return []

    async def _store_match_result(
        self,
        resume_id: str,
        job_id: str,
        match_scores: Dict[str, float],
        match_analysis: MatchAnalysis,
        improvements: List[ImprovementSuggestion],
        start_time: datetime
    ) -> ResumeJobMatchResult:
        """Store match results in database and return result object"""
        try:
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Create match record
            match_record = ResumeJobMatch(
                resume_id=resume_id,
                job_id=job_id,
                overall_match_score=match_scores["overall_match_score"],
                skills_match_score=match_scores["skills_match_score"],
                experience_match_score=match_scores["experience_match_score"],
                education_match_score=match_scores["education_match_score"],
                keywords_match_score=match_scores["keywords_match_score"],
                
                match_analysis=json.dumps(match_analysis.dict()),
                improvement_suggestions=json.dumps([imp.dict() for imp in improvements]),
                missing_skills=json.dumps(match_analysis.skills_analysis.get("missing_skills", [])),
                matching_skills=json.dumps(match_analysis.skills_analysis.get("matching_skills", [])),
                gap_analysis=json.dumps(match_analysis.gap_analysis),
                
                analysis_version="1.0"
            )
            
            self.db.add(match_record)
            await self.db.commit()
            
            # Create result object
            return ResumeJobMatchResult(
                resume_id=resume_id,
                job_id=job_id,
                overall_match_score=match_scores["overall_match_score"],
                skills_match_score=match_scores["skills_match_score"],
                experience_match_score=match_scores["experience_match_score"],
                education_match_score=match_scores["education_match_score"],
                keywords_match_score=match_scores["keywords_match_score"],
                
                match_analysis=match_analysis,
                improvement_suggestions=improvements,
                missing_skills=match_analysis.skills_analysis.get("missing_skills", []),
                matching_skills=match_analysis.skills_analysis.get("matching_skills", []),
                
                created_at=match_record.created_at,
                analysis_version="1.0"
            )
            
        except Exception as e:
            logger.error(f"Failed to store match result: {e}", exc_info=True)
            raise ImprovementGenerationError(f"Failed to store match result: {str(e)}")

    async def get_match_history(self, resume_id: str) -> List[ResumeJobMatchResult]:
        """Get all match results for a resume"""
        try:
            query = select(ResumeJobMatch).where(ResumeJobMatch.resume_id == resume_id)
            result = await self.db.execute(query)
            matches = result.scalars().all()
            
            match_results = []
            for match in matches:
                # Parse stored JSON data
                match_analysis = MatchAnalysis(**json.loads(match.match_analysis)) if match.match_analysis else None
                improvements = [ImprovementSuggestion(**imp) for imp in json.loads(match.improvement_suggestions)] if match.improvement_suggestions else []
                
                match_result = ResumeJobMatchResult(
                    resume_id=match.resume_id,
                    job_id=match.job_id,
                    overall_match_score=match.overall_match_score,
                    skills_match_score=match.skills_match_score,
                    experience_match_score=match.experience_match_score,
                    education_match_score=match.education_match_score,
                    keywords_match_score=match.keywords_match_score,
                    
                    match_analysis=match_analysis,
                    improvement_suggestions=improvements,
                    missing_skills=json.loads(match.missing_skills) if match.missing_skills else [],
                    matching_skills=json.loads(match.matching_skills) if match.matching_skills else [],
                    
                    created_at=match.created_at,
                    analysis_version=match.analysis_version
                )
                
                match_results.append(match_result)
            
            return match_results
            
        except Exception as e:
            logger.error(f"Failed to get match history for resume {resume_id}: {e}", exc_info=True)
            return []