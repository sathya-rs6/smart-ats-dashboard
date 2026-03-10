"""
Helper utilities for Resume Analyzer RAG
"""

import os
import hashlib
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import re
from datetime import datetime

logger = logging.getLogger(__name__)


def generate_file_hash(file_path: str) -> str:
    """Generate MD5 hash of a file"""
    try:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"Error generating file hash: {e}")
        return ""


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to remove dangerous characters"""
    # Remove any characters that aren't alphanumeric, dash, underscore, or dot
    filename = re.sub(r'[^\w\-.]', '_', filename)
    # Remove multiple consecutive underscores
    filename = re.sub(r'_+', '_', filename)
    return filename


def get_file_extension(filename: str) -> str:
    """Get file extension in lowercase"""
    return Path(filename).suffix.lower()


def is_valid_file_type(filename: str, allowed_extensions: List[str]) -> bool:
    """Check if file type is valid"""
    ext = get_file_extension(filename)
    # Remove leading dot if present in allowed_extensions
    allowed = [e if e.startswith('.') else f'.{e}' for e in allowed_extensions]
    return ext in allowed


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def extract_years_of_experience(text: str) -> float:
    """Extract years of experience from text using regex patterns"""
    patterns = [
        r'(\d+\.?\d*)\s*(?:years?|yrs?)\s+(?:of\s+)?experience',
        r'experience\s+(?:of\s+)?(\d+\.?\d*)\s*(?:years?|yrs?)',
        r'(\d+\.?\d*)\+?\s*(?:years?|yrs?)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue
    
    return 0.0


def normalize_skill_name(skill: str) -> str:
    """Normalize skill name for comparison"""
    # Convert to lowercase
    skill = skill.lower().strip()
    
    # Remove version numbers
    skill = re.sub(r'\s*\d+(\.\d+)*$', '', skill)
    
    # Remove special characters except dots and hyphens
    skill = re.sub(r'[^\w\s\-.]', '', skill)
    
    # Normalize common variations
    skill_mappings = {
        'js': 'javascript',
        'ts': 'typescript',
        'py': 'python',
        'nodejs': 'node.js',
        'reactjs': 'react',
        'vuejs': 'vue',
        'mysql': 'sql',
        'postgresql': 'sql',
        'aws': 'amazon web services',
        'gcp': 'google cloud platform',
    }
    
    return skill_mappings.get(skill, skill)


def calculate_match_percentage(matched: int, total: int) -> float:
    """Calculate match percentage"""
    if total == 0:
        return 100.0
    return (matched / total) * 100


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime object to string"""
    try:
        return dt.strftime(format_str)
    except Exception as e:
        logger.error(f"Error formatting datetime: {e}")
        return str(dt)


def parse_comma_separated_list(text: str) -> List[str]:
    """Parse comma-separated string into list"""
    if not text:
        return []
    return [item.strip() for item in text.split(',') if item.strip()]


def deduplicate_list(items: List[Any]) -> List[Any]:
    """Remove duplicates from list while preserving order"""
    seen = set()
    result = []
    for item in items:
        # Convert to string for comparison if not hashable
        try:
            key = item
        except TypeError:
            key = str(item)
        
        if key not in seen:
            seen.add(key)
            result.append(item)
    
    return result


def clean_text(text: str) -> str:
    """Clean and normalize text"""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep important punctuation
    text = re.sub(r'[^\w\s.,!?;:()\-]', '', text)
    return text.strip()


def extract_email_addresses(text: str) -> List[str]:
    """Extract email addresses from text"""
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(pattern, text)


def extract_phone_numbers(text: str) -> List[str]:
    """Extract phone numbers from text"""
    patterns = [
        r'\+?\d{1,3}?[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}',
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
    ]
    
    phone_numbers = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        phone_numbers.extend(matches)
    
    return list(set(phone_numbers))


def create_directory_if_not_exists(directory: str) -> bool:
    """Create directory if it doesn't exist"""
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {directory}: {e}")
        return False


def get_relative_path(full_path: str, base_path: str) -> str:
    """Get relative path from base path"""
    try:
        return str(Path(full_path).relative_to(base_path))
    except ValueError:
        return full_path


def validate_api_key(api_key: Optional[str], provider: str) -> bool:
    """Validate API key format"""
    if not api_key:
        logger.warning(f"No API key provided for {provider}")
        return False
    
    # Basic validation - check if it's not empty and has minimum length
    if len(api_key.strip()) < 10:
        logger.warning(f"Invalid API key format for {provider}")
        return False
    
    return True


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries"""
    result = {}
    for d in dicts:
        result.update(d)
    return result


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, return default if denominator is zero"""
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except Exception:
        return default
