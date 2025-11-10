# JobBot - Telegram Job Search Bot

A Telegram bot that searches for DevOps, SRE, and Cloud Engineering jobs daily and sends relevant listings to your Telegram chat. The bot filters jobs based on experience level (0-3 years, junior, entry level, associate) and required skills (Jenkins, AWS, EKS, GitHub, Docker, etc.).

**Default location:** Israel (configurable via `SEARCH_LOCATIONS` environment variable)  
**Work arrangements:** Searches for on-site, hybrid, and remote positions

## Features

- 🔍 **Daily Job Search**: Automatically searches multiple job boards daily
- 🎯 **Smart Filtering**: Filters jobs by role, experience level, and required skills
- 📱 **Telegram Notifications**: Sends job listings directly to your Telegram chat
- 🔄 **n8n Integration**: Webhook endpoint for n8n workflow automation
- 💾 **Database Tracking**: Tracks posted jobs to avoid duplicates
- 📊 **Multiple Sources**: Searches Drushim, GotFriends (Israeli job sites), and Google Jobs (via SerpAPI)

## Job Sources

The bot currently supports:

1. **Drushim** (Primary - Israeli job site)
   - Leading job portal in Israel
   - Free, no API key required
   - Web scraping method
   - Excellent coverage of Israeli tech jobs

2. **GotFriends** (Primary - Israeli job site)
   - Popular Israeli job platform
   - Free, no API key required
   - Web scraping method
   - Great for tech and startup positions

