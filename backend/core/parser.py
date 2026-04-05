"""
Resume Parser Module
Handles parsing of different resume file formats and extracts structured information.
"""

import os
import re
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import fitz  # PyMuPDF
    import pdfplumber
    from docx import Document
    import spacy
    import nltk
    from sklearn.feature_extraction.text import TfidfVectorizer
    from fuzzywuzzy import fuzz, process
except ImportError as e:
    logger.warning(f"Some parsing dependencies not available: {e}")


class ResumeParser:
    """Advanced resume parser with multiple extraction methods"""

    def __init__(self):
        self.nlp = None
        self._initialize_nlp()

    def _initialize_nlp(self):
        """Initialize spaCy NLP model and NLTK data"""
        try:
            # Download necessary NLTK data
            import nltk
            for data in ['punkt', 'stopwords', 'averaged_perceptron_tagger']:
                try:
                    nltk.data.find(f'tokenizers/{data}' if data == 'punkt' else f'corpora/{data}')
                except LookupError:
                    nltk.download(data, quiet=True)
            
            # Try to load spaCy model
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Run: python -m spacy download en_core_web_sm")
            self.nlp = None
        except Exception as e:
            logger.error(f"Error initializing NLP components: {e}")

    def parse_resume(self, file_path: str) -> Dict[str, Any]:
        """Parse resume based on file extension"""
        file_extension = Path(file_path).suffix.lower()

        if file_extension == '.pdf':
            return self._parse_pdf(file_path)
        elif file_extension in ['.docx', '.doc']:
            return self._parse_docx(file_path)
        elif file_extension == '.txt':
            return self._parse_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")

    def _parse_pdf(self, file_path: str) -> Dict[str, Any]:
        """Parse PDF resume using multiple methods"""
        text_content = ""

        # Try PyMuPDF first (better for text extraction)
        try:
            doc = fitz.open(file_path)
            for page in doc:
                text_content += page.get_text()
            doc.close()
        except Exception as e:
            logger.warning(f"PyMuPDF failed, trying pdfplumber: {e}")

            # Fallback to pdfplumber
            try:
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        text_content += page.extract_text() or ""
            except Exception as e2:
                logger.error(f"Both PDF parsers failed: {e2}")
                raise ValueError(f"Could not extract text from PDF: {e2}")

        if not text_content.strip():
            raise ValueError("No text content found in PDF")

        return self._extract_information(text_content)

    def _parse_docx(self, file_path: str) -> Dict[str, Any]:
        """Parse DOCX resume"""
        try:
            doc = Document(file_path)
            text_content = ""

            for paragraph in doc.paragraphs:
                text_content += paragraph.text + "\n"

            return self._extract_information(text_content)
        except Exception as e:
            logger.error(f"Failed to parse DOCX: {e}")
            raise ValueError(f"Could not extract text from DOCX: {e}")

    def _parse_txt(self, file_path: str) -> Dict[str, Any]:
        """Parse TXT resume"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text_content = file.read()
            return self._extract_information(text_content)
        except Exception as e:
            logger.error(f"Failed to parse TXT: {e}")
            raise ValueError(f"Could not read text file: {e}")

    def _extract_information(self, text: str) -> Dict[str, Any]:
        """Extract structured information from resume text"""
        if not text.strip():
            return {}

        # Basic text cleaning
        text = self._clean_text(text)

        extracted_info = {
            'raw_text': text,
            'personal_info': self._extract_personal_info(text),
            'education': self._extract_education(text),
            'experience': self._extract_experience(text),
            'skills': self._extract_skills(text),
            'projects': self._extract_projects(text),
            'certifications': self._extract_certifications(text),
            'summary': self._extract_summary(text)
        }

        return extracted_info

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep important ones
        text = re.sub(r'[^\w\s\-.,()/@:+]', '', text)
        return text.strip()

    def _extract_personal_info(self, text: str) -> Dict[str, Any]:
        """Extract personal information"""
        personal_info = {}

        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            personal_info['email'] = emails[0]

        # Phone pattern (various formats)
        phone_patterns = [
            r'\+?\d{1,3}?[-.\s]?\(?0?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}',
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        ]

        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            if phones:
                personal_info['phone'] = phones[0]
                break

        # Name extraction (heuristic - first line or capitalized words)
        lines = text.split('\n')
        first_line = lines[0].strip() if lines else ""

        # Look for name-like patterns
        name_candidates = []
        for line in lines[:5]:  # Check first 5 lines
            words = line.split()
            if len(words) >= 2 and len(words) <= 4:
                # Check if words are capitalized (likely a name)
                if all(word[0].isupper() for word in words if word.isalpha()):
                    name_candidates.append(' '.join(words))

        if name_candidates:
            personal_info['name'] = name_candidates[0]

        # Location extraction
        location_keywords = ['location', 'address', 'city', 'state', 'country']
        for keyword in location_keywords:
            pattern = f'{keyword}[:\\s]+([^\\n]+)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                personal_info['location'] = match.group(1).strip()
                break

        return personal_info

    def _extract_education(self, text: str) -> List[Dict[str, Any]]:
        """Extract education information"""
        education = []

        # Common education keywords
        edu_keywords = [
            'education', 'degree', 'bachelor', 'master', 'phd', 'doctorate',
            'university', 'college', 'institute', 'school', 'graduated',
            'b.tech', 'm.tech', 'b.e.', 'm.e.', 'b.sc', 'm.sc', 'b.a.', 'm.a.',
            'b.com', 'm.com', 'b.b.a.', 'm.b.a.'
        ]

        lines = text.split('\n')
        edu_section_found = False

        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in edu_keywords):
                edu_section_found = True
                # Look at next few lines for education details
                for j in range(i, min(i + 5, len(lines))):
                    edu_line = lines[j].strip()
                    if edu_line and not any(keyword in edu_line.lower() for keyword in edu_keywords):

                        # Extract degree, institution, year
                        edu_entry = {}

                        # Look for years (4 digits)
                        years = re.findall(r'\b(19|20)\d{2}\b', edu_line)
                        if years:
                            edu_entry['year'] = years[0]

                        # Look for degree patterns
                        degree_patterns = [
                            r'\b(B\.Tech|M\.Tech|B\.E\.|M\.E\.|B\.Sc|M\.Sc|B\.A\.|M\.A\.|B\.Com|M\.Com|B\.B\.A\.|M\.B\.A\.)\b',
                            r'\b(Bachelor|Master|Doctorate|PhD)\b',
                        ]

                        for pattern in degree_patterns:
                            degrees = re.findall(pattern, edu_line, re.IGNORECASE)
                            if degrees:
                                edu_entry['degree'] = degrees[0]
                                break

                        if edu_entry:
                            education.append(edu_entry)

                break

        return education

    def _extract_experience(self, text: str) -> List[Dict[str, Any]]:
        """Extract work experience"""
        experience = []

        # Experience keywords
        exp_keywords = ['experience', 'work experience', 'employment', 'career']

        lines = text.split('\n')
        exp_section_found = False

        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in exp_keywords):
                exp_section_found = True
                # Look for company names and positions
                for j in range(i + 1, min(i + 10, len(lines))):
                    exp_line = lines[j].strip()
                    if exp_line and len(exp_line) > 3:
                        # Look for company indicators
                        if any(char in exp_line for char in ['Ltd', 'Inc', 'Corp', 'LLC']):
                            exp_entry = {'company': exp_line}
                            experience.append(exp_entry)

                break

        return experience

    def _extract_skills(self, text: str) -> List[str]:
        """Extract technical and soft skills"""
        skills = []

        # Common technical skills
        technical_skills = [
            'python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'swift',
            'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask',
            'mysql', 'postgresql', 'mongodb', 'redis', 'docker', 'kubernetes',
            'aws', 'azure', 'gcp', 'linux', 'git', 'jenkins', 'ci/cd',
            'machine learning', 'ai', 'data science', 'tensorflow', 'pytorch',
            'html', 'css', 'sass', 'bootstrap', 'tailwind', 'rest api', 'graphql'
        ]

        # Find skills section
        skills_section = re.search(
            r'(?:skills|technologies|technical skills|expertise)(.*?)(?:\n\n|\n\s*\n)',
            text,
            re.IGNORECASE | re.DOTALL
        )

        if skills_section:
            skills_text = skills_section.group(1)
        else:
            # If no skills section, look for skills in the entire text
            skills_text = text

        # Extract skills using pattern matching
        for skill in technical_skills:
            if skill.lower() in skills_text.lower():
                if skill not in skills:
                    skills.append(skill)

        # Also look for other potential skills (capitalized words in skills area)
        words = re.findall(r'\b[A-Z][a-z]+\b', skills_text)
        for word in words:
            if len(word) > 2 and word.lower() not in [s.lower() for s in skills]:
                # Check if it's a common skill
                if any(tech.lower() in word.lower() for tech in technical_skills):
                    skills.append(word)

        return list(set(skills))  # Remove duplicates

    def _extract_projects(self, text: str) -> List[Dict[str, Any]]:
        """Extract project information"""
        projects = []

        # Project keywords
        project_keywords = ['projects', 'portfolio', 'case studies']

        lines = text.split('\n')
        project_section_found = False

        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in project_keywords):
                project_section_found = True
                # Look for project descriptions
                for j in range(i + 1, min(i + 8, len(lines))):
                    project_line = lines[j].strip()
                    if project_line and len(project_line) > 10:
                        projects.append({'description': project_line})

                break

        return projects

    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certifications"""
        certifications = []

        # Certification keywords
        cert_keywords = ['certification', 'certified', 'license', 'aws certified', 'google certified']

        lines = text.split('\n')
        cert_section_found = False

        for line in lines:
            if any(keyword in line.lower() for keyword in cert_keywords):
                cert_section_found = True
                # Extract certification names
                cert_names = re.findall(r'\b([A-Z][a-zA-Z\s]+(?:Certified|Certification|License))\b', line)
                certifications.extend(cert_names)

        return certifications

    def _extract_summary(self, text: str) -> str:
        """Extract professional summary or objective"""
        # Look for summary/objective section
        summary_patterns = [
            r'(?:summary|objective|profile|about me)(.*?)(?:\n\n|\n\s*\n)',
            r'(?:professional summary|career objective)(.*?)(?:\n\n|\n\s*\n)'
        ]

        for pattern in summary_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()

        # If no explicit summary, return first paragraph
        first_para = text.split('\n\n')[0] if text else ""
        return first_para.strip()[:200] + "..." if len(first_para) > 200 else first_para


def main():
    """Test the resume parser"""
    parser = ResumeParser()

    # Test with sample file
    test_file = "sample_resume.pdf"  # Update with actual path

    if os.path.exists(test_file):
        try:
            result = parser.parse_resume(test_file)
            print("Parsed Resume:")
            for key, value in result.items():
                print(f"\n{key.title()}:")
                if isinstance(value, list):
                    for item in value:
                        print(f"  - {item}")
                elif isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        print(f"  {sub_key}: {sub_value}")
                else:
                    print(f"  {value}")
        except Exception as e:
            print(f"Error parsing resume: {e}")
    else:
        print("Test file not found")


if __name__ == "__main__":
    main()
