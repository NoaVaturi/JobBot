🤖 JobBot – Automated Job Search & Telegram Alerts

A smart, automated job-search assistant that continuously scans top job boards for DevOps positions, filters them intelligently, and delivers new listings straight to your Telegram chat — no manual searching required.


🏗️ Project Overview
This system automates the full job discovery pipeline — from scheduled search to personalized Telegram notifications — integrating multiple data sources, workflow automation, and message delivery services inside a Dockerized environment.
It demonstrates real-world event-driven automation, data filtering, and workflow orchestration using modern DevOps tools and APIs.

🧰 Tech Stack
Category	Technologies
Automation & Workflow	n8n · Cron Scheduling · Webhooks
Backend Service	Flask (Python)
Data Storage	SQLite (persistent via Docker volume)
Notifications	Telegram Bot API
Scraping & Aggregation	Drushim · GotFriends · (Optional) SerpAPI (Google Jobs)
Containerization	Docker · Docker Compose

📊 Architecture Diagram
Workflow:
+-----------+         +----------------+         +-----------------+         +----------------+
|  Scheduler|  --->   |   n8n Workflow |  --->   |  Flask API (/webhook) |  --->   |  Telegram Chat |
+-----------+         +----------------+         +-----------------+         +----------------+
                            |
                            v
                      Job Search Logic
                (Drushim · GotFriends · SerpAPI)
                            |
                            v
                       Keyword Filter
                            |
                            v
                         SQLite DB

🚀 Workflow Summary
Stage	Description
⏰ Schedule Trigger	n8n runs daily or weekly on a defined schedule
🔗 Webhook Call	Sends POST request to /webhook/n8n endpoint
🔍 Job Search	Flask searches Drushim + GotFriends (and SerpAPI if enabled)
🧠 Filter Jobs	Filters postings by experience level (0–3 years) and DevOps keywords
💾 Database Save	Stores new jobs in SQLite and skips duplicates
💬 Telegram Alert	Sends formatted job listings directly to Telegram chat
📭 No New Jobs	Sends a "No new jobs today" message if no matches are found

📁 Repository Breakdown
Folder / File	Description
app.py	Flask API and /webhook/n8n endpoint
job_service.py	Core service logic (search → filter → save → send)
job_search.py	Handles scraping from Drushim, GotFriends, and SerpAPI
job_filter.py	Filters jobs by keywords and experience (English + Hebrew)
telegram_bot.py	Formats and sends Telegram messages
database.py	SQLite setup and deduplication logic
config.py	Loads environment variables
n8n-data/	Example n8n workflow (Schedule → HTTP Request)
docker-compose.yml	Defines Flask + n8n services
.env.example	Example configuration template

⚙️ Key Features
Feature	Description
✅ Automated Scheduling	n8n runs the job search on a predefined schedule
✅ Smart Filtering	Matches junior/0–3y roles and key DevOps terms
✅ Telegram Notifications	Sends real-time messages with job details
✅ Persistent Storage	SQLite DB keeps job history and prevents duplicates
✅ Modular Design	Independent Flask and n8n services via Docker
✅ Optional SerpAPI Integration	Adds Google Jobs results (free-tier API)

🧠 Challenges & Solutions
Challenge	Solution
Filtering too strictly (missing valid jobs)	Reduced required keyword matches and relaxed experience filter
Hebrew job descriptions not matching	Added Hebrew keyword and experience pattern support
Duplicate messages after restarts	Used Docker volume for persistent SQLite database
No results from limited sources	Added optional SerpAPI (Google Jobs) integration for more coverage
Workflow timing	Offloaded search to background thread to prevent n8n timeouts

🧩 Tools Used
Docker · Flask · Python · n8n · Telegram Bot API · SQLite · BeautifulSoup · SerpAPI

🧾 Environment Variables
Variable	Description
TELEGRAM_BOT_TOKEN	Telegram bot token (from @BotFather)
TELEGRAM_CHAT_ID	Your Telegram user or group chat ID
SEARCH_KEYWORDS	Job titles to search (e.g., "devops engineer, cloud engineer")
JOB_KEYWORDS	Tech stack filters (e.g., "jenkins, aws, docker, kubernetes")
EXPERIENCE_LEVELS	Experience filters (default: "junior, entry level, 0-3 years")
SERPAPI_KEY	Optional API key for Google Jobs (free tier available)
DATABASE_URL	Default: sqlite:///data/jobs.db (persistent via Docker volume)
N8N_WEBHOOK_SECRET	Optional secret for webhook authentication
PORT	Flask server port (default: 8000)

🧱 Docker & Setup
Run locally:
docker compose up -d --build
Check health:
curl http://localhost:8000/health

Manual trigger:
curl -X POST http://localhost:8000/jobs/search

✅ Response:
{"status": "success", "result": {...}}

🗓️ n8n Workflow Configuration
Node	Type	Purpose
🕒 Schedule Trigger	Runs daily at chosen time	
🌐 HTTP Request	POST → http://jobbot:8000/webhook/n8n	

🧩 Optional Header	Add X-Webhook-Secret if enabled	
That’s all — the jobBot runs automatically, searching, filtering, and sending you updates every day.
💬 Example Telegram Output
🚀 Found 3 new job(s) today!

1/3 - Junior DevOps Engineer  
🏢 Company: Amdocs  
📍 Location: Tel Aviv  
🔗 Source: DRUSHIM  
📝 Description:  
Looking for a Junior DevOps Engineer with AWS & Jenkins experience...  

🔗 [View Job](https://www.drushim.co.il/job/123456/)

🧠 Learnings
Building this project helped me combine:
Automation + APIs — integrating n8n with Flask and Telegram
Data filtering logic — parsing and cleaning real-world job listings
Persistence & state — using SQLite for deduplication across runs
Scalable container design — two coordinated microservices via Docker Compose

👩‍💻 Author
Noa Vaturi
💼 LinkedIn · 💻 GitHub