3. **SerpAPI/Google Jobs** (Optional, requires API key)
   - Aggregates jobs from multiple sources including LinkedIn, Glassdoor, etc.
   - Requires paid API key (free tier: 100 searches/month)
   - Additional coverage beyond Israeli sites
   - [Sign up here](https://serpapi.com/)

### About LinkedIn and Glassdoor

**LinkedIn Jobs API:**
- Requires LinkedIn Partner Program approval
- Application process can take weeks/months
- May require business verification
- [More info](https://developer.linkedin.com/)

**Glassdoor Jobs API:**
- Requires API partnership approval
- Must contact Glassdoor directly
- May have usage restrictions
- [More info](https://www.glassdoor.com/developer/jobsApiActions.htm)

**Our Solution:**
The bot uses Israeli job sites that are specifically designed for the local market:
- **Drushim** (free, no approval needed, excellent Israeli job coverage)
- **GotFriends** (free, no approval needed, great for tech jobs)
- **SerpAPI** (optional, paid but affordable, aggregates from multiple sources including LinkedIn/Glassdoor via Google Jobs)

**Recommendation:** Drushim and GotFriends provide excellent coverage for Israeli jobs. Add SerpAPI if you want additional coverage from international sources.

## Installation

### Option 1: Docker Compose (Recommended)

1. **Clone or download this repository**

2. **Create a `.env` file** from the example:
```bash
cp env.example .env
```

3. **Edit `.env` file** with your configuration:
   - Add your Telegram bot token and chat ID
   - (Optional) Add SerpAPI key for enhanced job search

4. **Build and run with Docker Compose**:
```bash
docker-compose up -d
```

5. **Check logs**:
```bash
docker-compose logs -f
```

6. **Stop the service**:
```bash
docker-compose down
```

### Option 2: Manual Installation

1. **Clone or download this repository**

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Create a `.env` file** from the example:
```bash
cp env.example .env
```

4. **Edit `.env` file** with your configuration

## Setup

### 1. Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the instructions
3. Copy the bot token and add it to `.env` as `TELEGRAM_BOT_TOKEN`

### 2. Get Your Telegram Chat ID

**Quick Method:**
1. Start a chat with your bot (search for your bot by username and click "Start")
2. Send any message to your bot (e.g., `/start`)
3. Visit `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates` in your browser
   - Replace `<YOUR_BOT_TOKEN>` with your actual bot token
4. Find your chat ID in the JSON response (look for `"id"` under `"chat"`)
5. Add it to `.env` as `TELEGRAM_CHAT_ID`

**Alternative Methods:**
- Use `@userinfobot` or `@getidsbot` on Telegram (they'll show your User ID, which is your Chat ID for private chats)
- See `GET_TELEGRAM_CHAT_ID.md` for detailed instructions with multiple methods

### 3. (Optional) Get SerpAPI Key

1. Sign up at [SerpAPI](https://serpapi.com/)
2. Get your API key from the dashboard
3. Add it to `.env` as `SERPAPI_KEY`

**Note**: SerpAPI offers a free tier with 100 searches/month. For more searches, paid plans start at $50/month.

## Usage

### Docker Compose

**Start the service:**
```bash
docker-compose up -d
```

**View logs:**
```bash
docker-compose logs -f jobbot
```

**Stop the service:**
```bash
docker-compose down
```

**Restart the service:**
```bash
docker-compose restart
```

**Rebuild after code changes:**
```bash
docker-compose up -d --build
```

The server will be available at `http://localhost:8000` (or the port specified in `.env`).

### Manual Execution

**Run the bot manually:**
```bash
python main.py
```

**Start the Flask web server:**
```bash
python app.py
```

The server will start on `http://0.0.0.0:8000` (or the port specified in `.env`).

### n8n Integration

1. **Set up n8n workflow**:
   - Create a new workflow
   - Add a "Schedule Trigger" node (set to daily)
   - Add an "HTTP Request" node
   - Set method to `POST`
   - Set URL to `http://your-server:8000/webhook/n8n` (or `http://jobbot:8000/webhook/n8n` if n8n is on the same Docker network)
   - (Optional) Add header `X-Webhook-Secret` with your secret

2. **Test the webhook**:
```bash
# If running locally
curl -X POST http://localhost:8000/webhook/n8n

# If running in Docker
curl -X POST http://localhost:8000/webhook/n8n
```

**Note:** For Docker setups, make sure n8n can reach the jobbot container. You can either:
- Use the host's IP address and port mapping
- Add n8n to the same Docker network (`jobbot-network`)
- Use Docker service name if n8n is also containerized

### API Endpoints

- `GET /health` - Health check
- `POST /webhook/n8n` - n8n webhook endpoint (triggers job search)
- `POST /jobs/search` - Manually trigger job search
- `GET /stats` - Get job statistics

## Configuration

### Search Keywords

Modify `SEARCH_KEYWORDS` in `.env` to change job titles searched:
```
SEARCH_KEYWORDS=devops engineer,sre,cloud engineer,site reliability engineer
```

### Experience Levels

Modify `EXPERIENCE_LEVELS` in `.env`:
```
EXPERIENCE_LEVELS=junior,entry level,associate,0-3 years,intern
```

### Job Keywords

Modify `JOB_KEYWORDS` in `.env` to change required skills:
```
JOB_KEYWORDS=jenkins,aws,eks,github,docker,kubernetes,terraform
```

### Search Locations

Edit `SEARCH_LOCATIONS` in `.env` to change search locations (comma-separated):
```bash
SEARCH_LOCATIONS=Israel,Tel Aviv,Jerusalem,Haifa,Remote
```

Or modify in `config.py`:
```python
SEARCH_LOCATIONS = ['Israel', 'Tel Aviv', 'Jerusalem', 'Haifa', 'Remote']
```

**Default:** Israel, Tel Aviv, Jerusalem, Haifa, Remote

**Work Arrangements:** The bot searches for all work arrangements:
- **On-site** jobs (in Israeli cities)
- **Hybrid** jobs (combination of on-site and remote)
- **Remote** jobs (fully remote positions)

All job types matching your criteria will be included regardless of work arrangement.

## How It Works

1. **Job Search**: The bot searches multiple job boards using RSS feeds and APIs
2. **Filtering**: Jobs are filtered based on:
   - Role (DevOps Engineer, SRE, Cloud Engineer)
   - Experience level (0-3 years, junior, entry level, associate)
   - Required skills (at least 2 keywords must match)
3. **Database**: New jobs are saved to a SQLite database
4. **Telegram**: New jobs are sent to your Telegram chat
5. **Tracking**: Jobs are marked as sent to avoid duplicates

## Database

The bot uses SQLite to track jobs. The database file (`jobs.db`) is created automatically on first run.

To reset the database, simply delete the `jobs.db` file.

## Troubleshooting

### No jobs found

1. Check that your search keywords are correct
2. Verify that job boards are accessible
3. Try adjusting the keyword matching threshold in `job_filter.py`

### Telegram bot not sending messages

1. Verify `TELEGRAM_BOT_TOKEN` is correct
2. Verify `TELEGRAM_CHAT_ID` is correct
3. Make sure you've started a conversation with the bot

### Rate limiting

If you encounter rate limiting:
1. Add delays between requests in `job_search.py`
2. Use SerpAPI for more reliable access
3. Reduce the number of search keywords/locations

## Legal Considerations

- **Terms of Service**: Be aware that web scraping may violate some sites' ToS
- **Rate Limiting**: The bot includes delays to avoid overwhelming servers
- **API Usage**: When using paid APIs (SerpAPI), ensure you comply with their terms

## License

This project is provided as-is for personal use.

## Contributing

Feel free to submit issues or pull requests!

## Support

For issues or questions, please open an issue on GitHub.

