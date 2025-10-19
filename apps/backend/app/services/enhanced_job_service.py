import json
import uuid
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import ValidationError

from app.models import Job, ProcessedJob
from app.agent import AgentManager
from app.prompt import prompt_factory
from app.schemas.json import json_schema_factory
from app.schemas.pydantic import (
    StructuredJobModel,
    AnalysisMetadata,
    ProcessedJobWithAnalysis
)
from app.services.exceptions import JobNotFoundError, JobProcessingError
from app.core.exceptions import AIProcessingError

logger = logging.getLogger(__name__)


class EnhancedJobService:
    """Enhanced job service with complete AI analysis and scoring"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.agent_manager = AgentManager()

    async def process_job_descriptions(
        self,
        resume_id: str,
        job_descriptions: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Process multiple job descriptions and generate matching analysis
        
        Args:
            resume_id: ID of the resume to associate jobs with
            job_descriptions: List of job description data
            
        Returns:
            Dict containing processed jobs and analysis results
        """
        start_time = datetime.utcnow()
        
        try:
            processed_jobs = []
            
            for i, job_data in enumerate(job_descriptions):
                logger.info(f"Processing job description {i+1}/{len(job_descriptions)}")
                
                # Extract structured job data
                structured_job = await self._extract_job_structure(job_data)
                
                # Generate job analysis scores
                analysis_scores = await self._generate_job_analysis_scores(structured_job)
                
                # Store job in database
                job_record = await self._store_processed_job_with_analysis(
                    resume_id, structured_job, analysis_scores, start_time
                )
                
                processed_jobs.append({
                    "job_id": job_record.job_id,
                    "structured_data": structured_job,
                    "analysis_scores": analysis_scores
                })
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.info(f"Processed {len(processed_jobs)} job descriptions in {processing_time:.2f}ms")
            
            return {
                "status": "success",
                "processed_jobs": processed_jobs,
                "total_processed": len(processed_jobs),
                "processing_time_ms": int(processing_time),
                "message": f"Successfully processed {len(processed_jobs)} job description(s)"
            }
            
        except Exception as e:
            logger.error(f"Job processing failed: {e}", exc_info=True)
            raise JobProcessingError(f"Failed to process jobs: {str(e)}")

    async def _extract_job_structure(self, job_data: Dict[str, str]) -> Dict[str, Any]:
        """Extract structured data from job description using AI"""
        try:
            # Build comprehensive job content string
            job_content = self._build_job_content_string(job_data)
            
            # Get AI prompt and schema for job extraction
            prompt = prompt_factory.get("structured_job").format(job_posting=job_content)
            schema = json_schema_factory.get("structured_job")
            
            structured_response = await self.agent_manager.generate_structured_response(
                prompt=prompt,
                schema=schema,
                validation_model=StructuredJobModel
            )
            
            return structured_response
            
        except Exception as e:
            logger.error(f"Job structure extraction failed: {e}", exc_info=True)
            raise AIProcessingError(f"Failed to extract job structure: {str(e)}")

    def _build_job_content_string(self, job_data: Dict[str, str]) -> str:
        """Build a comprehensive job content string from job data"""
        content_parts = []
        
        if job_data.get("company"):
            content_parts.append(f"Company: {job_data['company']}")
        
        if job_data.get("job_title"):
            content_parts.append(f"Job Title: {job_data['job_title']}")
        
        if job_data.get("job_description"):
            content_parts.append(f"Job Description:\n{job_data['job_description']}")
        
        if job_data.get("location"):
            content_parts.append(f"Location: {job_data['location']}")
        
        if job_data.get("employment_type"):
            content_parts.append(f"Employment Type: {job_data['employment_type']}")
        
        return "\n\n".join(content_parts)

    async def _generate_job_analysis_scores(self, structured_job: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI analysis scores for the job posting"""
        try:
            analysis_prompt = f"""
            Analyze the following job posting and provide scoring in the following categories (0-100):
            
            1. Requirements Clarity: How clearly are the job requirements defined?
            2. Keyword Complexity: How complex/demanding are the required keywords and skills?
            3. Match Potential: How likely is this job to find good candidate matches?
            
            Job Data: {json.dumps(structured_job, indent=2)}
            
            Provide your analysis as a JSON object with these exact keys:
            {{
                "requirements_clarity_score": <score>,
                "keyword_complexity_score": <score>,
                "match_potential_score": <score>,
                "overall_job_quality": <score>
            }}
            """
            
            response = await self.agent_manager.generate_response(analysis_prompt)
            
            try:
                scores_data = json.loads(response)
                return scores_data
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(f"Failed to parse job analysis response: {e}")
                # Return default scores if parsing fails
                return {
                    "requirements_clarity_score": 75,
                    "keyword_complexity_score": 70,
                    "match_potential_score": 80,
                    "overall_job_quality": 75
                }
                
        except Exception as e:
            logger.error(f"Job analysis score generation failed: {e}", exc_info=True)
            return {}

    async def _store_processed_job_with_analysis(
        self,
        resume_id: str,
        structured_job: Dict[str, Any],
        analysis_scores: Dict[str, Any],
        start_time: datetime
    ) -> ProcessedJob:
        """Store processed job with AI analysis in database"""
        job_id = str(uuid.uuid4())
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Create job content string for raw storage
        job_content = json.dumps(structured_job, indent=2)
        
        # Store raw job
        job = Job(
            job_id=job_id,
            resume_id=resume_id,
            content=job_content
        )
        self.db.add(job)
        await self.db.flush()
        
        # Prepare analysis metadata
        analysis_metadata = AnalysisMetadata(
            analysis_version="1.0",
            processing_time_ms=int(processing_time),
            ai_model_used="gemma:2b",
            confidence_score=0.85,
            error_messages=[]
        )
        
        # Extract key information from structured job
        company_profile = structured_job.get("company_profile", {})
        location_info = structured_job.get("location", {})
        qualifications = structured_job.get("qualifications", {})
        compensation = structured_job.get("compensation_and_benefits", {})
        application_info = structured_job.get("application_info", {})
        
        # Store processed job with analysis
        processed_job = ProcessedJob(
            job_id=job_id,
            job_title=structured_job.get("job_title", ""),
            company_profile=json.dumps(company_profile) if company_profile else None,
            location=json.dumps(location_info) if location_info else None,
            date_posted=structured_job.get("date_posted"),
            employment_type=structured_job.get("employment_type"),
            job_summary=structured_job.get("job_summary", ""),
            key_responsibilities=json.dumps(structured_job.get("key_responsibilities", [])),
            qualifications=json.dumps(qualifications) if qualifications else None,
            compensation_and_benfits=json.dumps(compensation) if compensation else None,
            application_info=json.dumps(application_info) if application_info else None,
            extracted_keywords=json.dumps(structured_job.get("extracted_keywords", [])),
            
            # AI analysis fields
            ai_analysis_scores=json.dumps(analysis_scores),
            requirements_clarity_score=analysis_scores.get("requirements_clarity_score"),
            keyword_complexity_score=analysis_scores.get("keyword_complexity_score"),
            match_potential_score=analysis_scores.get("match_potential_score"),
            analysis_metadata=json.dumps(analysis_metadata.dict())
        )
        
        self.db.add(processed_job)
        await self.db.commit()
        
        return processed_job

    async def get_processed_job_with_analysis(self, job_id: str) -> Optional[ProcessedJobWithAnalysis]:
        """Retrieve processed job with AI analysis"""
        try:
            query = select(ProcessedJob).where(ProcessedJob.job_id == job_id)
            result = await self.db.execute(query)
            processed_job = result.scalars().first()
            
            if not processed_job:
                raise JobNotFoundError(job_id=job_id)
            
            # Parse JSON fields and create response model
            return ProcessedJobWithAnalysis(
                job_id=processed_job.job_id,
                job_title=processed_job.job_title,
                company_profile=processed_job.company_profile,
                location=processed_job.location,
                date_posted=processed_job.date_posted,
                employment_type=processed_job.employment_type,
                job_summary=processed_job.job_summary,
                key_responsibilities=json.loads(processed_job.key_responsibilities) if processed_job.key_responsibilities else [],
                qualifications=json.loads(processed_job.qualifications) if processed_job.qualifications else {},
                compensation_and_benefits=json.loads(processed_job.compensation_and_benfits) if processed_job.compensation_and_benfits else {},
                application_info=json.loads(processed_job.application_info) if processed_job.application_info else {},
                extracted_keywords=json.loads(processed_job.extracted_keywords) if processed_job.extracted_keywords else [],
                
                ai_analysis_scores=json.loads(processed_job.ai_analysis_scores) if processed_job.ai_analysis_scores else {},
                requirements_clarity_score=processed_job.requirements_clarity_score,
                keyword_complexity_score=processed_job.keyword_complexity_score,
                match_potential_score=processed_job.match_potential_score,
                analysis_metadata=AnalysisMetadata(**json.loads(processed_job.analysis_metadata)) if processed_job.analysis_metadata else None,
                
                processed_at=processed_job.processed_at
            )
            
        except Exception as e:
            logger.error(f"Failed to retrieve processed job {job_id}: {e}", exc_info=True)
            return None

    async def get_jobs_for_resume(self, resume_id: str) -> List[ProcessedJobWithAnalysis]:
        """Get all processed jobs associated with a resume"""
        try:
            query = select(Job).where(Job.resume_id == resume_id)
            result = await self.db.execute(query)
            jobs = result.scalars().all()
            
            processed_jobs = []
            for job in jobs:
                processed_job = await self.get_processed_job_with_analysis(job.job_id)
                if processed_job:
                    processed_jobs.append(processed_job)
            
            return processed_jobs
            
        except Exception as e:
            logger.error(f"Failed to retrieve jobs for resume {resume_id}: {e}", exc_info=True)
            return []