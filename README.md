# 🤖 JobBot – Automated Job Search & Telegram Alerts

A smart, automated job-search assistant that continuously scans top job boards for **DevOps positions**, filters them intelligently, and delivers new listings straight to your **Telegram chat** — no manual searching required.

---

## 🏗️ Project Overview
This system automates the full **job discovery pipeline** — from scheduled search to personalized Telegram notifications — integrating multiple data sources, workflow automation, and message delivery services inside a Dockerized environment.
It demonstrates real-world event-driven automation, data filtering, and workflow orchestration using modern DevOps tools and APIs.

---

## 🧰 Tech Stack

| Category | Technologies |
|-----------|---------------|
| **Automation & Workflow** | n8n · Cron Scheduling · Webhooks |
| **Backend Service** | Flask (Python) |
| **Data Storage** | SQLite (persistent via Docker volume) |
| **Notifications** | Telegram Bot API |
| **Scraping & Aggregation** | Drushim · GotFriends · SerpAPI (Google Jobs) |
| **Containerization** | Docker · Docker Compose |

---	
		
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

---

## 🚀 Workflow Summary

| Stage | Description |
|-------|--------------|
| ⏰ **Schedule Trigger** | n8n runs daily or weekly on a defined schedule |
| 🔗 **Webhook Call** | Sends POST request to /webhook/n8n endpoint |
| 🔍 **Job Search** | Flask searches Drushim + GotFriends and SerpAPI |
| 🧠 **Filter Jobs** | Filters postings by experience level (0–3 years) and DevOps keywords |
| 💾 **Database Save** | Stores new jobs in SQLite and skips duplicates |
| 💬 **Telegram Alert** | Sends formatted job listings directly to Telegram chat |
| 📭 **No New Jobs** | Sends a "No new jobs today" message if no matches are found |

---

## 📁 Repository Breakdown
| Folder / File | Description |
|-------------|-------------|
| 🔹 **app.py** | AFlask API and /webhook/n8n endpoint
| 🔹 **job_service.py** | Core service logic (search → filter → save → send)
| 🔹 **job_search.py** | Handles scraping from Drushim, GotFriends, and SerpAPI
| 🔹 **job_filter.py** | Filters jobs by keywords and experience (English + Hebrew)
| 🔹 **telegram_bot.py** | Formats and sends Telegram messages
| 🔹 **database.py** | SQLite setup and deduplication logic
| 🔹 **config.py** | Loads environment variables
| 🔹 **n8n-data/** | Example n8n workflow (Schedule → HTTP Request)
| 🔹 **docker-compose.yml** | Defines Flask + n8n services
| 🔹 **.env.example** | Example configuration template

---

## 📸 Screenshots & Demo

| Section | Preview |
|----------|----------|
| **N8N UI** | ![argocd-ui](https://github.com/user-attachments/assets/fce78f8e-cff1-493f-a216-028203e65069) |
| **Bot- Telegram Chat** | <img width="1792" height="949" alt="web-prev" src="https://github.com/user-attachments/assets/b0456dd5-ad5f-492b-96e6-0a59ee70df67" /><br>🎥 [**Watch Demo Video**](docs/web.mp4) |

---	

## ⚙️ Key Features
| Feature | Description |
|----------|--------------|
| ✅ Automated Scheduling | n8n runs the job search on a predefined schedule |
| ✅ Smart Filtering | Matches junior/0–3y roles and key DevOps terms |
| ✅ Telegram Notifications | Sends real-time messages with job details |
| ✅ Persistent Storage | SQLite DB keeps job history and prevents duplicates |
| ✅ Modular Design | Independent Flask and n8n services via Docker |
| ✅ SerpAPI Integration | Adds Google Jobs results (free-tier API) |

---

## 🧠 Challenges & Solutions
| Challenge | Solution |
|------------|-----------|
| Filtering too strictly (missing valid jobs) | Reduced required keyword matches and relaxed experience filter |
| Hebrew job descriptions not matching | Added Hebrew keyword and experience pattern support |
| Duplicate messages after restarts | Used Docker volume for persistent SQLite database |
| No results from limited sources | Added SerpAPI (Google Jobs) integration for more coverage |
| Workflow timing | Offloaded search to background thread to prevent n8n timeouts |

---

## 🧩 Tools Used
Docker · Flask · Python · n8n · Telegram Bot API · SQLite · BeautifulSoup · SerpAPI

---

## 🧪 Running Locally

Make sure Docker and Docker Compose are installed.

```bash
# Clone the repository
git clone https://github.com/NoaVaturi/JobBot.git
cd JobBot

docker compose up -d --build
Check health:
curl http://localhost:8000/health
```

Manual trigger:
```bash
curl -X POST http://localhost:8000/jobs/search
```

✅ Response:
{"status": "success", "result": {...}}

---

## 🗓️ n8n Workflow Configuration
| Node | Type | 
|----------|--------------|
| 🕒 Schedule Trigger | Runs daily at chosen time |
| 🌐 HTTP Request | POST → http://jobbot:8000/webhook/n8n |

---

That’s all — the jobBot runs automatically, searching, filtering, and sending you updates every day.

---

💬 Example Telegram Output
🚀 Found 3 new job(s) today!

1/3 - Junior DevOps Engineer  
🏢 Company: Amdocs  
📍 Location: Tel Aviv  
🔗 Source: DRUSHIM  
📝 Description:  
Looking for a Junior DevOps Engineer with AWS & Jenkins experience...  

🔗 [View Job](https://www.drushim.co.il/job/123456/)

---

## 🧠 Learnings
Building this project helped me combine:
Automation + APIs — integrating n8n with Flask and Telegram
Data filtering logic — parsing and cleaning real-world job listings
Persistence & state — using SQLite for deduplication across runs
Scalable container design — two coordinated microservices via Docker Compose

👩‍💻 Author
Noa Vaturi
💼 LinkedIn · 💻 GitHub
