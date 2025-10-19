import logging
import traceback

from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi import (
    APIRouter,
    File,
    UploadFile,
    HTTPException,
    Depends,
    Request,
    status,
    Query,
)

from app.core import get_db_session
from app.services import (
    ResumeService,
    ScoreImprovementService,
    EnhancedResumeService,
    ImprovementService,
    ResumeNotFoundError,
    ResumeParsingError,
    ResumeValidationError,
    JobNotFoundError,
    JobParsingError,
    ResumeKeywordExtractionError,
    JobKeywordExtractionError,
    ImprovementGenerationError,
)
from app.schemas.pydantic import ResumeImprovementRequest

resume_router = APIRouter()
logger = logging.getLogger(__name__)


@resume_router.post(
    "/upload",
    summary="Upload a resume in PDF or DOCX format and store it into DB in HTML/Markdown format",
)
async def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Accepts a PDF or DOCX file (max 2MB), converts it to HTML/Markdown, and stores it in the database.

    Raises:
        HTTPException: If the file type is not supported, file is empty, or file exceeds 2MB limit.
    """
    request_id = getattr(request.state, "request_id", str(uuid4()))

    allowed_content_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]

    if file.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF and DOCX files are allowed.",
        )

    MAX_FILE_SIZE = 2 * 1024 * 1024
    
    # Try to get size from file object or Content-Length header
    file_size = getattr(file, 'size', None)
    if file_size is None and hasattr(request, 'headers'):
        content_length = request.headers.get('content-length')
        if content_length:
            try:
                file_size = int(content_length)
            except ValueError:
                pass  # Invalid content-length header
    
    if file_size and file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds maximum allowed size of 2.0MB.",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file. Please upload a valid file.",
        )

    # Verify size after reading
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds maximum allowed size of 2.0MB.",
        )

    try:
        resume_service = ResumeService(db)
        resume_id = await resume_service.convert_and_store_resume(
            file_bytes=file_bytes,
            file_type=file.content_type,
            filename=file.filename,
            content_type="md",
        )
    except ResumeValidationError as e:
        logger.warning(f"Resume validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            f"Error processing file: {str(e)} - traceback: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}",
        )

    return {
        "message": f"File {file.filename} successfully processed as MD and stored in the DB",
        "request_id": request_id,
        "resume_id": resume_id,
    }


@resume_router.post(
    "/improve",
    summary="Score and improve a resume against a job description",
)
async def score_and_improve(
    request: Request,
    payload: ResumeImprovementRequest,
    db: AsyncSession = Depends(get_db_session),
    stream: bool = Query(
        False, description="Enable streaming response using Server-Sent Events"
    ),
):
    """
    Scores and improves a resume against a job description.

    Raises:
        HTTPException: If the resume or job is not found.
    """
    request_id = getattr(request.state, "request_id", str(uuid4()))
    headers = {"X-Request-ID": request_id}

    request_payload = payload.model_dump()

    try:
        resume_id = str(request_payload.get("resume_id", ""))
        if not resume_id:
            raise ResumeNotFoundError(
                message="invalid value passed in `resume_id` field, please try again with valid resume_id."
            )
        job_id = str(request_payload.get("job_id", ""))
        if not job_id:
            raise JobNotFoundError(
                message="invalid value passed in `job_id` field, please try again with valid job_id."
            )
        score_improvement_service = ScoreImprovementService(db=db)

        if stream:
            return StreamingResponse(
                content=score_improvement_service.run_and_stream(
                    resume_id=resume_id,
                    job_id=job_id,
                ),
                media_type="text/event-stream",
                headers=headers,
            )
        else:
            improvements = await score_improvement_service.run(
                resume_id=resume_id,
                job_id=job_id,
            )
            return JSONResponse(
                content={
                    "request_id": request_id,
                    "data": improvements,
                },
                headers=headers,
            )
    except ResumeNotFoundError as e:
        logger.error(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except JobNotFoundError as e:
        logger.error(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except ResumeParsingError as e:
        logger.error(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except JobParsingError as e:
        logger.error(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except ResumeKeywordExtractionError as e:
        logger.warning(str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except JobKeywordExtractionError as e:
        logger.warning(str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error: {str(e)} - traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="sorry, something went wrong!",
        )


@resume_router.get(
    "",
    summary="Get resume data from both resume and processed_resume models",
)
async def get_resume(
    request: Request,
    resume_id: str = Query(..., description="Resume ID to fetch data for"),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Retrieves resume data from both resume_model and processed_resume model by resume_id.

    Args:
        resume_id: The ID of the resume to retrieve

    Returns:
        Combined data from both resume and processed_resume models

    Raises:
        HTTPException: If the resume is not found or if there's an error fetching data.
    """
    request_id = getattr(request.state, "request_id", str(uuid4()))
    headers = {"X-Request-ID": request_id}

    try:
        if not resume_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="resume_id is required",
            )

        resume_service = ResumeService(db)
        resume_data = await resume_service.get_resume_with_processed_data(
            resume_id=resume_id
        )
        
        if not resume_data:
            raise ResumeNotFoundError(
                message=f"Resume with id {resume_id} not found"
            )

        return JSONResponse(
            content={
                "request_id": request_id,
                "data": resume_data,
            },
            headers=headers,
        )
    
    except ResumeNotFoundError as e:
        logger.error(str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error fetching resume: {str(e)} - traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching resume data",
        )


