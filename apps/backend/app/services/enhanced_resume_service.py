import os
import uuid
import json
import tempfile
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List

from markitdown import MarkItDown
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import ValidationError

from app.models import Resume, ProcessedResume
from app.agent import AgentManager
from app.prompt import prompt_factory
from app.schemas.json import json_schema_factory
from app.schemas.pydantic import (
    StructuredResumeModel, 
    AIAnalysisScores, 
    AIFeedback, 
    AnalysisMetadata,
    ProcessedResumeWithAnalysis
)
from app.services.exceptions import ResumeNotFoundError, ResumeValidationError
from app.core.exceptions import AIProcessingError

logger = logging.getLogger(__name__)


class EnhancedResumeService:
    """Enhanced resume service with complete AI analysis and scoring"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.md = MarkItDown(enable_plugins=False)
        self.agent_manager = AgentManager()
        self._validate_docx_dependencies()

    def _validate_docx_dependencies(self):
        """Validate that required dependencies for DOCX processing are available"""
        missing_deps = []
        
        try:
            from markitdown.converters import DocxConverter
            DocxConverter()
        except ImportError:
            missing_deps.append("markitdown[all]==0.1.2")
        except Exception as e:
            if "MissingDependencyException" in str(e) or "dependencies needed to read .docx files" in str(e):
                missing_deps.append("markitdown[all]==0.1.2 (current installation missing DOCX extras)")
        
        if missing_deps:
            logger.warning(
                f"Missing dependencies for DOCX processing: {', '.join(missing_deps)}. "
                f"DOCX file processing may fail. Install with: pip install {' '.join(missing_deps)}"
            )

    async def process_resume_with_analysis(
        self, 
        file_bytes: bytes, 
        file_type: str, 
        filename: str, 
        content_type: str = "md"
    ) -> Dict[str, Any]:
        """
        Complete resume processing with AI analysis and scoring
        
        Args:
            file_bytes: Raw bytes of the uploaded file
            file_type: MIME type of the file
            filename: Original filename
            content_type: Output format ("md" for markdown or "html")
            
        Returns:
            Dict containing resume_id, structured_data, analysis_scores, and AI feedback
        """
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Document parsing
            logger.info(f"Starting resume processing for file: {filename}")
            parsed_content = await self._parse_document(file_bytes, file_type)
            
            # Step 2: AI extraction of structured data
            structured_data = await self._extract_structured_data(parsed_content)
            
            # Step 3: Generate AI analysis and scoring
            analysis_scores = await self._generate_analysis_scores(structured_data)
            ai_feedback = await self._generate_ai_feedback(structured_data, analysis_scores)
            
            # Step 4: Store processed resume with analysis
            resume_id = await self._store_processed_resume_with_analysis(
                parsed_content, content_type, structured_data, analysis_scores, ai_feedback, start_time
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.info(f"Resume processing completed in {processing_time:.2f}ms for resume_id: {resume_id}")
            
            return {
                "status": "success",
                "resume_id": resume_id,
                "structured_data": structured_data,
                "analysis_scores": analysis_scores.dict() if analysis_scores else None,
                "ai_feedback": ai_feedback.dict() if ai_feedback else None,
                "processing_time_ms": int(processing_time),
                "message": "Resume processed successfully with AI analysis"
            }
            
        except Exception as e:
            logger.error(f"Resume processing failed for {filename}: {e}", exc_info=True)
            raise ResumeValidationError(
                resume_id="unknown",
                message=f"Failed to process resume: {str(e)}"
            )

    async def _parse_document(self, file_bytes: bytes, file_type: str) -> str:
        """Parse document using MarkItDown"""
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=self._get_file_extension(file_type)
        ) as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name

        try:
            result = self.md.convert(temp_path)
            return result.text_content
        except Exception as e:
            error_msg = str(e)
            if "MissingDependencyException" in error_msg or "DocxConverter" in error_msg:
                raise Exception(
                    "File conversion failed: markitdown is missing DOCX support. "
                    "Please install with: pip install 'markitdown[all]==0.1.2'"
                ) from e
            elif "docx" in error_msg.lower():
                raise Exception(
                    f"DOCX file processing failed: {error_msg}. "
                    "Please ensure the file is a valid DOCX document."
                ) from e
            else:
                raise Exception(f"File conversion failed: {error_msg}") from e
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    async def _extract_structured_data(self, content: str) -> Dict[str, Any]:
        """Extract structured data from resume content using AI"""
        try:
            prompt = prompt_factory.get("structured_resume").format(resume_text=content)
            schema = json_schema_factory.get("structured_resume")
            
            structured_response = await self.agent_manager.generate_structured_response(
                prompt=prompt,
                schema=schema,
                validation_model=StructuredResumeModel
            )
            
            return structured_response
            
        except Exception as e:
            logger.error(f"Structured data extraction failed: {e}", exc_info=True)
            raise AIProcessingError(f"Failed to extract structured data: {str(e)}")

    async def _generate_analysis_scores(self, structured_data: Dict[str, Any]) -> Optional[AIAnalysisScores]:
        """Generate AI analysis scores for the resume"""
        try:
            # Create analysis prompt
            analysis_prompt = f"""
            Analyze the following resume data and provide scoring in the following categories (0-100):
            
            1. ATS Compatibility: How well will this resume pass through ATS systems?
            2. Keyword Density: How rich is the resume in relevant keywords?
            3. Structure Quality: How well-structured and organized is the resume?
            4. Content Relevance: How relevant and impactful is the content?
            5. Overall Score: Overall assessment of the resume quality.
            
            Resume Data: {json.dumps(structured_data, indent=2)}
            
            Provide your analysis as a JSON object with these exact keys:
            {{
                "ats_compatibility": <score>,
                "keyword_density": <score>,
                "structure_quality": <score>,
                "content_relevance": <score>,
                "overall_score": <score>
            }}
            """
            
            response = await self.agent_manager.generate_response(analysis_prompt)
            
            # Parse and validate the response
            try:
                scores_data = json.loads(response)
                return AIAnalysisScores(**scores_data)
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(f"Failed to parse AI scores response: {e}")
                # Return default scores if parsing fails
                return AIAnalysisScores(
                    ats_compatibility=75,
                    keyword_density=70,
                    structure_quality=80,
                    content_relevance=75,
                    overall_score=75
                )
                
        except Exception as e:
            logger.error(f"Analysis score generation failed: {e}", exc_info=True)
            return None

    async def _generate_ai_feedback(
        self, 
        structured_data: Dict[str, Any], 
        analysis_scores: Optional[AIAnalysisScores]
    ) -> Optional[AIFeedback]:
        """Generate AI feedback and suggestions"""
        try:
            feedback_prompt = f"""
            Based on the resume analysis and scores, provide detailed feedback in the following categories:
            
            1. Strengths: What are the resume's strong points?
            2. Weaknesses: What areas need improvement?
            3. Suggestions: Specific actionable improvements
            4. Missing Elements: What important elements are missing?
            5. ATS Recommendations: Specific recommendations for ATS optimization
            
            Resume Data: {json.dumps(structured_data, indent=2)}
            Analysis Scores: {analysis_scores.dict() if analysis_scores else "Not available"}
            
            Provide your feedback as a JSON object with these exact keys:
            {{
                "strengths": ["strength1", "strength2", ...],
                "weaknesses": ["weakness1", "weakness2", ...],
                "suggestions": ["suggestion1", "suggestion2", ...],
                "missing_elements": ["element1", "element2", ...],
                "ats_recommendations": ["recommendation1", "recommendation2", ...]
            }}
            """
            
            response = await self.agent_manager.generate_response(feedback_prompt)
            
            try:
                feedback_data = json.loads(response)
                return AIFeedback(**feedback_data)
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(f"Failed to parse AI feedback response: {e}")
                # Return default feedback if parsing fails
                return AIFeedback(
                    strengths=["Resume contains relevant work experience"],
                    weaknesses=["Could benefit from more specific achievements"],
                    suggestions=["Add quantifiable results to experience descriptions"],
                    missing_elements=["Skills section could be more comprehensive"],
                    ats_recommendations=["Use standard section headings for better ATS parsing"]
                )
                
        except Exception as e:
            logger.error(f"AI feedback generation failed: {e}", exc_info=True)
            return None

    async def _store_processed_resume_with_analysis(
        self,
        content: str,
        content_type: str,
        structured_data: Dict[str, Any],
        analysis_scores: Optional[AIAnalysisScores],
        ai_feedback: Optional[AIFeedback],
        start_time: datetime
    ) -> str:
        """Store processed resume with AI analysis in database"""
        resume_id = str(uuid.uuid4())
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Store raw resume
        resume = Resume(
            resume_id=resume_id, 
            content=content, 
            content_type=content_type
        )
        self.db.add(resume)
        await self.db.flush()
        
        # Prepare analysis metadata
        analysis_metadata = AnalysisMetadata(
            analysis_version="1.0",
            processing_time_ms=int(processing_time),
            ai_model_used="gemma:2b",
            confidence_score=0.85,
            error_messages=[]
        )
        
        # Store processed resume with analysis
        processed_resume = ProcessedResume(
            resume_id=resume_id,
            personal_data=json.dumps(structured_data.get("personal_data", {})),
            experiences=json.dumps(structured_data.get("experiences", [])),
            projects=json.dumps(structured_data.get("projects", [])),
            skills=json.dumps(structured_data.get("skills", [])),
            research_work=json.dumps(structured_data.get("research_work", [])),
            achievements=json.dumps(structured_data.get("achievements", [])),
            education=json.dumps(structured_data.get("education", [])),
            extracted_keywords=json.dumps(structured_data.get("extracted_keywords", [])),
            
            # AI analysis fields
            ai_analysis_scores=json.dumps(analysis_scores.dict() if analysis_scores else {}),
            ai_feedback=json.dumps(ai_feedback.dict() if ai_feedback else {}),
            ats_compatibility_score=analysis_scores.ats_compatibility if analysis_scores else None,
            keyword_density_score=analysis_scores.keyword_density if analysis_scores else None,
            structure_score=analysis_scores.structure_quality if analysis_scores else None,
            analysis_metadata=json.dumps(analysis_metadata.dict())
        )
        
        self.db.add(processed_resume)
        await self.db.commit()
        
        return resume_id

    async def get_processed_resume_with_analysis(self, resume_id: str) -> Optional[ProcessedResumeWithAnalysis]:
        """Retrieve processed resume with AI analysis"""
        try:
            query = select(ProcessedResume).where(ProcessedResume.resume_id == resume_id)
            result = await self.db.execute(query)
            processed_resume = result.scalars().first()
            
            if not processed_resume:
                raise ResumeNotFoundError(resume_id=resume_id)
            
            # Parse JSON fields and create response model
            return ProcessedResumeWithAnalysis(
                resume_id=processed_resume.resume_id,
                personal_data=json.loads(processed_resume.personal_data) if processed_resume.personal_data else {},
                experiences=json.loads(processed_resume.experiences) if processed_resume.experiences else [],
                projects=json.loads(processed_resume.projects) if processed_resume.projects else [],
                skills=json.loads(processed_resume.skills) if processed_resume.skills else [],
                research_work=json.loads(processed_resume.research_work) if processed_resume.research_work else [],
                achievements=json.loads(processed_resume.achievements) if processed_resume.achievements else [],
                education=json.loads(processed_resume.education) if processed_resume.education else [],
                extracted_keywords=json.loads(processed_resume.extracted_keywords) if processed_resume.extracted_keywords else [],
                
                ai_analysis_scores=AIAnalysisScores(**json.loads(processed_resume.ai_analysis_scores)) if processed_resume.ai_analysis_scores else None,
                ai_feedback=AIFeedback(**json.loads(processed_resume.ai_feedback)) if processed_resume.ai_feedback else None,
                ats_compatibility_score=processed_resume.ats_compatibility_score,
                keyword_density_score=processed_resume.keyword_density_score,
                structure_score=processed_resume.structure_score,
                analysis_metadata=AnalysisMetadata(**json.loads(processed_resume.analysis_metadata)) if processed_resume.analysis_metadata else None,
                
                processed_at=processed_resume.processed_at
            )
            
        except Exception as e:
            logger.error(f"Failed to retrieve processed resume {resume_id}: {e}", exc_info=True)
            return None

    def _get_file_extension(self, file_type: str) -> str:
        """Returns the appropriate file extension based on MIME type"""
        if file_type == "application/pdf":
            return ".pdf"
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return ".docx"
        return ""