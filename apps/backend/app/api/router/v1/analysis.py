import logging
import traceback

from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, HTTPException, Depends, Request, status, Query
from fastapi.responses import JSONResponse

from app.core import get_db_session
from app.services.enhanced_resume_service import EnhancedResumeService
from app.services.enhanced_job_service import EnhancedJobService
from app.services.improvement_service import ImprovementService
from app.services.exceptions import (
    ResumeNotFoundError,
    JobNotFoundError,
    ImprovementGenerationError
)

analysis_router = APIRouter()
logger = logging.getLogger(__name__)


@analysis_router.get(
    "/dashboard/{resume_id}",
    summary="Get comprehensive dashboard data for a resume including all analyses and matches",
)
async def get_resume_dashboard(
    request: Request,
    resume_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Comprehensive dashboard endpoint that provides:
    1. Enhanced resume data with AI analysis
    2. All match results and scores
    3. Improvement suggestions summary
    4. ATS compatibility insights
    
    Args:
        resume_id: ID of the resume to get dashboard data for
    
    Returns:
        Complete dashboard data with analytics
    """
    request_id = getattr(request.state, "request_id", str(uuid4()))
    headers = {"X-Request-ID": request_id}

    try:
        if not resume_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="resume_id is required",
            )

        # Get enhanced resume data
        resume_service = EnhancedResumeService(db)
        resume_data = await resume_service.get_resume_with_analysis(resume_id)
        
        if not resume_data:
            raise ResumeNotFoundError(resume_id=resume_id)

        # Get match history
        improvement_service = ImprovementService(db)
        match_history = await improvement_service.get_match_history(resume_id)
        
        # Calculate summary statistics
        total_matches = len(match_history)
        avg_score = sum([match.overall_match_score for match in match_history]) / total_matches if total_matches > 0 else 0
        best_match = max(match_history, key=lambda x: x.overall_match_score) if match_history else None
        
        # Recent matches (last 5)
        recent_matches = sorted(match_history, key=lambda x: x.created_at, reverse=True)[:5]
        
        dashboard_data = {
            "resume_id": resume_id,
            "resume_data": resume_data,
            "analytics": {
                "total_matches_performed": total_matches,
                "average_match_score": round(avg_score, 3),
                "best_match_score": best_match.overall_match_score if best_match else 0,
                "best_match_job_id": best_match.job_id if best_match else None,
                "ats_compatibility_score": resume_data.get("ai_analysis_scores", {}).get("ats_compatibility_score", 0)
            },
            "recent_matches": [match.dict() for match in recent_matches],
            "improvement_summary": {
                "total_suggestions": sum([len(match.improvement_suggestions) for match in match_history]),
                "common_gaps": _extract_common_gaps(match_history),
                "skill_recommendations": _extract_skill_recommendations(match_history)
            }
        }
        
        return JSONResponse(
            content={
                "request_id": request_id,
                "data": dashboard_data
            },
            headers=headers,
        )

    except ResumeNotFoundError as e:
        logger.error(f"Resume not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Dashboard data retrieval failed: {str(e)} - traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard data",
        )


@analysis_router.get(
    "/bulk-analysis/{resume_id}",
    summary="Perform bulk analysis of a resume against multiple jobs",
)
async def bulk_resume_analysis(
    request: Request,
    resume_id: str,
    job_ids: str = Query(..., description="Comma-separated list of job IDs"),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Analyze a resume against multiple job descriptions in a single request.
    
    Args:
        resume_id: ID of the resume to analyze
        job_ids: Comma-separated string of job IDs (e.g., "job1,job2,job3")
    
    Returns:
        Bulk analysis results with ranking and comparison
    """
    request_id = getattr(request.state, "request_id", str(uuid4()))
    headers = {"X-Request-ID": request_id}

    try:
        if not resume_id or not job_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both resume_id and job_ids are required",
            )

        # Parse job IDs
        job_id_list = [jid.strip() for jid in job_ids.split(",") if jid.strip()]
        if not job_id_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one valid job_id is required",
            )

        improvement_service = ImprovementService(db)
        results = []
        
        # Process each job
        for job_id in job_id_list:
            try:
                result = await improvement_service.generate_improvements(
                    resume_id=resume_id,
                    job_id=job_id
                )
                results.append({
                    "job_id": job_id,
                    "status": "success",
                    **result
                })
            except Exception as e:
                logger.warning(f"Analysis failed for job {job_id}: {str(e)}")
                results.append({
                    "job_id": job_id,
                    "status": "failed",
                    "error": str(e)
                })
        
        # Sort by match score (successful analyses only)
        successful_results = [r for r in results if r["status"] == "success"]
        successful_results.sort(
            key=lambda x: x.get("match_result", {}).get("overall_match_score", 0), 
            reverse=True
        )
        
        # Calculate summary
        total_jobs = len(job_id_list)
        successful_analyses = len(successful_results)
        best_match = successful_results[0] if successful_results else None
        
        bulk_analysis_data = {
            "resume_id": resume_id,
            "summary": {
                "total_jobs_analyzed": total_jobs,
                "successful_analyses": successful_analyses,
                "failed_analyses": total_jobs - successful_analyses,
                "best_match_job_id": best_match["job_id"] if best_match else None,
                "best_match_score": best_match.get("match_result", {}).get("overall_match_score", 0) if best_match else 0
            },
            "results": results,
            "ranking": [
                {
                    "job_id": result["job_id"],
                    "overall_score": result.get("match_result", {}).get("overall_match_score", 0),
                    "skills_score": result.get("match_result", {}).get("skills_match_score", 0),
                    "experience_score": result.get("match_result", {}).get("experience_match_score", 0)
                }
                for result in successful_results
            ]
        }
        
        return JSONResponse(
            content={
                "request_id": request_id,
                "data": bulk_analysis_data
            },
            headers=headers,
        )

    except ResumeNotFoundError as e:
        logger.error(f"Resume not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Bulk analysis failed: {str(e)} - traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bulk analysis failed",
        )


