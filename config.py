import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    
    # SerpAPI Configuration (optional)
    SERPAPI_KEY = os.getenv('SERPAPI_KEY', '')
    
    # Database Configuration
    # Default to jobs.db in current directory, but can be overridden by DATABASE_URL env var
    # In Docker, DATABASE_URL should be set to sqlite:///data/jobs.db
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///jobs.db')
    
    # Job Search Configuration
    SEARCH_KEYWORDS = os.getenv('SEARCH_KEYWORDS', 'devops engineer,sre,cloud engineer,devsecops').split(',')
    EXPERIENCE_LEVELS = os.getenv('EXPERIENCE_LEVELS', 'junior,entry level,associate,0-3 years').split(',')
    JOB_KEYWORDS = os.getenv('JOB_KEYWORDS', 'jenkins,aws,eks,github,github actions,git,docker,argocd,gitops,ci/cd,devops,pipeline,linux,python,bash').split(',')
    
    # n8n Webhook Configuration
    N8N_WEBHOOK_SECRET = os.getenv('N8N_WEBHOOK_SECRET', '')
    PORT = int(os.getenv('PORT', 8000))
    
    # Job Search Locations
    # Default to Israel (includes on-site, hybrid, and remote jobs)
    # Searches major Israeli cities for on-site/hybrid jobs and "Remote" for remote positions
    # Can be overridden via SEARCH_LOCATIONS env var (comma-separated)
    _locations = os.getenv('SEARCH_LOCATIONS', 'Israel,Tel Aviv,Jerusalem,Haifa,Remote')
    SEARCH_LOCATIONS = [loc.strip() for loc in _locations.split(',')]
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present"""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        if not cls.TELEGRAM_CHAT_ID:
            raise ValueError("TELEGRAM_CHAT_ID is required")
        return True

