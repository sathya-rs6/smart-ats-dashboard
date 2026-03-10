"""
Scoring Module
Handles the scoring and evaluation of resumes against job requirements.
"""

import logging
import re
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from fuzzywuzzy import fuzz

logger = logging.getLogger(__name__)

class ScoreWeights:
    """Default weights for different scoring components"""
    HARD_MATCH = 0.4
    SEMANTIC_MATCH = 0.6
    SKILL_MATCH = 0.35
    EXPERIENCE_MATCH = 0.25
    EDUCATION_MATCH = 0.2
    CERTIFICATION_MATCH = 0.1
    KEYWORD_MATCH = 0.1

class MatchLevel(str, Enum):
    """Match level for scoring"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class ScoreBreakdown:
    """Detailed breakdown of resume scores"""
    overall_score: float = 0.0
    skill_score: float = 0.0
    experience_score: float = 0.0
    education_score: float = 0.0
    certification_score: float = 0.0
    keyword_score: float = 0.0
    match_level: MatchLevel = MatchLevel.LOW
    missing_skills: List[str] = None
    missing_keywords: List[str] = None
    
    def __post_init__(self):
        if self.missing_skills is None:
            self.missing_skills = []
        if self.missing_keywords is None:
            self.missing_keywords = []
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "overall_score": round(self.overall_score, 2),
            "skill_score": round(self.skill_score, 2),
            "experience_score": round(self.experience_score, 2),
            "education_score": round(self.education_score, 2),
            "certification_score": round(self.certification_score, 2),
            "keyword_score": round(self.keyword_score, 2),
            "match_level": self.match_level.value,
            "missing_skills": self.missing_skills,
            "missing_keywords": self.missing_keywords
        }

class ResumeScorer:
    """Scores resumes based on job requirements"""
    
    def __init__(
        self,
        job_description: Dict[str, Any],
        weights: Optional[Dict[str, float]] = None
    ):
        """Initialize with job description and optional custom weights"""
        self.job_description = job_description
        self.weights = ScoreWeights()
        
        # Update weights if provided
        if weights:
            for key, value in weights.items():
                if hasattr(self.weights, key.upper()):
                    setattr(self.weights, key.upper(), value)
        
        # Preprocess job description
        self.required_skills = self._preprocess_skills(job_description.get("required_skills", []))
        self.preferred_skills = self._preprocess_skills(job_description.get("preferred_skills", []))
        self.required_experience = job_description.get("required_experience", 0)
        self.required_education = job_description.get("required_education", [])
        self.required_certifications = job_description.get("required_certifications", [])
        self.keywords = self._extract_keywords(job_description.get("description", ""))
    
    def _preprocess_skills(self, skills: List[str]) -> List[str]:
        """Normalize skill names for comparison"""
        processed = []
        for skill in skills:
            # Convert to lowercase and remove extra spaces
            skill = " ".join(skill.lower().strip().split())
            # Remove version numbers (e.g., Python 3.8 -> python)
            skill = re.sub(r'\s*\d+(\.\d+)*$', '', skill)
            processed.append(skill)
        return list(set(processed))  # Remove duplicates
    
    def _extract_keywords(self, text: str, top_n: int = 20) -> List[str]:
        """Extract important keywords from text"""
        if not text.strip():
            return []
            
        # Simple word frequency approach (can be enhanced with TF-IDF or RAKE)
        words = re.findall(r'\b\w{3,}\b', text.lower())
        word_counts = {}
        
        for word in words:
            if word not in ['and', 'the', 'for', 'with', 'this', 'that', 'have', 'from']:
                word_counts[word] = word_counts.get(word, 0) + 1
                
        # Sort by frequency and get top N
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:top_n]]
    
    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts using TF-IDF and cosine similarity"""
        if not text1 or not text2:
            return 0.0
            
        vectorizer = TfidfVectorizer(stop_words='english')
        try:
            tfidf = vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
            return float(similarity)
        except Exception as e:
            logger.warning(f"Error calculating semantic similarity: {e}")
            return 0.0
    
    def _calculate_fuzzy_match(self, text1: str, text2: str) -> float:
        """Calculate fuzzy string matching score"""
        if not text1 or not text2:
            return 0.0
        return fuzz.token_sort_ratio(text1.lower(), text2.lower()) / 100.0
    
    def _calculate_skill_match(self, resume_skills: List[str]) -> Tuple[float, List[str]]:
        """Calculate skill match score"""
        if not self.required_skills:
            return 1.0, []  # No required skills means perfect match
            
        resume_skills = self._preprocess_skills(resume_skills)
        
        # Calculate matches
        required_matches = 0
        missing_skills = []
        
        for req_skill in self.required_skills:
            # Check for exact or partial match
            matched = any(
                req_skill in skill or skill in req_skill 
                or self._calculate_fuzzy_match(req_skill, skill) > 0.8
                for skill in resume_skills
            )
            
            if matched:
                required_matches += 1
            else:
                missing_skills.append(req_skill)
        
        # Calculate preferred skill matches (bonus)
        preferred_matches = sum(
            1 for pref_skill in self.preferred_skills
            if any(
                pref_skill in skill or skill in pref_skill 
                or self._calculate_fuzzy_match(pref_skill, skill) > 0.8
                for skill in resume_skills
            )
        )
        
        # Calculate score (70% required, 30% preferred)
        required_score = (required_matches / len(self.required_skills)) if self.required_skills else 1.0
        preferred_score = (preferred_matches / len(self.preferred_skills)) if self.preferred_skills else 1.0
        
        total_score = (0.7 * required_score) + (0.3 * preferred_score)
        return total_score, missing_skills
    
    def _calculate_experience_match(self, experience_years: float) -> float:
        """Calculate experience match score"""
        if self.required_experience <= 0:
            return 1.0
            
        if experience_years >= self.required_experience:
            return 1.0
        else:
            # Linear scaling (can be adjusted to non-linear if needed)
            return min(experience_years / self.required_experience, 1.0)
    
    def _calculate_education_match(self, education: List[Dict[str, Any]]) -> float:
        """Calculate education match score"""
        if not self.required_education:
            return 1.0
            
        if not education:
            return 0.0
            
        # Check if any education level matches required education
        for edu in education:
            degree = edu.get("degree", "").lower()
            if any(req_edu.lower() in degree for req_edu in self.required_education):
                return 1.0
                
        return 0.0
    
    def _calculate_certification_match(self, certifications: List[str]) -> float:
        """Calculate certification match score"""
        if not self.required_certifications:
            return 1.0
            
        if not certifications:
            return 0.0
            
        # Count matching certifications
        matches = sum(
            1 for cert in certifications
            if any(
                req_cert.lower() in cert.lower() or cert.lower() in req_cert.lower()
                for req_cert in self.required_certifications
            )
        )
        
        return min(matches / len(self.required_certifications), 1.0)
    
    def _calculate_keyword_match(self, resume_text: str) -> float:
        """Calculate keyword match score"""
        if not self.keywords:
            return 1.0
            
        if not resume_text:
            return 0.0
            
        # Count matching keywords
        matches = sum(
            1 for keyword in self.keywords
            if keyword.lower() in resume_text.lower()
        )
        
        return matches / len(self.keywords)
    
    def calculate_score(self, resume_data: Dict[str, Any]) -> ScoreBreakdown:
        """Calculate overall resume score"""
        breakdown = ScoreBreakdown()
        
        try:
            # Calculate individual component scores
            breakdown.skill_score, breakdown.missing_skills = self._calculate_skill_match(
                resume_data.get("skills", [])
            )
            
            # Calculate experience score
            experience_years = float(resume_data.get("total_experience", 0))
            breakdown.experience_score = self._calculate_experience_match(experience_years)
            
            # Calculate education score
            breakdown.education_score = self._calculate_education_match(
                resume_data.get("education", [])
            )
            
            # Calculate certification score
            breakdown.certification_score = self._calculate_certification_match(
                resume_data.get("certifications", [])
            )
            
            # Calculate keyword score
            breakdown.keyword_score = self._calculate_keyword_match(
                resume_data.get("raw_text", "")
            )
            
            # Calculate overall weighted score
            breakdown.overall_score = (
                self.weights.SKILL_MATCH * breakdown.skill_score +
                self.weights.EXPERIENCE_MATCH * breakdown.experience_score +
                self.weights.EDUCATION_MATCH * breakdown.education_score +
                self.weights.CERTIFICATION_MATCH * breakdown.certification_score +
                self.weights.KEYWORD_MATCH * breakdown.keyword_score
            )
            
            # Determine match level
            if breakdown.overall_score >= 0.75:
                breakdown.match_level = MatchLevel.HIGH
            elif breakdown.overall_score >= 0.5:
                breakdown.match_level = MatchLevel.MEDIUM
            else:
                breakdown.match_level = MatchLevel.LOW
                
        except Exception as e:
            logger.error(f"Error calculating resume score: {e}")
            breakdown.overall_score = 0.0
            breakdown.match_level = MatchLevel.LOW
            
        return breakdown