@analysis_router.get(
    "/comparison",
    summary="Compare match results between different resume-job combinations",
)
async def compare_matches(
    request: Request,
    resume_ids: str = Query(..., description="Comma-separated resume IDs"),
    job_id: str = Query(..., description="Job ID to compare against"),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Compare how different resumes perform against the same job.
    Useful for understanding which resume variations work best.
    
    Args:
        resume_ids: Comma-separated string of resume IDs
        job_id: Job ID to compare all resumes against
    
    Returns:
        Comparative analysis with rankings and insights
    """
    request_id = getattr(request.state, "request_id", str(uuid4()))
    headers = {"X-Request-ID": request_id}

    try:
        if not resume_ids or not job_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both resume_ids and job_id are required",
            )

        # Parse resume IDs
        resume_id_list = [rid.strip() for rid in resume_ids.split(",") if rid.strip()]
        if not resume_id_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one valid resume_id is required",
            )

        improvement_service = ImprovementService(db)
        comparison_results = []
        
        # Analyze each resume against the job
        for resume_id in resume_id_list:
            try:
                result = await improvement_service.generate_improvements(
                    resume_id=resume_id,
                    job_id=job_id
                )
                comparison_results.append({
                    "resume_id": resume_id,
                    "status": "success",
                    **result
                })
            except Exception as e:
                logger.warning(f"Comparison failed for resume {resume_id}: {str(e)}")
                comparison_results.append({
                    "resume_id": resume_id,
                    "status": "failed",
                    "error": str(e)
                })
        
        # Sort by overall match score
        successful_comparisons = [r for r in comparison_results if r["status"] == "success"]
        successful_comparisons.sort(
            key=lambda x: x.get("match_result", {}).get("overall_match_score", 0), 
            reverse=True
        )
        
        # Generate insights
        if len(successful_comparisons) >= 2:
            best_resume = successful_comparisons[0]
            worst_resume = successful_comparisons[-1]
            score_difference = (
                best_resume.get("match_result", {}).get("overall_match_score", 0) - 
                worst_resume.get("match_result", {}).get("overall_match_score", 0)
            )
        else:
            score_difference = 0
        
        comparison_data = {
            "job_id": job_id,
            "total_resumes_compared": len(resume_id_list),
            "successful_comparisons": len(successful_comparisons),
            "score_range": {
                "highest": successful_comparisons[0].get("match_result", {}).get("overall_match_score", 0) if successful_comparisons else 0,
                "lowest": successful_comparisons[-1].get("match_result", {}).get("overall_match_score", 0) if successful_comparisons else 0,
                "difference": score_difference
            },
            "results": comparison_results,
            "ranking": [
                {
                    "resume_id": result["resume_id"],
                    "rank": idx + 1,
                    "overall_score": result.get("match_result", {}).get("overall_match_score", 0),
                    "key_strengths": result.get("match_result", {}).get("matching_skills", [])[:3]
                }
                for idx, result in enumerate(successful_comparisons)
            ]
        }
        
        return JSONResponse(
            content={
                "request_id": request_id,
                "data": comparison_data
            },
            headers=headers,
        )

    except JobNotFoundError as e:
        logger.error(f"Job not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Comparison failed: {str(e)} - traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Comparison analysis failed",
        )


def _extract_common_gaps(match_history) -> list:
    """Extract most common gaps from match history"""
    gap_counts = {}
    for match in match_history:
        if match.match_analysis and hasattr(match.match_analysis, 'gap_analysis'):
            gaps = match.match_analysis.gap_analysis.get("major_gaps", [])
            for gap in gaps:
                gap_counts[gap] = gap_counts.get(gap, 0) + 1
    
    # Return top 5 most common gaps
    sorted_gaps = sorted(gap_counts.items(), key=lambda x: x[1], reverse=True)
    return [gap for gap, count in sorted_gaps[:5]]


def _extract_skill_recommendations(match_history) -> list:
    """Extract most recommended skills from match history"""
    skill_counts = {}
    for match in match_history:
        missing_skills = match.missing_skills or []
        for skill in missing_skills:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1
    
    # Return top 10 most recommended skills
    sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
    return [skill for skill, count in sorted_skills[:10]]