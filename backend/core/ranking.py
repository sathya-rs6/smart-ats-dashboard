"""
Ranking Service
Handles sorting and retrieving the best matching candidates for a job description.
"""
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from models.database import Resume, ResumeAnalysis, JobDescription

logger = logging.getLogger(__name__)

class RankingService:
    @staticmethod
    def get_top_candidates(db: Session, job_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve the top N candidates for a specific job description, 
        sorted by their overall compatibility score.
        """
        try:
            # Join ResumeAnalysis with Resume to get candidate names and file info
            results = (
                db.query(ResumeAnalysis, Resume)
                .join(Resume, ResumeAnalysis.resume_id == Resume.id)
                .filter(ResumeAnalysis.job_description_id == job_id)
                .order_by(ResumeAnalysis.overall_score.desc())
                .limit(limit)
                .all()
            )
            
            rankings = []
            for i, (analysis, resume) in enumerate(results):
                # Try to get candidate name from extracted data if available
                candidate_name = resume.extracted_data.get("personal_info", {}).get("name", "Unknown") if resume.extracted_data else "Unknown"
                if candidate_name == "Unknown":
                    candidate_name = resume.file_name
                
                candidate_email = resume.extracted_data.get("personal_info", {}).get("email", "unknown@email.com") if resume.extracted_data else "unknown@email.com"
                
                # Default skills if empty
                matched_skills = analysis.skill_feedback if isinstance(analysis.skill_feedback, list) else ["Python", "JavaScript"]

                rankings.append({
                    "rank": i + 1,
                    "resume_id": resume.id,
                    "candidate_name": candidate_name,
                    "candidate_email": candidate_email,
                    "overall_score": round(analysis.overall_score, 1),
                    "match_level": analysis.match_level,
                    "skill_score": round(analysis.skill_score, 1),
                    "experience_score": round(analysis.experience_score, 1),
                    "education_score": round(analysis.education_score, 1),
                    "certification_score": round(analysis.certification_score, 1),
                    "keyword_score": round(analysis.keyword_score, 1),
                    "matched_skills": matched_skills,
                    "missing_skills": analysis.missing_skills if isinstance(analysis.missing_skills, list) else [],
                    "file_name": resume.file_name,
                    "experience": resume.extracted_data.get("experience", []) if resume.extracted_data else []
                })
                
            return rankings
        except Exception as e:
            logger.error(f"Error retrieving rankings: {e}")
            return []

    @staticmethod
    def get_recruiter_stats(db: Session) -> Dict[str, Any]:
        """Get overall statistics for the recruiter dashboard"""
        total_resumes = db.query(Resume).count()
        total_jobs = db.query(JobDescription).count()
        total_analyses = db.query(ResumeAnalysis).count()
        
        # Match level distribution
        high_matches = db.query(ResumeAnalysis).filter(ResumeAnalysis.match_level == "high").count()
        med_matches = db.query(ResumeAnalysis).filter(ResumeAnalysis.match_level == "medium").count()
        low_matches = db.query(ResumeAnalysis).filter(ResumeAnalysis.match_level == "low").count()
        
        return {
            "total_resumes": total_resumes,
            "total_jobs": total_jobs,
            "total_analyses": total_analyses,
            "distribution": {
                "high": high_matches,
                "medium": med_matches,
                "low": low_matches
            }
        }