def generate_feedback(breakdown: ScoreBreakdown) -> Dict[str, Any]:
    """Generate feedback based on score breakdown"""
    feedback = {
        "overall_score": round(breakdown.overall_score * 100, 1),
        "match_level": breakdown.match_level.value,
        "strengths": [],
        "improvements": [],
        "missing_skills": breakdown.missing_skills,
        "score_breakdown": {
            "skills": round(breakdown.skill_score * 100, 1),
            "experience": round(breakdown.experience_score * 100, 1),
            "education": round(breakdown.education_score * 100, 1),
            "certifications": round(breakdown.certification_score * 100, 1),
            "keywords": round(breakdown.keyword_score * 100, 1)
        }
    }
    
    # Add strengths
    if breakdown.skill_score >= 0.8:
        feedback["strengths"].append("Strong skill match with the job requirements")
    if breakdown.experience_score >= 0.8:
        feedback["strengths"].append("Meets or exceeds required experience")
    if breakdown.education_score == 1.0:
        feedback["strengths"].append("Education requirements fully met")
    if breakdown.certification_score == 1.0:
        feedback["strengths"].append("All required certifications present")
    
    # Add improvement suggestions
    if breakdown.skill_score < 0.5:
        feedback["improvements"].append(
            f"Consider adding experience with: {', '.join(breakdown.missing_skills[:3])}"
        )
    if breakdown.experience_score < 0.5:
        feedback["improvements"].append("Gain more relevant work experience")
    if breakdown.education_score == 0 and breakdown.education_score * 100 < 50:
        feedback["improvements"].append("Consider obtaining the required education")
    if breakdown.certification_score < 1.0 and len(breakdown.missing_skills) > 0:
        feedback["improvements"].append(
            f"Consider obtaining these certifications: {', '.join(breakdown.missing_skills[:3])}"
        )
    
    return feedback
