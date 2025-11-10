from sqlalchemy import create_engine, Column, String, DateTime, Integer, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import hashlib
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

class Job(Base):
    __tablename__ = 'jobs'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    company = Column(String)
    location = Column(String)
    url = Column(Text, nullable=False)
    description = Column(Text)
    source = Column(String)  # 'indeed', 'linkedin', 'glassdoor', etc.
    posted_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_to_telegram = Column(Boolean, default=False)
    sent_date = Column(DateTime)
    
    def __repr__(self):
        return f"<Job(id={self.job_id}, title={self.title}, company={self.company})>"
    
    @staticmethod
    def generate_job_id(url, title, company):
        """Generate a unique job ID from URL, title, and company"""
        unique_string = f"{url}{title}{company}".lower()
        return hashlib.md5(unique_string.encode()).hexdigest()

class Database:
    def __init__(self, database_url):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def get_session(self):
        return self.Session()
    
    def job_exists(self, job_id):
        """Check if a job already exists in the database"""
        session = self.get_session()
        try:
            job = session.query(Job).filter(Job.job_id == job_id).first()
            return job is not None
        finally:
            session.close()
    
    def add_job(self, job_data):
        """Add a new job to the database"""
        session = self.get_session()
        try:
            job_id = Job.generate_job_id(
                job_data['url'],
                job_data.get('title', ''),
                job_data.get('company', '')
            )
            
            if self.job_exists(job_id):
                return None
            
            job = Job(
                job_id=job_id,
                title=job_data.get('title', ''),
                company=job_data.get('company', ''),
                location=job_data.get('location', ''),
                url=job_data['url'],
                description=job_data.get('description', ''),
                source=job_data.get('source', 'unknown'),
                posted_date=job_data.get('posted_date')
            )
            
            session.add(job)
            session.commit()
            # Detach the job from the session before returning
            # This prevents "not bound to a Session" errors when accessing attributes later
            session.expunge(job)
            return job
        except Exception as e:
            session.rollback()
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error adding job: {e}", exc_info=True)
            return None
        finally:
            session.close()
    
    def get_unsent_jobs(self, date=None):
        """Get jobs that haven't been sent to Telegram"""
        session = self.get_session()
        try:
            query = session.query(Job).filter(Job.sent_to_telegram == False)
            
            if date:
                query = query.filter(Job.created_at >= date)
            
            return query.all()
        finally:
            session.close()
    
    def mark_job_as_sent(self, job_id):
        """Mark a job as sent to Telegram"""
        session = self.get_session()
        try:
            job = session.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.sent_to_telegram = True
                job.sent_date = datetime.utcnow()
                session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error marking job as sent: {e}")
        finally:
            session.close()
    
    def get_today_jobs_count(self):
        """Get count of jobs added today"""
        session = self.get_session()
        try:
            today = datetime.utcnow().date()
            count = session.query(Job).filter(
                Job.created_at >= datetime.combine(today, datetime.min.time())
            ).count()
            return count
        finally:
            session.close()
    
    def get_jobs_from_last_days(self, days: int = 1, limit: int = 10):
        """Get jobs from the last N days, formatted for Telegram"""
        session = self.get_session()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            jobs = session.query(Job).filter(
                Job.posted_date >= cutoff
            ).order_by(Job.posted_date.desc()).limit(limit).all()
            
            # Format jobs for Telegram - access all attributes while session is open
            formatted_jobs = []
            for job in jobs:
                # Access all attributes while session is still open
                title = job.title
                company = job.company
                location = job.location
                url = job.url
                description = job.description
                source = job.source
                
                # Detach from session before appending
                session.expunge(job)
                
                formatted_jobs.append({
                    'title': title,
                    'company': company or 'Unknown',
                    'location': location or 'Not specified',
                    'url': url,
                    'description': description or '',
                    'source': source or 'unknown'
                })
            return formatted_jobs
        except Exception as e:
            logger.error(f"Error getting jobs from last {days} days: {e}", exc_info=True)
            return []
        finally:
            session.close()

