from flask import Flask, request, jsonify
from job_service import JobService
from config import Config
import os
import logging
import sys
import threading

# Configure logging to show in Docker logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
job_service = JobService()

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/webhook/n8n', methods=['POST'])
def n8n_webhook():
    """Webhook endpoint for n8n to trigger job search"""
    try:
        logger.info("Webhook called - starting job search in background")
        
        # Optional: Verify webhook secret
        # if Config.N8N_WEBHOOK_SECRET:
        #     secret = request.headers.get('X-Webhook-Secret')
        #     if secret != Config.N8N_WEBHOOK_SECRET:
        #         return jsonify({'error': 'Unauthorized'}), 401
        
        # Run job search in background thread to avoid n8n timeout
        def run_job_search():
            try:
                logger.info("Background job search started")
                success = job_service.send_daily_jobs()
                if success:
                    stats = job_service.get_stats()
                    logger.info(f"Background job search completed. Stats: {stats}")
                else:
                    logger.warning("Background job search returned False")
            except Exception as e:
                logger.error(f"Error in background job search: {e}", exc_info=True)
        
        # Start background thread
        thread = threading.Thread(target=run_job_search, daemon=True)
        thread.start()
        
        # Return immediately to avoid n8n timeout
        return jsonify({
            'status': 'accepted',
            'message': 'Job search started in background'
        }), 202  # 202 Accepted - request accepted but processing asynchronously
            
    except Exception as e:
        logger.error(f"Error in webhook: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/jobs/search', methods=['POST'])
def manual_search():
    """Manually trigger job search (for testing)"""
    try:
        result = job_service.search_and_save_jobs()
        return jsonify({
            'status': 'success',
            'result': result
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/stats', methods=['GET'])
def stats():
    """Get job statistics"""
    try:
        stats = job_service.get_stats()
        return jsonify({
            'status': 'success',
            'stats': stats
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/test/telegram', methods=['GET'])
def test_telegram():
    """Test endpoint to send a test message to Telegram"""
    try:
        test_message = "🧪 *Test Message*\n\nIf you see this, your Telegram bot is working correctly! ✅"
        success = job_service.telegram_bot.send_notification_sync(test_message)
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Test message sent to Telegram',
                'chat_id': Config.TELEGRAM_CHAT_ID
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to send test message'
            }), 500
    except Exception as e:
        logger.error(f"Error in test_telegram: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/debug/search', methods=['GET'])
def debug_search():
    """Debug endpoint to see what jobs are being found (without saving to DB)"""
    try:
        # Search without saving to see what's being found
        all_jobs = job_service.job_search.search_all_sources(Config.SERPAPI_KEY)
        
        # Filter jobs
        filtered_jobs = job_service.job_filter.filter_jobs(all_jobs)
        
        # Get recent jobs (last 72 hours)
        today_jobs = job_service.job_filter.get_jobs_from_today(filtered_jobs, days_back=0)
        
        # Format for display
        jobs_info = []
        for job in today_jobs[:20]:  # Limit to 20 for display
            jobs_info.append({
                'title': job.get('title', ''),
                'company': job.get('company', ''),
                'url': job.get('url', ''),
                'posted_date': str(job.get('posted_date', 'No date')),
                'source': job.get('source', ''),
                'description_preview': job.get('description', '')[:100]
            })
        
        return jsonify({
            'status': 'success',
            'total_found': len(all_jobs),
            'filtered': len(filtered_jobs),
            'recent': len(today_jobs),
            'jobs': jobs_info
        }), 200
    except Exception as e:
        import traceback
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500

if __name__ == '__main__':
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please check your .env file")
        exit(1)
    
    # Configure Flask logging
    logging.getLogger('werkzeug').setLevel(logging.INFO)
    
    port = int(os.getenv('PORT', Config.PORT))
    logger.info(f"Starting JobBot server on port {port}")
    logger.info(f"Search keywords: {Config.SEARCH_KEYWORDS}")
    logger.info(f"Search locations: {Config.SEARCH_LOCATIONS}")
    
    app.run(host='0.0.0.0', port=port, debug=False)

