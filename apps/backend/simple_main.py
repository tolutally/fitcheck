from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import uuid
from datetime import datetime

# Create FastAPI app
app = FastAPI(title="Fitscore API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Fitscore API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/v1/resumes/upload")
async def upload_resume(file: UploadFile = File(...)):
    """Upload and process a resume file"""
    try:
        # Validate file type
        if not file.filename.endswith(('.pdf', '.docx')):
            raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")
        
        # Generate a unique resume ID
        resume_id = str(uuid.uuid4())
        
        # Read file content
        content = await file.read()
        
        # Create uploads directory if it doesn't exist
        uploads_dir = "uploads"
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Save file with resume_id as filename to avoid conflicts
        file_extension = os.path.splitext(file.filename)[1]
        safe_filename = f"{resume_id}{file_extension}"
        file_path = os.path.join(uploads_dir, safe_filename)
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Return success response with resume_id
        return {
            "status": "success",
            "message": "File uploaded successfully",
            "resume_id": resume_id,
            "filename": file.filename,
            "size": len(content),
            "file_path": file_path,
            "file_url": f"/uploads/{safe_filename}",
            "uploaded_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/api/v1/jobs/upload")
async def upload_job_description(job_data: dict):
    """Upload job descriptions as JSON data"""
    try:
        # Extract job descriptions and resume_id from request
        job_descriptions = job_data.get("job_descriptions", [])
        resume_id = job_data.get("resume_id", "")
        
        if not job_descriptions or not isinstance(job_descriptions, list):
            raise HTTPException(status_code=400, detail="job_descriptions must be a non-empty array")
        
        if not resume_id:
            raise HTTPException(status_code=400, detail="resume_id is required")
        
        # Generate job IDs for each description
        job_ids = []
        uploaded_jobs = []
        
        # Create uploads directory if it doesn't exist
        uploads_dir = "uploads/jobs"
        os.makedirs(uploads_dir, exist_ok=True)
        
        for i, description in enumerate(job_descriptions):
            if not description.strip():
                continue  # Skip empty descriptions
            
            # Generate a unique job ID
            job_id = str(uuid.uuid4())
            job_ids.append(job_id)
            
            # Save description as a text file
            safe_filename = f"{job_id}.txt"
            file_path = os.path.join(uploads_dir, safe_filename)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(description)
            
            uploaded_jobs.append({
                "job_id": job_id,
                "description_index": i,
                "content_length": len(description),
                "file_path": file_path,
                "file_url": f"/uploads/jobs/{safe_filename}"
            })
        
        if not job_ids:
            raise HTTPException(status_code=400, detail="No valid job descriptions provided")
        
        # Return success response with job_ids
        return {
            "status": "success",
            "message": f"Successfully uploaded {len(job_ids)} job description(s)",
            "job_id": job_ids,  # Return array as expected by frontend
            "resume_id": resume_id,
            "uploaded_jobs": uploaded_jobs,
            "uploaded_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job upload failed: {str(e)}")

@app.post("/api/v1/jobs/upload-text")
async def upload_job_description_text(job_text: dict):
    """Upload job description as text content"""
    try:
        # Extract text content from request
        text_content = job_text.get("content", "")
        if not text_content.strip():
            raise HTTPException(status_code=400, detail="Job description content cannot be empty")
        
        # Generate a unique job ID
        job_id = str(uuid.uuid4())
        
        # Create uploads directory if it doesn't exist
        uploads_dir = "uploads/jobs"
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Save text content as a file
        safe_filename = f"{job_id}.txt"
        file_path = os.path.join(uploads_dir, safe_filename)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text_content)
        
        # Return success response with job_id
        return {
            "status": "success",
            "message": "Job description uploaded successfully",
            "job_id": job_id,
            "content_length": len(text_content),
            "file_path": file_path,
            "file_url": f"/uploads/jobs/{safe_filename}",
            "uploaded_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job text upload failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("simple_main:app", host="0.0.0.0", port=8001, reload=True)