# 🤖 Job Search Agent

An AI-powered Python agent that searches multiple job portals every morning, scores each listing against your resume using Claude AI, and emails you only the top matches — running fully autonomously in the cloud via GitHub Actions.

---

## 💡 Why I Built This

As a data & analytics professional actively looking for new opportunities in Germany, I built this tool to automate my daily job search completely. It scrapes multiple job portals, scores every listing against my actual resume using Claude AI, and emails me a daily ranked digest — no manual effort required.

This project also demonstrates my approach to problem-solving: when I face a challenge, I build a solution. It is my first independent Python and GitHub project, built entirely from scratch.

---

## ✨ Features

- 🔍 **Multi-portal search** — searches StepStone and Arbeitnow (LinkedIn via RapidAPI when free tier available)
- 🤖 **AI-powered resume matching** — Claude AI scores every job against your actual resume
- ⚡ **Smart pre-filtering** — keyword scorer shortlists top candidates before AI scoring (saves API costs)
- 🔄 **Deduplication** — same job appearing across multiple searches is counted only once, and never seen twice across days
- 📊 **Intelligent scoring** — scores based on recency, skill match, title match, location and company, plus Claude's deep resume analysis
- 📬 **Daily email digest** — top matches per portal delivered to your inbox every morning
- ☁️ **Fully cloud automated** — runs on GitHub Actions, works even when your laptop is off
- 💾 **Saves results** — exports all found and scored jobs to dated JSON files for manual review
- 🔒 **Secure by design** — sensitive credentials stored in `.env` locally and GitHub Secrets in the cloud, never exposed in the repository

---

## 🗂️ Project Structure

```
job-search-agent/
│
├── .github/
│   └── workflows/
│       └── daily_job_search.yml   # GitHub Actions cloud automation
│
├── config/
│   └── settings.py          # Your job search criteria, skills, portals
│
├── src/
│   ├── job_agent.py         # Scrapes StepStone, Arbeitnow & LinkedIn
│   ├── scorer.py            # Fast keyword pre-filter scorer
│   ├── resume_scorer.py     # Claude AI resume matching scorer
│   ├── deduplicator.py      # Cross-day deduplication
│   └── email_digest.py      # Builds & sends the HTML email
│
├── run_agent.py             # Single command to run everything
├── output/                  # Daily results saved here (local only)
├── .env                     # Private credentials (local only)
├── .gitignore                # Keeps secrets and clutter off GitHub
└── README.md                # You are here!
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/bhattacharjeenivedita/job-search-agent.git
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
LOCATIONS = ["Germany", "Remote"]
SKILLS = ["Python", "SQL", "Power BI", "Data Analysis", "Excel"]
```

### 6. Run locally

```bash
python run_agent.py
```

### 7. Deploy to the cloud (optional but recommended)

1. Add the same credentials from your `.env` as **GitHub Secrets**: repository → Settings → Secrets and variables → Actions
2. Enable **"Read and write permissions"**: Settings → Actions → General → Workflow permissions
3. The agent will then run automatically every morning at 8am German time via GitHub Actions — no laptop required!

---

## 🤖 How the AI Scoring Works

The agent uses a two-stage scoring system to keep costs low while maintaining quality:

**Stage 1 — Fast keyword pre-filter (free)**
All jobs are scored instantly using keyword and skill matching. Only the top candidates proceed to Stage 2.

**Stage 2 — Claude AI resume scoring (~$0.001 per job)**
Claude reads each job description and compares it against your full resume. It returns:
- A match score (0–100)
- Match level (Excellent / Good / Partial / Poor)
- Why it's a good fit
- Any gaps or concerns
- Key matching skills

Jobs scoring above your minimum threshold make it into your daily email. All scored jobs (including lower scores) are saved to a review file for manual checking.

---

## 📊 Scoring Breakdown (Pre-filter Stage)

| Factor | Points | Description |
|--------|--------|-------------|
| Recency | 40 | Fresh listings scored highest |
| Skill match | 25 | Skills found in title and description |
| Title match | 20 | Keyword appears in job title |
| Location | 10 | Matches your preferred locations |
| Company | 5 | Well-known international companies |

---

## ☁️ Cloud Automation

This project runs on **GitHub Actions** — completely free for this usage level:

- Scheduled to run daily at 7:00 UTC (8:00/9:00 German time depending on DST)
- Can also be triggered manually from the Actions tab
- Commits the updated "seen jobs" list back to the repository automatically
- No dependency on your laptop being on, awake, or connected

---

## 🛣️ Roadmap

- [x] StepStone scraper
- [x] Arbeitnow free API integration
- [x] LinkedIn via RapidAPI
- [x] Claude AI resume scoring
- [x] Smart pre-filtering to reduce API costs
- [x] Deduplication within and across days
- [x] Daily email digest with AI reasoning
- [x] GitHub Actions cloud automation
- [x] requirements.txt
- [ ] Web dashboard to view and manage results
- [ ] Deploy publicly so other job seekers can use it too

---

## 🛠️ Built With

- [Python 3.13](https://www.python.org/)
- [Requests](https://docs.python-requests.org/) — fetching web pages
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) — parsing HTML
- [Anthropic Claude API](https://www.anthropic.com/) — AI resume matching
- [langdetect](https://pypi.org/project/langdetect/) — language detection
- [python-dotenv](https://pypi.org/project/python-dotenv/) — secure credential management
- [RapidAPI](https://rapidapi.com/) — LinkedIn job search
- [GitHub Actions](https://github.com/features/actions) — cloud automation & CI/CD

---

## 👤 About Me

I'm a data & analytics professional currently open to new opportunities in Germany. This project reflects my approach to problem-solving — when I face a challenge, I build a solution.

Feel free to connect with me on [LinkedIn](https://www.linkedin.com/in/nivedita-bhattacharjee) or reach out via GitHub!

---

## ⚠️ Disclaimer

This tool is for personal job search assistance only. Always review job listings yourself before applying. The AI scoring is a guide, not a guarantee of fit.

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
