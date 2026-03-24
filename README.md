# 🤖 Job Search Agent

An AI-powered Python agent that searches multiple job portals every morning, scores each listing against your resume using Claude AI, and emails you only the top matches — built from scratch as a hands-on learning project.

---

## 💡 Why I Built This

As a data & analytics professional actively looking for new opportunities, I found myself spending too much time manually checking multiple job portals every day. So I built a tool to do it for me — one that not only finds jobs but intelligently ranks them against my actual resume.

This project is also my first step into Python development and GitHub — built entirely from scratch, with every line of code written and understood by me.

---

## ✨ Features

- 🔍 **Multi-portal search** — searches StepStone, Arbeitnow and LinkedIn
- 🤖 **AI-powered resume matching** — Claude AI scores every job against your actual resume
- ⚡ **Smart pre-filtering** — keyword scorer shortlists top candidates before AI scoring (saves API costs)
- 🔄 **Deduplication** — same job appearing across multiple searches is counted only once
- 🌍 **Language filtering** — filters out jobs requiring advanced German language skills
- 📊 **Intelligent scoring** — scores based on recency, skill match, title match, location and company
- 📬 **Daily email digest** — top 5 per portal delivered to your inbox every morning
- 💾 **Saves results** — exports all found jobs to a dated JSON file for tracking
- 🔒 **Secure by design** — sensitive credentials stored in `.env`, never exposed on GitHub

---

## 🗂️ Project Structure

```
job-search-agent/
│
├── config/
│   └── settings.py          # Your job search criteria, skills, portals
│
├── src/
│   ├── job_agent.py         # Scrapes StepStone, Arbeitnow & LinkedIn
│   ├── scorer.py            # Fast keyword pre-filter scorer
│   ├── resume_scorer.py     # Claude AI resume matching scorer
│   └── email_digest.py      # Builds & sends the HTML email
│
├── run_agent.py             # Single command to run everything
├── output/                  # Daily results saved here (local only)
├── .env                     # Private credentials (local only)
├── .gitignore               # Keeps secrets and clutter off GitHub
└── README.md                # You are here!
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/job-search-agent.git
cd job-search-agent
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac / Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up your private credentials

Create a `.env` file in the root folder:

```
YOUR_EMAIL=your.email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
YOUR_NAME=Your Name
CLAUDE_API_KEY=your_claude_api_key
RAPIDAPI_KEY=your_rapidapi_key
```

> ⚠️ Never share this file or commit it to GitHub.

**Getting your credentials:**
- **Gmail App Password**: Google Account → Security → 2-Step Verification → App Passwords
- **Claude API Key**: https://console.anthropic.com → API Keys (add ~$5 credit)
- **RapidAPI Key**: https://rapidapi.com → subscribe to LinkedIn Jobs Search (free tier)

### 5. Configure your search criteria

Edit `config/settings.py` to set your keywords, locations, skills and portals:

```python
KEYWORDS = ["Data Analyst", "BI Developer", "Power BI Developer"]
LOCATIONS = ["Stuttgart", "Baden-Württemberg", "Remote", "Germany"]
SKILLS = ["Python", "SQL", "Power BI", "Data Analysis", "Excel"]
```

### 6. Run the agent

```bash
python run_agent.py
```

Results will be printed in the terminal and the top matches emailed to you.

---

## 🤖 How the AI Scoring Works

The agent uses a two-stage scoring system to keep costs low while maintaining quality:

**Stage 1 — Fast keyword pre-filter (free)**
All jobs are scored instantly using keyword and skill matching. Only the top 30 candidates proceed to Stage 2.

**Stage 2 — Claude AI resume scoring (~$0.001 per job)**
Claude reads each job description and compares it against your full resume. It returns:
- A match score (0–100)
- Match level (Excellent / Good / Partial / Poor)
- Why it's a good fit
- Any gaps or concerns
- Key matching skills

Only jobs scoring 60+ make it into your daily email.

---

## 📊 Scoring Breakdown

| Factor | Points | Description |
|--------|--------|-------------|
| Recency | 40 | Fresh listings scored highest |
| Skill match | 25 | Skills found in title and description |
| Title match | 20 | Keyword appears in job title |
| Location | 10 | Matches your preferred locations |
| Company | 5 | Well-known international companies |

---

## 🛣️ Roadmap

- [x] StepStone scraper
- [x] Arbeitnow free API integration
- [x] LinkedIn via RapidAPI
- [x] Claude AI resume scoring
- [x] Smart pre-filtering to reduce API costs
- [x] Deduplication
- [x] Language detection & German language requirement filter
- [x] Daily email digest with AI reasoning
- [ ] Windows Task Scheduler automation
- [ ] requirements.txt
- [ ] Deduplication across days (never see same job twice)
- [ ] Web dashboard to view and manage results
- [ ] Deploy online so others can use it too

---

## 🛠️ Built With

- [Python 3.13](https://www.python.org/)
- [Requests](https://docs.python-requests.org/) — fetching web pages
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) — parsing HTML
- [Anthropic Claude API](https://www.anthropic.com/) — AI resume matching
- [langdetect](https://pypi.org/project/langdetect/) — language detection
- [python-dotenv](https://pypi.org/project/python-dotenv/) — secure credential management
- [RapidAPI](https://rapidapi.com/) — LinkedIn job search

---

## 👤 About Me

I'm a data & analytics professional currently open to new opportunities in Germany. This project reflects my approach to problem-solving — when I face a challenge, I build a solution.

Feel free to connect with me on [LinkedIn](https://www.linkedin.com/in/niveditabjee11/) or reach out via GitHub!

---

## ⚠️ Disclaimer

This tool is for personal job search assistance only. Always review job listings yourself before applying. The AI scoring is a guide, not a guarantee of fit.

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).