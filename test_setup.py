#!/usr/bin/env python3
"""
Test script to verify JobBot setup
"""
import sys

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    try:
        from config import Config
        from database import Database, Job
        from job_search import JobSearch
        from job_filter import JobFilter
        from telegram_bot import TelegramJobBot
        from job_service import JobService
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_config():
    """Test configuration"""
    print("\nTesting configuration...")
    try:
        from config import Config
        # Don't validate, just check if config loads
        print(f"✓ Config loaded")
        print(f"  - Search keywords: {Config.SEARCH_KEYWORDS}")
        print(f"  - Experience levels: {Config.EXPERIENCE_LEVELS}")
        print(f"  - Job keywords: {len(Config.JOB_KEYWORDS)} keywords")
        print(f"  - Locations: {Config.SEARCH_LOCATIONS}")
        
        # Check if required env vars are set (but don't fail if they're not)
        if Config.TELEGRAM_BOT_TOKEN and Config.TELEGRAM_BOT_TOKEN != 'your_telegram_bot_token_here':
            print("  - Telegram bot token: ✓ Set")
        else:
            print("  - Telegram bot token: ✗ Not set (update .env file)")
        
        if Config.TELEGRAM_CHAT_ID and Config.TELEGRAM_CHAT_ID != 'your_telegram_chat_id_here':
            print("  - Telegram chat ID: ✓ Set")
        else:
            print("  - Telegram chat ID: ✗ Not set (update .env file)")
        
        if Config.SERPAPI_KEY:
            print("  - SerpAPI key: ✓ Set (optional)")
        else:
            print("  - SerpAPI key: ✗ Not set (optional, but recommended)")
        
        return True
    except Exception as e:
        print(f"✗ Config error: {e}")
        return False

def test_database():
    """Test database setup"""
    print("\nTesting database...")
    try:
        from database import Database, Job
        from config import Config
        
        db = Database(Config.DATABASE_URL)
        print("✓ Database connection successful")
        
        # Test job_id generation
        job_id = Job.generate_job_id("https://example.com/job", "Test Job", "Test Company")
        print(f"✓ Job ID generation works: {job_id[:8]}...")
        
        return True
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False

def test_job_filter():
    """Test job filtering"""
    print("\nTesting job filter...")
    try:
        from job_filter import JobFilter
        from config import Config
        
        job_filter = JobFilter(Config.EXPERIENCE_LEVELS, Config.JOB_KEYWORDS)
        
        # Test job that should match
        test_job = {
            'title': 'Junior DevOps Engineer',
            'company': 'Tech Corp',
            'description': 'Looking for a junior DevOps engineer with AWS, Docker, and Jenkins experience. 0-2 years required.',
            'location': 'Remote'
        }
        
        matches = job_filter.filter_job(test_job)
        print(f"✓ Job filter works: Test job matches = {matches}")
        
        return True
    except Exception as e:
        print(f"✗ Job filter error: {e}")
        return False

def main():
    """Run all tests"""
    print("JobBot Setup Test\n" + "=" * 50)
    
    tests = [
        test_imports,
        test_config,
        test_database,
        test_job_filter
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print(f"Tests passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("✓ All tests passed! Setup looks good.")
        print("\nNext steps:")
        print("1. Update .env file with your Telegram bot token and chat ID")
        print("2. (Optional) Add SerpAPI key for enhanced job search")
        print("3. Run: python main.py (for manual testing)")
        print("4. Run: python app.py (to start the web server for n8n)")
        return 0
    else:
        print("✗ Some tests failed. Please check the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())

