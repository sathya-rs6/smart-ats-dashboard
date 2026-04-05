"""
Resume Analyzer RAG Application
Main entry point for the Resume Analyzer with RAG capabilities.
"""
import os
import sys
import logging
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status, BackgroundTasks

# Ensure the backend directory is in the path for local imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
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
from core.ranking import RankingService
from core.email_service import EmailService

from routers import auth
from core.security import get_current_user
from fastapi.security import OAuth2PasswordBearer


# Configure logging
try:
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=settings.log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(settings.log_file) if settings.log_file else logging.NullHandler(),
            logging.StreamHandler()
        ]
    )
except Exception as e:
    print(f"Logging setup failed, using basic config: {e}")
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
logger.info(f"Starting Smart ATS from: {os.getcwd()}")

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

app.include_router(auth.router)


# Static files directory
STATIC_DIR = Path("frontend_v2/dist")
try:
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
except Exception as e:
    logger.warning(f"Could not create static directory: {e}")

# Mount static files
assets_dir = STATIC_DIR / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

# Keep old frontend path mounted in case it's used elsewhere
old_frontend_dir = Path("frontend")
if old_frontend_dir.exists():
    app.mount("/frontend", StaticFiles(directory=str(old_frontend_dir)), name="frontend_old")

# Serve the frontend
@app.get("/")
async def serve_frontend():
    """Serve the main frontend page"""
    index_path = STATIC_DIR / "index.html"
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
    }
    if index_path.exists():
        return FileResponse(index_path, headers=headers)
        
    old_index_path = Path("frontend_backup/index.html")
    if old_index_path.exists():
        return FileResponse(old_index_path, headers=headers)
        
    return {"message": "Frontend index.html not found", "docs": "/docs"}

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

# Upload directory is already handled above

# Request models
class AnalyzeRequest(BaseModel):
    resume_id: int
    job_description_id: int

class ChatRequest(BaseModel):
    resume_id: int
    query: str

class NotificationRequest(BaseModel):
    candidate_id: int
    job_id: int
    smtp_app_password: Optional[str] = None
    smtp_email: Optional[str] = None

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
@app.get("/info")
async def api_info():
    """API information endpoint"""
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
    """Upload a single resume file"""
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

@app.get("/resumes/file/{resume_id}")
async def get_resume_file(resume_id: int, db: Session = Depends(get_db)):
    """Serve the raw resume file (PDF/Doc) inline"""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume or not os.path.exists(resume.file_path):
        raise HTTPException(status_code=404, detail="Resume file not found")
    
    # Avoid setting attachment to allow modern browsers to render PDFs inline
    headers = {"Content-Disposition": f"inline; filename={resume.file_name}"}
    return FileResponse(resume.file_path, headers=headers, media_type=resume.file_type)

