"""Validation utilities for file uploads and URLs."""
import os
import re
from urllib.parse import urlparse
from config import Config


def allowed_file(filename):
    """
    Check if file has an allowed extension.
    
    Args:
        filename: Name of the file
        
    Returns:
        True if file extension is allowed, False otherwise
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def validate_file_size(file_size):
    """
    Validate file size is within limits.
    
    Args:
        file_size: Size of file in bytes
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if file_size > Config.MAX_FILE_SIZE_BYTES:
        return False, f"File size exceeds {Config.MAX_FILE_SIZE_MB}MB limit"
    return True, None


def sanitize_url(url):
    """
    Sanitize and validate URL.
    
    Args:
        url: URL string to sanitize
        
    Returns:
        Sanitized URL or None if invalid
    """
    if not url or not isinstance(url, str):
        return None
    
    url = url.strip()
    
    # Check if empty or placeholder
    if not url or url.lower() in ['n/a', 'na', 'none', '-', '']:
        return None
    
    # Add https:// if no scheme
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return None
        return url
    except Exception:
        return None


def validate_platform_url(url, platform):
    """
    Validate URL belongs to expected platform.
    
    Args:
        url: URL to validate
        platform: Expected platform name
        
    Returns:
        True if URL is valid for platform, False otherwise
    """
    if not url:
        return False
    
    platform_domains = {
        'leetcode': ['leetcode.com'],
        'codeforces': ['codeforces.com'],
        'linkedin': ['linkedin.com'],
        'github': ['github.com']
    }
    
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace('www.', '')
        
        if platform.lower() in platform_domains:
            return any(d in domain for d in platform_domains[platform.lower()])
        
        return True
    except Exception:
        return False


def extract_username_from_url(url, platform):
    """
    Extract username from profile URL.
    
    Args:
        url: Profile URL
        platform: Platform name
        
    Returns:
        Username or None
    """
    if not url:
        return None
    
    try:
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        if platform.lower() == 'github':
            # GitHub: https://github.com/username
            parts = path.split('/')
            return parts[0] if parts else None
        
        elif platform.lower() == 'linkedin':
            # LinkedIn: https://linkedin.com/in/username
            if '/in/' in path:
                parts = path.split('/in/')
                if len(parts) > 1:
                    return parts[1].split('/')[0]
        
        elif platform.lower() == 'leetcode':
            # LeetCode: https://leetcode.com/username or /u/username
            parts = path.split('/')
            return parts[-1] if parts else None
        
        elif platform.lower() == 'codeforces':
            # Codeforces: https://codeforces.com/profile/username
            if '/profile/' in path:
                parts = path.split('/profile/')
                if len(parts) > 1:
                    return parts[1].split('/')[0]
        
        return None
    except Exception:
        return None


def normalize_column_name(name):
    """
    Normalize column name to lowercase without spaces.
    
    Args:
        name: Column name
        
    Returns:
        Normalized column name
    """
    if not name:
        return ''
    return str(name).lower().strip().replace(' ', '').replace('_', '')
