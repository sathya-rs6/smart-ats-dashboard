"""
Database models and connection management for Resume Analyzer RAG
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# SQLAlchemy Base
Base = declarative_base()

# Database Models
class Resume(Base):
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer)
    file_type = Column(String)
    upload_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")  # pending, processed, error
    extracted_data = Column(JSON)
    
    # Relationships
    analyses = relationship("ResumeAnalysis", back_populates="resume")


class JobDescription(Base):
    __tablename__ = "job_descriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    company = Column(String)
    location = Column(String)
    description = Column(Text, nullable=False)
    requirements = Column(Text)
    required_skills = Column(JSON)  # List of skills
    preferred_skills = Column(JSON)  # List of skills
    required_experience = Column(Float, default=0.0)
    required_education = Column(JSON)  # List of education levels
    required_certifications = Column(JSON)  # List of certifications
    created_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analyses = relationship("ResumeAnalysis", back_populates="job_description")


class ResumeAnalysis(Base):
    __tablename__ = "resume_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=False)
    
    # Scores
    overall_score = Column(Float)
    skill_score = Column(Float)
    experience_score = Column(Float)
    education_score = Column(Float)
    certification_score = Column(Float)
    keyword_score = Column(Float)
    
    # Analysis results
    match_level = Column(String)  # high, medium, low
    matched_skills = Column(JSON)
    missing_skills = Column(JSON)
    matched_keywords = Column(JSON)
    missing_keywords = Column(JSON)
    feedback = Column(JSON)
    
    analysis_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    resume = relationship("Resume", back_populates="analyses")
    job_description = relationship("JobDescription", back_populates="analyses")


# Pydantic Models for API
class ResumeCreate(BaseModel):
    file_name: str
    file_path: str
    file_size: int
    file_type: str
    extracted_data: Dict[str, Any] = Field(default_factory=dict)


class JobDescriptionCreate(BaseModel):
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    description: str
    requirements: Optional[str] = None
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    required_experience: float = 0.0
    required_education: List[str] = Field(default_factory=list)
    required_certifications: List[str] = Field(default_factory=list)


class ResumeAnalysisCreate(BaseModel):
    resume_id: int
    job_description_id: int
    overall_score: float = 0.0
    skill_score: float = 0.0
    experience_score: float = 0.0
    education_score: float = 0.0
    certification_score: float = 0.0
    keyword_score: float = 0.0
    match_level: str = "low"
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    matched_keywords: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    feedback: Dict[str, Any] = Field(default_factory=dict)


# Database connection and session management
class DatabaseManager:
    """Manages database connections and sessions"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
        
    def init_db(self):
        """Initialize database connection and create tables"""
        try:
            # For SQLite, ensure the directory exists
            if self.database_url.startswith('sqlite'):
                db_path = self.database_url.replace('sqlite:///', '')
                if db_path != ':memory:':
                    db_dir = os.path.dirname(db_path)
                    if db_dir:
                        os.makedirs(db_dir, exist_ok=True)
            
            # Create engine
            self.engine = create_engine(
                self.database_url, 
                connect_args={"check_same_thread": False} if self.database_url.startswith('sqlite') else {}
            )
            
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            
            # Create session maker
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            logger.info(f"Database initialized successfully: {self.database_url}")
            return self.SessionLocal
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get a new database session"""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized. Call init_db() first.")
            
        return self.SessionLocal()


# Global SessionLocal variable
SessionLocal = None

# Initialize database manager with default settings
def init_database(database_url: str = None):
    """Initialize the database with the given URL or from environment"""
    global SessionLocal
    
    if database_url is None:
        from config.settings import settings
        database_url = settings.database_url
        
    db_manager = DatabaseManager(database_url)
    SessionLocal = db_manager.init_db()
    return SessionLocal

# Auto-initialize database when module is imported
try:
    if SessionLocal is None:
        SessionLocal = init_database()
        logger.info("Database auto-initialized successfully")
except Exception as e:
    logger.warning(f"Could not auto-initialize database: {e}")
    SessionLocal = None


# Dependency to get DB session
def get_db():
    """Dependency function to get database session"""
    if SessionLocal is None:
        raise RuntimeError("Database not initialized")
        
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Example usage
if __name__ == "__main__":
    # Initialize with SQLite for testing
    db_url = "sqlite:///./test_resume_analyzer.db"
    session_maker = init_database(db_url)
    
    # Create a test session
    db = session_maker()
    
    # Example: Add a test resume
    test_resume = Resume(
        file_name="test_resume.pdf",
        file_path="/uploads/test_resume.pdf",
        file_size=1024,
        file_type="application/pdf",
        status="processed",
        extracted_data={"skills": ["Python", "SQL"], "experience": 3}
    )
    
    db.add(test_resume)
    db.commit()
    
    print(f"Created test resume with ID: {test_resume.id}")
    
    db.close()
