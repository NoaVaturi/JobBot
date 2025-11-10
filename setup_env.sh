#!/bin/bash
# Setup script for JobBot

echo "Setting up JobBot..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOF
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# SerpAPI Configuration (optional - for enhanced job search)
SERPAPI_KEY=your_serpapi_key_here

# Database Configuration
DATABASE_URL=sqlite:///jobs.db

# Job Search Configuration
SEARCH_KEYWORDS=devops engineer,sre,cloud engineer
EXPERIENCE_LEVELS=junior,entry level,associate,0-3 years
JOB_KEYWORDS=jenkins,aws,eks,github,github actions,git,docker,argocd,gitops,ci/cd,devops,pipeline,linux,python,bash
SEARCH_LOCATIONS=Israel,Tel Aviv,Jerusalem,Haifa,Remote

# n8n Webhook Configuration
N8N_WEBHOOK_SECRET=your_secret_key_here
PORT=8000
EOF
    echo ".env file created! Please update it with your credentials."
else
    echo ".env file already exists."
fi

echo "Setup complete!"
echo "Next steps:"
echo "1. Update .env file with your Telegram bot token and chat ID"
echo "2. (Optional) Add SerpAPI key for enhanced job search"
echo "3. Run: python main.py (for manual testing)"
echo "4. Run: python app.py (to start the web server for n8n)"

