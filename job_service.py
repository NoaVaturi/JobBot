from datetime import datetime, timedelta
from typing import List, Dict
from database import Database, Job
from job_search import JobSearch
from job_filter import JobFilter
from telegram_bot import TelegramJobBot
from config import Config
import logging
import sys

logger = logging.getLogger(__name__)

class JobService:
    def __init__(self):
        self.db = Database(Config.DATABASE_URL)
        self.job_search = JobSearch(Config.SEARCH_KEYWORDS, Config.SEARCH_LOCATIONS)
        self.job_filter = JobFilter(Config.EXPERIENCE_LEVELS, Config.JOB_KEYWORDS)
        self.telegram_bot = TelegramJobBot(Config.TELEGRAM_BOT_TOKEN, Config.TELEGRAM_CHAT_ID)
    
    def search_and_save_jobs(self) -> Dict:
        """Search for jobs, filter them, and save to database"""
        import sys
        sys.stdout.flush()  # Force output to be flushed
        
        logger.info("=" * 60)
        logger.info("Starting job search...")
        logger.info(f"Search keywords: {Config.SEARCH_KEYWORDS}")
        logger.info(f"Search locations: {Config.SEARCH_LOCATIONS}")
        if Config.SERPAPI_KEY:
            logger.info("✅ SerpAPI key found - Google Jobs search enabled")
        else:
            logger.info("ℹ️  SerpAPI key not set - only searching Drushim and GotFriends")
        logger.info("=" * 60)
        
        # Search all sources
        all_jobs = self.job_search.search_all_sources(Config.SERPAPI_KEY)
        logger.info(f"Found {len(all_jobs)} jobs from all sources")
        
        # Debug: Print sample jobs
        if all_jobs:
            logger.info(f"Sample job titles: {[job.get('title', '')[:50] for job in all_jobs[:5]]}")
        else:
            logger.warning("WARNING: No jobs found from any source!")
        
        # Filter jobs by keywords and experience
        filtered_jobs = self.job_filter.filter_jobs(all_jobs)
        logger.info(f"Filtered to {len(filtered_jobs)} jobs matching criteria (keywords + experience)")
        
        # Debug: Print why jobs were filtered out
        if len(filtered_jobs) < len(all_jobs):
            excluded = len(all_jobs) - len(filtered_jobs)
            logger.info(f"Excluded {excluded} jobs that didn't match keywords or experience requirements")
            # Log sample of excluded jobs for debugging
            excluded_samples = [job for job in all_jobs if job not in filtered_jobs][:3]
            for job in excluded_samples:
                logger.debug(f"Excluded job sample: '{job.get('title', '')[:50]}' - URL: {job.get('url', '')[:60]}")
        
        # Get jobs from the last 72 hours (rolling window)
        # Using days_back=0 to use default 72h window
        today_jobs = self.job_filter.get_jobs_from_today(filtered_jobs, days_back=0)
        logger.info(f"Found {len(today_jobs)} jobs posted in the last 72 hours")
        
        # Debug: Print job details
        if today_jobs:
            logger.info(f"\n✅ Jobs that passed all filters (will be sent to Telegram):")
            for i, job in enumerate(today_jobs[:10], 1):  # Show up to 10 jobs
                posted = job.get('posted_date', 'No date')
                if isinstance(posted, datetime):
                    hours_ago = (datetime.utcnow() - posted).total_seconds() / 3600
                    posted_str = f"{posted.date()} ({hours_ago:.1f} hours ago)"
                else:
                    posted_str = str(posted)
                logger.info(f"  {i}. '{job.get('title', '')[:60]}'")
                logger.info(f"     Company: {job.get('company', 'Unknown')}")
                logger.info(f"     Posted: {posted_str}")
                logger.info(f"     URL: {job.get('url', '')[:80]}")
        else:
            logger.warning("⚠️  WARNING: No jobs passed the date filter (last 72 hours)!")
            if filtered_jobs:
                logger.warning(f"  But {len(filtered_jobs)} jobs passed keyword/experience filters")
                logger.warning(f"  Sample filtered jobs (older than 72 hours):")
                for i, job in enumerate(filtered_jobs[:5], 1):
                    posted = job.get('posted_date', 'No date')
                    if isinstance(posted, datetime):
                        hours_ago = (datetime.utcnow() - posted).total_seconds() / 3600
                        if hours_ago < 72:
                            posted_str = f"{posted.date()} ({hours_ago:.1f} hours ago - should be included!)"
                        else:
                            days_ago = hours_ago / 24
                            posted_str = f"{posted.date()} ({days_ago:.1f} days ago)"
                    else:
                        posted_str = str(posted)
                    logger.warning(f"    {i}. '{job.get('title', '')[:50]}' - Posted: {posted_str}")
        
        # Save new jobs to database
        new_jobs = []
        duplicate_count = 0
        for job in today_jobs:
            saved_job = self.db.add_job(job)
            if saved_job:
                # Access all attributes immediately while the job object is still valid
                # (even though it's expunged, the attributes are already loaded)
                new_jobs.append({
                    'title': job.get('title', ''),
                    'company': job.get('company', ''),
                    'location': job.get('location', ''),
                    'url': job.get('url', ''),
                    'description': job.get('description', ''),
                    'source': job.get('source', 'unknown')
                })
            else:
                duplicate_count += 1
        
        if duplicate_count > 0:
            logger.info(f"Skipped {duplicate_count} duplicate jobs (already in database)")
        logger.info(f"Added {len(new_jobs)} new jobs to database")
        logger.info("=" * 60)
        
        return {
            'total_found': len(all_jobs),
            'filtered': len(filtered_jobs),
            'today': len(today_jobs),
            'new': len(new_jobs),
            'jobs': new_jobs
        }
    
    def send_daily_jobs(self) -> bool:
        """Search for jobs and send new ones to Telegram, or send today's jobs if no new ones"""
        try:
            # Search and save jobs
            result = self.search_and_save_jobs()
            logger.info(f"Job search result: {result['new']} new jobs, {result['today']} jobs from last 72h, {result['filtered']} passed filters")
            
            # Send jobs to Telegram
            if result['new'] > 0:
                logger.info(f"Sending {result['new']} new job(s) to Telegram")
                success = self.telegram_bot.send_jobs_sync(result['jobs'])
                if success:
                    logger.info("Successfully sent jobs to Telegram, marking as sent in database")
                    # Mark jobs as sent
                    for job in result['jobs']:
                        job_id = Job.generate_job_id(
                            job['url'],
                            job['title'],
                            job['company']
                        )
                        self.db.mark_job_as_sent(job_id)
                    logger.info("All jobs marked as sent in database")
                else:
                    logger.error("Failed to send jobs to Telegram")
                return success
            elif result['today'] > 0:
                # No new jobs, but there are jobs from today - send those instead
                logger.info(f"No new jobs, but found {result['today']} jobs from last 72h. Sending today's jobs from database.")
                today_jobs = self.db.get_jobs_from_last_days(days=3, limit=10)  # Get last 3 days (72h)
                if today_jobs:
                    logger.info(f"Sending {len(today_jobs)} job(s) from last 72h to Telegram")
                    success = self.telegram_bot.send_jobs_sync(today_jobs)
                    if success:
                        logger.info("Successfully sent today's jobs to Telegram")
                    else:
                        logger.error("Failed to send today's jobs to Telegram")
                    return success
                else:
                    # Fall through to "no jobs" message
                    logger.info("No jobs found in database from last 72h")
            else:
                # No jobs at all
                logger.info("No jobs found from last 72h")
            
            # No new jobs and no today's jobs, send notification
            logger.info("Sending 'no new jobs' message to Telegram")
            success = self.telegram_bot.send_no_jobs_sync()
            if success:
                logger.info("Successfully sent 'no new jobs' message to Telegram")
            else:
                logger.error("Failed to send 'no new jobs' message to Telegram")
            return success
        except Exception as e:
            logger.error(f"Error in send_daily_jobs: {e}", exc_info=True)
            return False
    
    def get_stats(self) -> Dict:
        """Get statistics about jobs"""
        today_count = self.db.get_today_jobs_count()
        return {
            'jobs_today': today_count
        }

