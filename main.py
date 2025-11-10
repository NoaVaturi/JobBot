#!/usr/bin/env python3
"""
Main script to run the job bot
Can be used for manual testing or scheduled execution
"""
import sys
from job_service import JobService
from config import Config

def main():
    """Main function to run job search and send to Telegram"""
    try:
        # Validate configuration
        Config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please check your .env file")
        sys.exit(1)
    
    # Create job service and run
    job_service = JobService()
    success = job_service.send_daily_jobs()
    
    if success:
        print("Job search completed successfully!")
        sys.exit(0)
    else:
        print("Job search failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()

