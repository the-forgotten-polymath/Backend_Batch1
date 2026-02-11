"""Configuration module for Placement Profile Enricher API."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""
    
    # Rate Limiting (requests per second)
    LEETCODE_RATE_LIMIT = float(os.getenv('LEETCODE_RATE_LIMIT', '0.8'))
    CODEFORCES_RATE_LIMIT = float(os.getenv('CODEFORCES_RATE_LIMIT', '1.0'))
    LINKEDIN_RATE_LIMIT = float(os.getenv('LINKEDIN_RATE_LIMIT', '0.5'))
    GITHUB_RATE_LIMIT = float(os.getenv('GITHUB_RATE_LIMIT', '0.8'))
    
    # Request Configuration
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '15'))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '2'))
    RETRY_BACKOFF_FACTOR = float(os.getenv('RETRY_BACKOFF_FACTOR', '2'))
    
    # File Upload Configuration
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '10'))
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
    ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'xlsx').split(','))
    
    # Selenium Configuration
    SELENIUM_ENABLED = os.getenv('SELENIUM_ENABLED', 'false').lower() == 'true'
    SELENIUM_HEADLESS = os.getenv('SELENIUM_HEADLESS', 'true').lower() == 'true'
    
    # Server Configuration
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '5000'))
    
    # Processing Configuration
    DEFAULT_DELAY_MS = int(os.getenv('DEFAULT_DELAY_MS', '1000'))
    MEMORY_THRESHOLD_MB = int(os.getenv('MEMORY_THRESHOLD_MB', '300'))
    
    # Directories
    UPLOAD_FOLDER = 'uploads'
    PHOTOS_FOLDER = 'photos'
    OUTPUT_FOLDER = 'output'
    
    # Expected Excel Columns (case-insensitive)
    EXPECTED_COLUMNS = [
        'rollno',
        'leetcodeurl',
        'codeforcesurl',
        'linkedinurl',
        'githuburl'
    ]
    
    # New Columns to Add
    NEW_COLUMNS = [
        'LC_Global_Contest_Rank',
        'CF_Rating',
        'Photos_Path',
        'GH_Commits_12mo',
        'GH_Public_Repos'
    ]
    
    # User Agent for Requests
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
