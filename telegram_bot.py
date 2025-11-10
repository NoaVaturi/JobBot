from telegram import Bot
from telegram.constants import ParseMode
from typing import List, Dict
import asyncio
import logging

logger = logging.getLogger(__name__)

class TelegramJobBot:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.bot = Bot(token=bot_token)
    
    async def send_jobs(self, jobs: List[Dict]) -> bool:
        """Send a list of jobs to Telegram"""
        if not jobs:
            logger.info("No jobs to send, sending 'no new jobs' message")
            return await self.send_no_jobs_message()
        
        try:
            logger.info(f"Sending {len(jobs)} job(s) to Telegram chat {self.chat_id}")
            # Send header message
            header = f"🚀 *Found {len(jobs)} new job(s) today!*\n\n"
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=header,
                parse_mode=ParseMode.MARKDOWN
            )
            logger.info("Sent header message to Telegram")
            
            # Send each job
            for i, job in enumerate(jobs, 1):
                message = self._format_job_message(job, i, len(jobs))
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=False
                )
                logger.info(f"Sent job {i}/{len(jobs)} to Telegram: {job.get('title', '')[:50]}")
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)
            
            logger.info(f"Successfully sent all {len(jobs)} jobs to Telegram")
            return True
        except Exception as e:
            logger.error(f"Error sending jobs to Telegram: {e}", exc_info=True)
            return False
    
    async def send_no_jobs_message(self) -> bool:
        """Send a message when no new jobs are found"""
        try:
            logger.info(f"Sending 'no new jobs' message to Telegram chat {self.chat_id}")
            message = "📭 *No new jobs found today*\n\n" \
                     "I've checked all the job boards, but there are no new job postings " \
                     "matching your criteria today. I'll check again tomorrow! 🔍"
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            logger.info("Successfully sent 'no new jobs' message to Telegram")
            return True
        except Exception as e:
            logger.error(f"Error sending no jobs message to Telegram: {e}", exc_info=True)
            return False
    
    async def send_notification(self, message: str) -> bool:
        """Send a custom notification message"""
        try:
            logger.info(f"Sending notification to Telegram chat {self.chat_id}")
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            logger.info("Successfully sent notification to Telegram")
            return True
        except Exception as e:
            logger.error(f"Error sending notification to Telegram: {e}", exc_info=True)
            return False
    
    def _format_job_message(self, job: Dict, index: int, total: int) -> str:
        """Format a single job for Telegram message"""
        title = job.get('title', 'N/A')
        company = job.get('company', 'Unknown Company')
        location = job.get('location', 'Location not specified')
        url = job.get('url', '#')
        source = job.get('source', 'unknown').upper()
        
        # Truncate description if too long
        description = job.get('description', '')
        if len(description) > 200:
            description = description[:200] + "..."
        
        message = f"*{index}/{total} - {title}*\n\n"
        message += f"🏢 *Company:* {company}\n"
        message += f"📍 *Location:* {location}\n"
        message += f"🔗 *Source:* {source}\n"
        
        if description:
            message += f"\n📝 *Description:*\n{description}\n"
        
        message += f"\n🔗 [View Job]({url})"
        
        return message
    
    def send_jobs_sync(self, jobs: List[Dict]) -> bool:
        """Synchronous wrapper for send_jobs"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.send_jobs(jobs))
    
    def send_no_jobs_sync(self) -> bool:
        """Synchronous wrapper for send_no_jobs_message"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.send_no_jobs_message())
    
    def send_notification_sync(self, message: str) -> bool:
        """Synchronous wrapper for send_notification"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.send_notification(message))

