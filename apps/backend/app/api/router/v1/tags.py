from fastapi import APIRouter

tags_metadata = [
    {
        "name": "resumes",
        "description": "Manage and analyze resumes with Fitscore's AI-powered engine.",
    },
    {
        "name": "jobs",
        "description": "Process job descriptions and calculate resume fit scores.",
    },
    {
        "name": "improvements",
        "description": "Get AI-powered suggestions to improve resume fit scores.",
    },
    {
        "name": "analysis",
        "description": "Advanced resume analytics and keyword extraction.",
    },
]

def create_api_router(prefix: str, tags: list[str]) -> APIRouter:
    """Create an API router with Fitscore's standard configuration"""
    return APIRouter(
        prefix=f"/api/v1/{prefix}",
        tags=tags,
    )