@resume_router.post(
    "/process-enhanced",
    summary="Upload Resume with FitScore AI Analysis",
    description="Upload and analyze resume using FitScore's advanced AI algorithms for ATS optimization",
    tags=["FitScore Enhanced Features"]
)
async def process_resume_enhanced(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Enhanced resume processing with comprehensive AI analysis.
    
    This endpoint:
    1. Converts PDF/DOCX to structured data
    2. Performs AI analysis and scoring
    3. Generates ATS compatibility feedback
    4. Provides improvement suggestions
    
    Returns enhanced resume data with AI analysis results.
    """
    request_id = getattr(request.state, "request_id", str(uuid4()))
    headers = {"X-Request-ID": request_id}

    # File validation (same as existing upload endpoint)
    allowed_content_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]

    if file.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF and DOCX files are allowed.",
        )

    MAX_FILE_SIZE = 2 * 1024 * 1024
    file_bytes = await file.read()
    
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file. Please upload a valid file.",
        )

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds maximum allowed size of 2.0MB.",
        )

    try:
        enhanced_service = EnhancedResumeService(db)
        result = await enhanced_service.process_resume_with_analysis(
            file_bytes=file_bytes,
            file_type=file.content_type,
            filename=file.filename
        )
        
        return JSONResponse(
            content={
                "request_id": request_id,
                "message": "Resume processed successfully with FitScore AI analysis",
                "status": "success",
                "data": result,
                "generated_by": "FitScore by Clarivue AI"
            },
            headers=headers,
        )

    except ResumeValidationError as e:
        logger.warning(f"Resume validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Enhanced processing failed: {str(e)} - traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enhanced processing failed: {str(e)}",
        )


@resume_router.post(
    "/analyze-match",
    summary="FitScore Resume-Job Matching Analysis",
    description="Analyze resume against job requirements using FitScore's AI matching algorithms",
    tags=["FitScore Enhanced Features"]
)
async def analyze_resume_job_match(
    request: Request,
    resume_id: str,
    job_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Comprehensive resume-job matching analysis.
    
    This endpoint:
    1. Analyzes skills, experience, education, and keyword compatibility
    2. Calculates detailed match scores
    3. Generates specific improvement suggestions
    4. Identifies gaps and strengths
    
    Args:
        resume_id: ID of the processed resume
        job_id: ID of the processed job
    
    Returns:
        Detailed match analysis with improvement recommendations
    """
    request_id = getattr(request.state, "request_id", str(uuid4()))
    headers = {"X-Request-ID": request_id}

    try:
        if not resume_id or not job_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both resume_id and job_id are required",
            )

        improvement_service = ImprovementService(db)
        result = await improvement_service.generate_improvements(
            resume_id=resume_id,
            job_id=job_id
        )
        
        return JSONResponse(
            content={
                "request_id": request_id,
                "message": "FitScore match analysis completed successfully",
                "generated_by": "FitScore by Clarivue AI",
                **result
            },
            headers=headers,
        )

    except ResumeNotFoundError as e:
        logger.error(f"Resume not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except JobNotFoundError as e:
        logger.error(f"Job not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ImprovementGenerationError as e:
        logger.error(f"Improvement generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Match analysis failed: {str(e)} - traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Match analysis failed",
        )


@resume_router.get(
    "/{resume_id}/matches",
    summary="Get FitScore Match History",
    description="Retrieve all match analyses performed for a specific resume using FitScore",
    tags=["FitScore Enhanced Features"]
)
async def get_resume_match_history(
    request: Request,
    resume_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Retrieve all match analyses performed for a specific resume.
    
    Args:
        resume_id: ID of the resume to get match history for
    
    Returns:
        List of all match results with scores and improvement suggestions
    """
    request_id = getattr(request.state, "request_id", str(uuid4()))
    headers = {"X-Request-ID": request_id}

    try:
        if not resume_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="resume_id is required",
            )

        improvement_service = ImprovementService(db)
        match_history = await improvement_service.get_match_history(resume_id)
        
        return JSONResponse(
            content={
                "request_id": request_id,
                "message": "FitScore match history retrieved successfully",
                "generated_by": "FitScore by Clarivue AI",
                "data": {
                    "resume_id": resume_id,
                    "match_count": len(match_history),
                    "matches": [match.dict() for match in match_history]
                }
            },
            headers=headers,
        )

    except Exception as e:
        logger.error(f"Failed to get match history: {str(e)} - traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve match history",
        )