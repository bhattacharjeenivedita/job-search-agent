# 🎯 India Job Search Agent

An AI-powered daily job search agent for the Indian market. Fetches fresh listings, scores them against a resume using LLM, saves top matches to Google Sheets, and emails a daily digest — fully automated via GitHub Actions.

Built and maintained by [@bhattacharjeenivedita](https://github.com/bhattacharjeenivedita).

---

## How It Works

1. **Fetch** — pulls fresh job listings from Adzuna India API across multiple roles and cities
2. **Deduplicate** — skips jobs already seen in previous runs (tracked via Google Sheets)
3. **Pre-filter** — keyword-based filter removes irrelevant roles instantly (no API cost)
4. **Score** — sends shortlisted jobs to Groq LLM, scored 1–10 against the candidate's resume
5. **Save** — appends new top matches (score 6+) to Google Sheets, never overwrites
6. **Email** — sends a formatted HTML digest with scores, match reasons, gaps, and job links

Runs automatically every morning at **8:00 AM IST** via GitHub Actions.

---

## Agents

### Nivedita — Data Analyst
- **Roles:** Data Analyst, Senior Data Analyst
- **Cities:** Bangalore, Pune, Hyderabad, Kolkata
- **Script:** `src/job_agent.py`
- **Sheet:** India Job Tracker

### Sauvik — Functional Safety / ADAS
- **Roles:** Functional Safety Engineer, FuSa Engineer, ADAS Safety Engineer, Systems Safety Engineer
- **Cities:** Bangalore, Pune, Hyderabad, Chennai
- **Script:** `src/job_agent_sauvik.py`
- **Sheet:** Sauvik Job Tracker

---

## Project Structure

```
job-search-agent/
├── .github/
│   └── workflows/
│       └── daily_job_agent.yml      # runs both agents daily at 8am IST
├── src/
│   ├── job_agent.py                 # Nivedita's agent
│   ├── job_agent_sauvik.py          # Sauvik's agent
│   ├── mock_and_email.py            # email preview / dry run tool
│   └── test_sheets.py               # Google Sheets connection tester
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Setup

### Prerequisites
- Python 3.11+
- A Google Cloud project with Sheets + Drive APIs enabled
- Free accounts on: [Adzuna Developer](https://developer.adzuna.com) · [Groq](https://console.groq.com) · Gmail with App Password

### 1. Clone the repo
```bash
git clone https://github.com/bhattacharjeenivedita/job-search-agent.git
cd job-search-agent
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. Create `.env` in the project root
```
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key
GROQ_API_KEY=your_groq_api_key
SPREADSHEET_ID=your_google_sheet_id_nivedita
SPREADSHEET_ID_SAUVIK=your_google_sheet_id_sauvik
YOUR_EMAIL=your_gmail@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
```

### 3. Add `credentials.json` to `src/`
Download from Google Cloud Console → Service Account → Keys → JSON.
Share both Google Sheets with the service account email as Editor.

### 4. Run locally
```bash
python src/job_agent.py           # Nivedita
python src/job_agent_sauvik.py    # Sauvik
```

---

## GitHub Actions (Automated Daily Run)

The workflow runs both agents every day at 8:00 AM IST.

Add these secrets under **Settings → Secrets and variables → Actions**:

| Secret | Description |
|---|---|
| `ADZUNA_APP_ID` | Adzuna API App ID |
| `ADZUNA_APP_KEY` | Adzuna API App Key |
| `GROQ_API_KEY` | Groq API key |
| `SPREADSHEET_ID` | Nivedita's Google Sheet ID |
| `SPREADSHEET_ID_SAUVIK` | Sauvik's Google Sheet ID |
| `YOUR_EMAIL` | Gmail address |
| `EMAIL_PASSWORD` | Gmail App Password |
| `GOOGLE_CREDENTIALS_JSON` | Full contents of `credentials.json` |

Trigger manually anytime: **Actions → Daily India Job Agent → Run workflow**

---

## Tech Stack

| Component | Tool |
|---|---|
| Job data | [Adzuna India API](https://developer.adzuna.com) (free) |
| LLM scoring | [Groq](https://console.groq.com) — `openai/gpt-oss-120b` (free) |
| Storage | Google Sheets via `gspread` |
| Email | Gmail SMTP |
| Scheduling | GitHub Actions (cron) |
| Language | Python 3.11 |

---

## Security

- `.env` and `credentials.json` are in `.gitignore` and never committed
- All secrets stored as encrypted GitHub Secrets
- `credentials.json` is written at runtime from a GitHub Secret and deleted after the job finishes

---

## Disclaimer

This tool is for personal job search assistance. Always review listings manually before applying. AI scoring is a guide, not a guarantee of fit.