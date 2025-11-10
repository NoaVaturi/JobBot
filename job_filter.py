import re
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class JobFilter:
    def __init__(self, experience_levels: List[str], keywords: List[str]):
        self.experience_levels = [level.lower() for level in experience_levels]
        self.keywords = [keyword.lower() for keyword in keywords]
    
    def filter_job(self, job: Dict) -> bool:
        """Check if a job matches all filtering criteria"""
        # Combine title, description, and company for filtering
        text_to_search = ' '.join([
            job.get('title', ''),
            job.get('description', ''),
            job.get('company', '')
        ]).lower()
        
        # Check experience level
        experience_match = self._matches_experience(text_to_search)
        if experience_match is False:
            # Explicitly excluded (senior/4+ years)
            logger.debug(f"Job '{job.get('title', '')[:50]}' filtered out: experience requirement not met (senior/4+ years)")
            return False
        # If experience_match is None (ambiguous/not found), don't block it
        # If experience_match is True (junior/0-3), continue to keyword check
        
        # Check keywords
        keyword_match = self._matches_keywords(text_to_search)
        if not keyword_match:
            logger.debug(f"Job '{job.get('title', '')[:50]}' filtered out: insufficient keywords match")
            return False
        
        return True
    
    def _matches_experience(self, text: str) -> Optional[bool]:
        """Check if job text matches experience level requirements (0-3 years, junior, entry level)"""
        # Check for experience level indicators in English
        experience_patterns = [
            r'\b(junior|jr\.?|entry\s*level|associate|intern|internship)\b',
            r'\b(0\s*-\s*[0-3])\s*years?\b',
            r'\b([0-3])\s*-\s*([0-3])\s*years?\b',  # e.g., "1-2 years", "0-3 years"
            r'\b([0-3])\s*years?\b',  # e.g., "1 year", "2 years", "3 years"
            r'\b([0-3])\s*\+\s*years?\b'  # e.g., "2+ years" but max 3
        ]
        
        # Check for experience in Hebrew (שנים = years)
        hebrew_patterns = [
            r'\b(0\s*-\s*[0-3])\s*שנים\b',  # "0-3 שנים"
            r'\b([0-3])\s*-\s*([0-3])\s*שנים\b',  # "1-2 שנים", "0-3 שנים"
            r'\b([0-3])\s*שנים\b',  # "1 שנים", "2 שנים"
            r'\b(ג\'וניור|ג\'וניורית|זוטר|זוטרה|בוגר|בוגרת|מתחיל|מתחילה)\b',  # Hebrew: junior, entry level
        ]
        
        # Check English patterns
        for pattern in experience_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Verify the number is within 0-3 range
                numbers = re.findall(r'\d+', match.group(0))
                if numbers:
                    max_years = max(int(n) for n in numbers if n.isdigit())
                    if max_years <= 3:
                        return True
        
        # Check Hebrew patterns
        for pattern in hebrew_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Verify the number is within 0-3 range
                numbers = re.findall(r'\d+', match.group(0))
                if numbers:
                    max_years = max(int(n) for n in numbers if n.isdigit())
                    if max_years <= 3:
                        return True
                else:
                    # Hebrew keywords for junior/entry level
                    return True
        
        # Check if any experience level keyword is in the text
        for level in self.experience_levels:
            if level.lower() in text.lower():
                return True
        
        # Check for explicit exclusion of higher experience (e.g., "לא נדרש ניסיון" = no experience required)
        no_experience_patterns = [
            r'\b(no\s*experience|לא\s*נדרש\s*ניסיון|ללא\s*ניסיון)\b',
            r'\b(entry\s*level|מתחיל)\b'
        ]
        for pattern in no_experience_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # Check for explicit senior/4+ years requirements (exclude these)
        senior_patterns = [
            r'\b(senior|sr\.?|lead|principal|architect|מנהל|מנהלת|מוביל|מובילה)\b',
            r'\b([4-9]|\d{2,})\s*(?:\+)?\s*(?:years?|yrs?|שנים)\b',  # 4+ years, 5 years, etc.
            r'\b([4-9]|\d{2,})\s*-\s*\d+\s*(?:years?|yrs?|שנים)\b',  # 4-5 years, 5-7 years, etc.
        ]
        for pattern in senior_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # For senior keywords, exclude immediately
                if re.search(r'\b(senior|sr\.?|lead|principal|architect|מנהל|מנהלת|מוביל|מובילה)\b', match.group(0), re.IGNORECASE):
                    return False  # Explicitly exclude senior positions
                # For year patterns, check the numbers
                year_numbers = re.findall(r'(\d+)', match.group(0))
                if year_numbers:
                    min_years = min(int(n) for n in year_numbers if n.isdigit())
                    if min_years >= 4:
                        return False  # Explicitly exclude senior/4+ years
        
        # Check if experience requirements are mentioned at all
        has_experience_mention = re.search(r'\d+\s*(year|yr|שנים)', text, re.IGNORECASE)
        if has_experience_mention:
            # Extract all year numbers
            year_numbers = re.findall(r'(\d+)\s*(?:year|yr|שנים)', text, re.IGNORECASE)
            if year_numbers:
                max_years_mentioned = max(int(n) for n in year_numbers if n.isdigit())
                if max_years_mentioned > 3:
                    return False  # Explicitly exclude jobs requiring more than 3 years
        
        # If no experience mentioned or ambiguous, return None (don't block it)
        return None
    
    def _matches_keywords(self, text: str) -> bool:
        """Check if job text contains at least some of the required keywords"""
        matched_keywords = 0
        min_keywords_required = 1
        matched_list = []
        
        for keyword in self.keywords:
            # Handle special cases
            keyword_pattern = self._get_keyword_pattern(keyword)
            if re.search(keyword_pattern, text, re.IGNORECASE):
                matched_keywords += 1
                matched_list.append(keyword)
        
        if matched_keywords >= min_keywords_required:
            return True
        else:
            # Debug: show which keywords matched and which didn't
            if matched_keywords > 0:
                logger.debug(f"  Only {matched_keywords} keyword(s) matched: {matched_list} (need {min_keywords_required})")
            return False
    
    def _get_keyword_pattern(self, keyword: str) -> str:
        """Get regex pattern for a keyword, handling special cases"""
        keyword = keyword.strip().lower()
        
        # Handle special cases
        if keyword == 'ci/cd':
            return r'\b(ci/cd|ci\s*/\s*cd|continuous\s*integration|continuous\s*deployment)\b'
        elif keyword == 'github actions':
            return r'\b(github\s*actions|gh\s*actions)\b'
        elif keyword == 'gitops':
            return r'\b(gitops|git\s*ops)\b'
        elif keyword == 'devops':
            return r'\b(devops|dev\s*ops)\b'
        elif keyword == 'devsecops' or keyword == 'dev sec ops':
            return r'\b(devsecops|dev\s*sec\s*ops|dev\s*security\s*ops)\b'
        else:
            # Escape special regex characters and create word boundary pattern
            escaped = re.escape(keyword)
            return rf'\b{escaped}\b'
    
    def filter_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Filter a list of jobs"""
        filtered_jobs = []
        for job in jobs:
            if self.filter_job(job):
                filtered_jobs.append(job)
        return filtered_jobs
    
    def get_jobs_from_today(self, jobs: List[Dict], days_back: int = 0) -> List[Dict]:
        """Filter jobs posted in the last 72 hours (rolling window)"""
        now = datetime.utcnow()
        # Calculate cutoff time: 72 hours ago (3 days)
        # If days_back is provided, use that instead
        if days_back > 0:
            cutoff_time = now - timedelta(days=days_back)
        else:
            cutoff_time = now - timedelta(hours=72)
        
        recent_jobs = []
        jobs_with_dates = 0
        jobs_without_dates = 0
        jobs_in_last_24h = 0
        jobs_older_than_24h = 0
        
        for job in jobs:
            posted_date = job.get('posted_date')
            if posted_date:
                jobs_with_dates += 1
                job_datetime = None
                if isinstance(posted_date, datetime):
                    job_datetime = posted_date
                elif isinstance(posted_date, str):
                    # Try to parse string date
                    try:
                        from dateutil import parser
                        job_datetime = parser.parse(posted_date)
                    except:
                        pass
                
                if job_datetime:
                    # Check if job was posted within the last 24 hours
                    time_diff = now - job_datetime
                    hours_ago = time_diff.total_seconds() / 3600
                    
                    if job_datetime >= cutoff_time:
                        # Job was posted within last 24 hours - include it
                        jobs_in_last_24h += 1
                        recent_jobs.append(job)
                    elif days_back > 0:
                        # If days_back > 0, include jobs from the last N days
                        cutoff_date = now - timedelta(days=days_back)
                        if job_datetime >= cutoff_date:
                            recent_jobs.append(job)
                        else:
                            jobs_older_than_24h += 1
                    else:
                        # Job is older than 72 hours - exclude it
                        jobs_older_than_24h += 1
                        logger.debug(f"Excluding job '{job.get('title', '')[:50]}' - posted {hours_ago:.1f} hours ago (older than 72h)")
                else:
                    # Could not parse datetime, but we have a posted_date value
                    # Be lenient and include it (might be a parsing issue)
                    logger.info(f"Including job '{job.get('title', '')[:50]}' - could not parse date: {posted_date}")
                    recent_jobs.append(job)
            else:
                # If no date available, be lenient and include it
                # This is important because web scraping might not always parse dates correctly
                # We'll include jobs without dates to avoid missing recent jobs
                jobs_without_dates += 1
                source = job.get('source', '')
                logger.info(f"Including job '{job.get('title', '')[:50]}' from {source} - no date available (assuming recent)")
                recent_jobs.append(job)
        
        logger.info(f"Date filtering (last 72h): {jobs_with_dates} with dates, {jobs_without_dates} without dates, {jobs_in_last_24h} in last 72h, {jobs_older_than_24h} older than 72h")
        logger.info(f"Total jobs after date filtering: {len(recent_jobs)}")
        return recent_jobs

