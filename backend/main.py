"""
Resume Analyzer RAG Application
Main entry point for the Resume Analyzer with RAG capabilities.
"""
import os
import sys
import logging
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from pathlib import Path
import shutil

# Import local modules
from config.settings import settings
from models.database import (
    init_database, Resume, JobDescription, ResumeAnalysis,
    ResumeCreate, JobDescriptionCreate, ResumeAnalysisCreate,
    DatabaseManager
)
from core.analyzer import ResumeAnalyzer
from core.parser import ResumeParser
from core.scoring import ResumeScorer, generate_feedback

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Resume Analyzer RAG API",
    description="API for analyzing resumes using RAG (Retrieval-Augmented Generation)",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# Serve the frontend
@app.get("/")
async def serve_frontend():
    """Serve the main frontend page"""
    return FileResponse("frontend/index.html")

# Initialize database
try:
    SessionLocal = init_database()
    db_manager = DatabaseManager(settings.database_url)
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    sys.exit(1)

# Create upload directories
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
RESUME_DIR = UPLOAD_DIR / "resumes"
RESUME_DIR.mkdir(exist_ok=True)

# Create static directory if it doesn't exist
STATIC_DIR = Path("frontend")
STATIC_DIR.mkdir(exist_ok=True)

# Mount static files
try:
    app.mount("/frontend", StaticFiles(directory=str(STATIC_DIR)), name="frontend")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")

# Request models
class AnalyzeRequest(BaseModel):
    resume_id: int
    job_description_id: int

class QuestionRequest(BaseModel):
    resume_id: int
    question: str

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Resume Analyzer RAG API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.post("/resumes/upload/")
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a resume file"""
    try:
        # Save the uploaded file
        file_path = RESUME_DIR / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Parse the resume
        parser = ResumeParser()
        parsed_data = parser.parse_resume(str(file_path))
        
        # Create resume record in database
        resume = Resume(
            file_name=file.filename,
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            file_type=file.content_type,
            status="processed",
            extracted_data=parsed_data
        )
        
        db.add(resume)
        db.commit()
        db.refresh(resume)
        
        return {
            "message": "Resume uploaded and processed successfully",
            "resume_id": resume.id,
            "file_name": resume.file_name,
            "extracted_data": parsed_data
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error uploading resume: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process resume: {str(e)}"
        )
    finally:
        file.file.close()

@app.post("/job-descriptions/")
async def create_job_description(
    job_data: JobDescriptionCreate,
    db: Session = Depends(get_db)
):
    """Create a new job description"""
    try:
        # Convert Pydantic model to dict (compatible with both v1 and v2)
        try:
            job_dict = job_data.model_dump()  # Pydantic v2
        except AttributeError:
            job_dict = job_data.dict()  # Pydantic v1
            
        job = JobDescription(**job_dict)
        db.add(job)
        db.commit()
        db.refresh(job)
        return job
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating job description: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job description"
        )

@app.post("/analyze/")
async def analyze_resume(
    request: AnalyzeRequest,
    db: Session = Depends(get_db)
):
    """Analyze a resume against a job description"""
    try:
        # Get resume and job description
        resume = db.query(Resume).filter(Resume.id == request.resume_id).first()
        job_description = db.query(JobDescription).filter(
            JobDescription.id == request.job_description_id
        ).first()
        
        if not resume or not job_description:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume or Job Description not found"
            )
        
        # Initialize analyzer and scorer
        analyzer = ResumeAnalyzer()
        
        # Convert SQLAlchemy model to dict (compatible approach)
        job_dict = {
            'id': job_description.id,
            'title': job_description.title,
            'company': job_description.company,
            'location': job_description.location,
            'description': job_description.description,
            'requirements': job_description.requirements,
            'required_skills': job_description.required_skills,
            'preferred_skills': job_description.preferred_skills,
            'required_experience': job_description.required_experience,
            'required_education': job_description.required_education,
            'required_certifications': job_description.required_certifications
        }
        
        scorer = ResumeScorer(job_dict)
        
        # Process resume with RAG
        analyzer.load_and_process_resume(resume.file_path)
        analyzer.create_vector_store(analyzer.docs)
        analyzer.create_qa_chain()
        
        # Generate comprehensive analysis
        analysis = analyzer.analyze_resume_comprehensive(resume.file_path)
        
        # Calculate scores
        score_breakdown = scorer.calculate_score(resume.extracted_data or {})
        feedback = generate_feedback(score_breakdown)
        
        # Save analysis to database
        analysis_record = ResumeAnalysis(
            resume_id=resume.id,
            job_description_id=job_description.id,
            overall_score=score_breakdown.overall_score * 100,  # Convert to percentage
            skill_score=score_breakdown.skill_score * 100,
            experience_score=score_breakdown.experience_score * 100,
            education_score=score_breakdown.education_score * 100,
            certification_score=score_breakdown.certification_score * 100,
            keyword_score=score_breakdown.keyword_score * 100,
            match_level=score_breakdown.match_level.value,
            missing_skills=score_breakdown.missing_skills,
            missing_keywords=score_breakdown.missing_keywords,
            feedback=feedback
        )
        
        db.add(analysis_record)
        db.commit()
        db.refresh(analysis_record)
        
        return {
            "analysis_id": analysis_record.id,
            "resume_id": resume.id,
            "job_description_id": job_description.id,
            "scores": {
                "overall": score_breakdown.overall_score * 100,
                "skill": score_breakdown.skill_score * 100,
                "experience": score_breakdown.experience_score * 100,
                "education": score_breakdown.education_score * 100,
                "certification": score_breakdown.certification_score * 100,
                "keyword": score_breakdown.keyword_score * 100,
                "match_level": score_breakdown.match_level.value
            },
            "feedback": feedback,
            "analysis": analysis
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error analyzing resume: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze resume: {str(e)}"
        )

@app.post("/ask/")
async def ask_question(
    request: QuestionRequest,
    db: Session = Depends(get_db)
):
    """Ask a question about a resume"""
    try:
        resume = db.query(Resume).filter(Resume.id == request.resume_id).first()
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )
        
        # Initialize analyzer
        analyzer = ResumeAnalyzer()
        
        # Process resume with RAG (always needed for new analyzer instance)
        analyzer.load_and_process_resume(resume.file_path)
        analyzer.create_vector_store(analyzer.docs)
        analyzer.create_qa_chain()
        
        # Ask question
        answer = analyzer.ask_question(request.question)
        
        return {
            "question": request.question,
            "answer": answer,
            "resume_id": resume.id
        }
        
    except Exception as e:
        logger.error(f"Error asking question: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process question: {str(e)}"
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    # Run the FastAPI application
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