@app.get("/resumes/")
async def get_all_resumes(db: Session = Depends(get_db)):
    """Retrieve a list of all resumes"""
    try:
        resumes = db.query(Resume).order_by(Resume.id.desc()).all()
        result = []
        for r in resumes:
            try:
                extracted = r.extracted_data or {}
                if isinstance(extracted, str):
                    import json
                    extracted = json.loads(extracted)
                personal = extracted.get("personal_info", {})
                result.append({
                    "id": r.id,
                    "file_name": r.file_name,
                    "status": r.status,
                    "candidate_name": personal.get("name") or personal.get("full_name") or "Unknown",
                    "candidate_email": personal.get("email") or "N/A"
                })
            except Exception as record_err:
                logger.warning(f"Error serializing resume {r.id}: {record_err}")
                result.append({
                    "id": r.id,
                    "file_name": r.file_name,
                    "status": r.status,
                    "candidate_name": r.file_name,
                    "candidate_email": "N/A"
                })
        return result
    except Exception as e:
        logger.error(f"Error retrieving resumes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_resume_background(resume_id: int, file_path: str, db_url: str):
    """Background task to process a single resume"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Parse the resume
        parser = ResumeParser()
        parsed_data = parser.parse_resume(file_path)
        
        # Update resume record
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if resume:
            resume.status = "processed"
            resume.extracted_data = parsed_data
            db.commit()
            logger.info(f"Processed resume {resume_id} in background")
            
            # Analyze against all jobs
            jobs = db.query(JobDescription).all()
            if jobs:
                from core.scoring import ResumeScorer, generate_feedback
                from datetime import datetime
                
                for job in jobs:
                    existing = db.query(ResumeAnalysis).filter_by(resume_id=resume.id, job_description_id=job.id).first()
                    if existing:
                        continue
                        
                    job_dict = {
                        'id': job.id, 'title': job.title, 'company': job.company, 'location': job.location,
                        'description': job.description, 'requirements': job.requirements,
                        'required_skills': job.required_skills, 'preferred_skills': job.preferred_skills,
                        'required_experience': job.required_experience, 'required_education': job.required_education,
                        'required_certifications': job.required_certifications
                    }
                    
                    scorer = ResumeScorer(job_dict)
                    score_breakdown = scorer.calculate_score(parsed_data or {})
                    feedback = generate_feedback(score_breakdown)
                    
                    analysis_record = ResumeAnalysis(
                        resume_id=resume.id,
                        job_description_id=job.id,
                        overall_score=score_breakdown.overall_score * 100,
                        skill_score=score_breakdown.skill_score * 100,
                        experience_score=score_breakdown.experience_score * 100,
                        education_score=score_breakdown.education_score * 100,
                        certification_score=score_breakdown.certification_score * 100,
                        keyword_score=score_breakdown.keyword_score * 100,
                        match_level=score_breakdown.match_level.value,
                        missing_skills=score_breakdown.missing_skills,
                        missing_keywords=score_breakdown.missing_keywords,
                        feedback=feedback,
                        analysis_date=datetime.utcnow()
                    )
                    db.add(analysis_record)
                
                db.commit()
                logger.info(f"Analyzed resume {resume_id} against {len(jobs)} jobs")
    except Exception as e:
        logger.error(f"Error processing resume {resume_id} in background: {e}")
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if resume:
            resume.status = "error"
            db.commit()
    finally:
        db.close()

async def analyze_all_resumes_for_job_background(job_id: int, db_url: str):
    """Background task to analyze all processed resumes for a newly created job"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from core.scoring import ResumeScorer, generate_feedback
    from datetime import datetime
    
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
        if not job:
            return
            
        job_dict = {
            'id': job.id, 'title': job.title, 'company': job.company, 'location': job.location,
            'description': job.description, 'requirements': job.requirements,
            'required_skills': job.required_skills, 'preferred_skills': job.preferred_skills,
            'required_experience': job.required_experience, 'required_education': job.required_education,
            'required_certifications': job.required_certifications
        }
        scorer = ResumeScorer(job_dict)
        
        resumes = db.query(Resume).filter(Resume.status == "processed").all()
        for resume in resumes:
            existing = db.query(ResumeAnalysis).filter_by(resume_id=resume.id, job_description_id=job.id).first()
            if existing:
                continue
                
            score_breakdown = scorer.calculate_score(resume.extracted_data or {})
            feedback = generate_feedback(score_breakdown)
            
            analysis_record = ResumeAnalysis(
                resume_id=resume.id,
                job_description_id=job.id,
                overall_score=score_breakdown.overall_score * 100,
                skill_score=score_breakdown.skill_score * 100,
                experience_score=score_breakdown.experience_score * 100,
                education_score=score_breakdown.education_score * 100,
                certification_score=score_breakdown.certification_score * 100,
                keyword_score=score_breakdown.keyword_score * 100,
                match_level=score_breakdown.match_level.value,
                missing_skills=score_breakdown.missing_skills,
                missing_keywords=score_breakdown.missing_keywords,
                feedback=feedback,
                analysis_date=datetime.utcnow()
            )
            db.add(analysis_record)
            
        db.commit()
        logger.info(f"Analyzed {len(resumes)} resumes for new job {job_id}")
    except Exception as e:
        logger.error(f"Error evaluating resumes for job {job_id} in background: {e}")
    finally:
        db.close()

@app.post("/resumes/bulk-upload/")
async def bulk_upload_resumes(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Upload multiple resume files and process in background"""
    uploaded_resumes = []
    
    for file in files:
        try:
            # Save the uploaded file
            file_path = RESUME_DIR / file.filename
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Create resume record in database with "pending" status
            resume = Resume(
                file_name=file.filename,
                file_path=str(file_path),
                file_size=file_path.stat().st_size,
                file_type=file.content_type,
                status="pending"
            )
            
            db.add(resume)
            db.commit()
            db.refresh(resume)
            
            # Add to background tasks
            background_tasks.add_task(
                process_resume_background, 
                resume.id, 
                str(file_path), 
                settings.database_url
            )
            
            uploaded_resumes.append({
                "resume_id": resume.id,
                "file_name": resume.file_name,
                "status": "pending"
            })
            
        except Exception as e:
            logger.error(f"Error in bulk upload for {file.filename}: {e}")
            # Continue with other files
            continue
        finally:
            file.file.close()
            
    return {
        "message": f"Successfully uploaded {len(uploaded_resumes)} resumes. Processing started in background.",
        "resumes": uploaded_resumes
    }

@app.post("/job-descriptions/")
async def create_job_description(
    job_data: JobDescriptionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new job description with automated requirement extraction"""
    try:
        # Initialize analyzer to extract structured data
        analyzer = ResumeAnalyzer()
        structured_requirements = analyzer.analyze_job_description(job_data.description)
        
        # Merge extracted data with provided data
        job_dict = job_data.model_dump() if hasattr(job_data, "model_dump") else job_data.dict()
        
        # Override with extracted data if available
        if "error" not in structured_requirements:
            job_dict["title"] = structured_requirements.get("title", job_dict["title"])
            job_dict["required_skills"] = list(set(job_dict.get("required_skills", []) + structured_requirements.get("required_skills", [])))
            job_dict["preferred_skills"] = list(set(job_dict.get("preferred_skills", []) + structured_requirements.get("preferred_skills", [])))
            job_dict["required_experience"] = float(structured_requirements.get("required_experience", job_dict.get("required_experience", 0)))
            job_dict["required_education"] = list(set(job_dict.get("required_education", []) + structured_requirements.get("required_education", [])))
            job_dict["required_certifications"] = list(set(job_dict.get("required_certifications", []) + structured_requirements.get("required_certifications", [])))

        job = JobDescription(**job_dict)
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # Trigger background analysis of all existing resumes for this new job
        background_tasks.add_task(
            analyze_all_resumes_for_job_background,
            job.id,
            settings.database_url
        )
        
        return job
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating job description: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job description: {str(e)}"
        )

@app.get("/jobs/")
async def get_jobs(db: Session = Depends(get_db)):
    """Get all job descriptions"""
    jobs = db.query(JobDescription).order_by(JobDescription.id.desc()).all()
    return jobs

@app.get("/analyses/")
async def get_analyses(db: Session = Depends(get_db)):
    """Get all analyses history"""
    results = (
        db.query(ResumeAnalysis, Resume, JobDescription)
        .join(Resume, ResumeAnalysis.resume_id == Resume.id)
        .join(JobDescription, ResumeAnalysis.job_description_id == JobDescription.id)
        .order_by(ResumeAnalysis.id.desc())
        .limit(50)
        .all()
    )
    
    history = []
    for analysis, resume, job in results:
        history.append({
            "id": analysis.id,
            "resume_id": resume.id,
            "job_id": job.id,
            "candidate_name": resume.extracted_data.get("personal_info", {}).get("name", resume.file_name) if resume.extracted_data else resume.file_name,
            "job_title": job.title,
            "overall_score": round(analysis.overall_score, 1),
            "match_level": analysis.match_level,
            "date": str(analysis.analysis_date)
        })
    return history

@app.get("/resumes/top/")
async def get_top_resumes(limit: int = 10, db: Session = Depends(get_db)):
    """Get the globally highest-scoring resumes across all job analyses"""
    try:
        results = (
            db.query(ResumeAnalysis, Resume)
            .join(Resume, ResumeAnalysis.resume_id == Resume.id)
            .order_by(ResumeAnalysis.overall_score.desc())
            .limit(limit)
            .all()
        )

        top = []
        seen = set()
        for analysis, resume in results:
            if resume.id in seen:
                continue
            seen.add(resume.id)
            try:
                extracted = resume.extracted_data or {}
                if isinstance(extracted, str):
                    import json as _json
                    extracted = _json.loads(extracted)
                personal = extracted.get("personal_info", {})
                name = personal.get("name") or resume.file_name
                email = personal.get("email") or "N/A"
            except Exception:
                name = resume.file_name
                email = "N/A"

            top.append({
                "rank": len(top) + 1,
                "resume_id": resume.id,
                "candidate_name": name,
                "candidate_email": email,
                "overall_score": round(analysis.overall_score, 1),
                "match_level": analysis.match_level,
                "skill_score": round(analysis.skill_score or 0, 1),
                "experience_score": round(analysis.experience_score or 0, 1),
                "education_score": round(analysis.education_score or 0, 1),
                "certification_score": round(analysis.certification_score or 0, 1),
                "keyword_score": round(analysis.keyword_score or 0, 1),
                "missing_skills": analysis.missing_skills if isinstance(analysis.missing_skills, list) else [],
                "file_name": resume.file_name,
                "experience": extracted.get("experience", []) if isinstance(extracted, dict) else []
            })
        return {"rankings": top}
    except Exception as e:
        logger.error(f"Error getting top resumes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs/{job_id}/rankings")
async def get_job_rankings(
    job_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get top ranked candidates for a specific job"""
    rankings = RankingService.get_top_candidates(db, job_id, limit)
    return {"job_id": job_id, "rankings": rankings}

@app.get("/dashboard/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get statistics for the recruiter dashboard"""
    stats = RankingService.get_recruiter_stats(db)
    return stats

@app.post("/chat/")
async def chat_with_resume(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Query a specific resume using RAG"""
    resume = db.query(Resume).filter(Resume.id == request.resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
        
    try:
        analyzer = ResumeAnalyzer()
        # In a real app, we'd ensure the index is active for this resume
        # analyzer.initialize_for_resume(resume.file_path)
        
        # We simulate the answer with LLM using the parsed content as context
        context = str(resume.extracted_data)
        prompt = f"Given this resume context: {context}\n\nAnswer the user's query: {request.query}"
        
        if not analyzer.llm:
            analyzer._initialize_llm()
            
        response = analyzer.llm.invoke(prompt)
        return {"answer": response.content}
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {"answer": f"I encountered an error analyzing this resume: {str(e)}"}

@app.post("/notifications/shortlist")
async def notify_shortlisted(
    request: NotificationRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Send an email to a shortlisted candidate using the logged-in user's credentials"""
    resume = db.query(Resume).filter(Resume.id == request.candidate_id).first()
    job = db.query(JobDescription).filter(JobDescription.id == request.job_id).first()
    
    if not resume or not job:
        raise HTTPException(status_code=404, detail="Candidate or Job not found")
        
    candidate_name = resume.extracted_data.get("personal_info", {}).get("name", "Unknown") if resume.extracted_data else "Unknown"
    candidate_email = resume.extracted_data.get("personal_info", {}).get("email", "Unknown") if resume.extracted_data else "Unknown"
    
    # Send email natively using request password or fallback to global SMTP credentials
    email_service = EmailService()
    hr_app_password = request.smtp_app_password if getattr(request, 'smtp_app_password', None) else (getattr(current_user, 'smtp_app_password', None) or None)
    hr_email = request.smtp_email if getattr(request, 'smtp_email', None) else None
    
    success = email_service.send_shortlist_email(
        candidate_name=candidate_name, 
        candidate_email=candidate_email, 
        job_title=job.title,
        hr_email=hr_email,
        hr_app_password=hr_app_password
    )
    
    if success:
        return {"message": "Notification sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send notification. Verify your App Password is correct in your profile.")


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
            feedback=feedback,
            analysis_date=datetime.utcnow()
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
        reload=False,
        log_level=settings.log_level.lower()
    )
