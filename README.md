I can give you the final README ready to paste. I can read your repo from here, but I can’t safely write back into `C:\Users\Public\Shared_Drive_HxHL\job_agent_claude\job-search-agent` from the current workspace permissions.

Replace the full contents of [README.md](C:\Users\Public\Shared_Drive_HxHL\job_agent_claude\job-search-agent\README.md) with this:

```md
# Job Search Agent

A configurable Python job search agent that finds recent jobs, scores them against a candidate resume, and emails the best matches. It supports provider-based AI scoring, local profile configuration, and offline re-scoring from saved job files for low-cost testing.

---

## Why This Exists

This project started as a personal job search automation tool and has gradually been refactored into a reusable MVP that other job seekers can configure for their own profile.

The goal is simple:
- search for fresh jobs
- rank them quickly with rule-based filtering
- score the best ones against a resume
- send a compact daily digest with reasons

---

## Features

- Configurable profile-based setup
- Resume-based AI scoring
- Local Ollama scoring support
- Optional cloud scoring provider structure
- Rule-based pre-filtering before AI scoring
- Cross-run deduplication
- Offline re-scoring from saved raw jobs
- JSON and CSV review exports
- Email digest of top matches
- 24-hour freshness filtering for current live search flow

---

## Project Structure

```text
job-search-agent/
│
├── .github/
│   └── workflows/
│       └── daily_job_search.yml
│
├── config/
│   └── settings.py
│
├── data/
│   ├── profile.json
│   ├── profile_template.json
│   ├── resume_profile.txt
│   └── resume_template.txt
│
├── output/
│   ├── jobs_YYYY-MM-DD.json
│   ├── all_scored_jobs_YYYY-MM-DD.json
│   └── all_scored_jobs_YYYY-MM-DD.csv
│
├── src/
│   ├── job_agent.py
│   ├── scorer.py
│   ├── resume_scorer.py
│   ├── deduplicator.py
│   └── email_digest.py
│
├── run_agent.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

---

## Quick Setup

A user only needs to update 3 files:

1. `.env`
   Stores secrets and runtime settings such as email credentials, API keys, and AI provider selection.

2. `data/profile.json`
   Stores target roles, target locations, skills, thresholds, and shortlist preferences.

3. `data/resume_profile.txt`
   Stores the candidate resume/profile text used by the scorer.

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/bhattacharjeenivedita/job-search-agent.git
cd job-search-agent
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create `.env`

Example:

```env
YOUR_EMAIL=your_email@example.com
EMAIL_PASSWORD=your_gmail_app_password
YOUR_NAME=Your Name

AI_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=qwen3:8b

CLAUDE_API_KEY=
GEMINI_API_KEY=
RAPIDAPI_KEY=your_rapidapi_key
```

Notes:
- Keep `.env` private
- Do not commit `.env` to GitHub
- `RAPIDAPI_KEY` is needed for the current LinkedIn search flow
- `AI_PROVIDER=ollama` is the main local scoring path

### 5. Create your profile

Use `data/profile_template.json` as a starting point and save your real configuration as `data/profile.json`.

Example:

```json
{
  "name": "Your Name",
  "target_roles": [
    "Senior Data Analyst",
    "Data Analyst",
    "BI Analyst"
  ],
  "target_locations": [
    "India",
    "Bangalore",
    "Hyderabad",
    "Remote"
  ],
  "skills": [
    "SQL",
    "Python",
    "Power BI",
    "Excel"
  ],
  "domain_preferences": [
    "Banking",
    "Business Intelligence",
    "Analytics"
  ],
  "top_jobs_per_portal": 5,
  "min_score": 50,
  "pre_filter_limit": 5
}
```

### 6. Create your resume profile

Use `data/resume_template.txt` as a starting point and save your real profile as `data/resume_profile.txt`.

This file should contain:
- summary
- experience
- skills
- languages
- achievements
- important scoring constraints

### 7. Set up Ollama

Install Ollama, then run:

```bash
ollama pull qwen3:8b
ollama serve
```

### 8. Run the agent

```bash
python run_agent.py
```

---

## Offline Re-Scoring Mode

To avoid consuming live job-source quota during testing, the agent supports offline re-scoring.

In `run_agent.py`, set:

```python
USE_SAVED_JOBS = True
SAVED_JOBS_FILE = "output/jobs_2026-08-20.json"
```

This skips live search and reuses a previously saved raw jobs file.

Use offline mode when you want to:
- tune scoring prompts
- test explanation quality
- validate ranking changes
- avoid spending additional LinkedIn API calls

---

## Current Workflow

1. Search recent jobs from the configured portal(s)
2. Remove jobs already seen in previous runs
3. Pre-filter candidates using rule-based scoring
4. Score shortlisted jobs against the candidate profile using the selected AI provider
5. Save scored results to JSON and CSV
6. Email the top matches

---

## Output Files

Each run can generate these files in the `output/` folder:

- `jobs_YYYY-MM-DD.json`
  Raw jobs collected from the search source

- `all_scored_jobs_YYYY-MM-DD.json`
  Full scored results including score, reasoning, and matched skills

- `all_scored_jobs_YYYY-MM-DD.csv`
  Review-friendly export for manual inspection

The CSV includes:
- title
- company
- location
- portal
- keyword
- ai_score
- match_level
- why_good
- why_not
- key_matching_skills
- link
- date_found

---

## Scoring Approach

The agent uses two scoring layers:

### 1. Rule-Based Pre-Filter
This stage quickly ranks jobs using:
- title relevance
- skill overlap
- location match
- domain preference
- company recognition
- penalties for weak-fit titles or missing descriptions

### 2. AI Resume Scoring
The shortlisted jobs are then scored against the resume/profile.

The AI scorer returns:
- `score`
- `match_level`
- `why_good`
- `why_not`
- `key_matching_skills`

The current logic also:
- cleans noisy job descriptions before scoring
- adds fallback explanations when model output is incomplete
- normalizes malformed model output
- uses fallback scoring when AI scoring fails or times out

---

## Current Limitations

- LinkedIn/RapidAPI usage is limited by quota
- Local Ollama scoring can be slow on some machines
- Some job descriptions may be incomplete depending on the source
- AI scoring is assistive and should still be reviewed manually
- India-focused job-source coverage is still limited and should be expanded over time

---

## MVP Scope

This version is intended as a practical MVP:
- configurable for different users
- useful for daily job matching
- testable offline without repeated API usage
- suitable for small-scale user testing before turning it into a larger product

---

## Suggested Next Steps

Likely next product improvements:
- add more India-relevant job sources
- improve local model reliability further
- add a simple review UI/dashboard
- add resume/profile upload flow
- support hosted scoring providers more smoothly

---

## Built With

- [Python](https://www.python.org/)
- [Requests](https://docs.python-requests.org/)
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)
- [Ollama](https://ollama.com/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- [RapidAPI](https://rapidapi.com/)

---

## Disclaimer

This tool is for job search assistance and experimentation. Always review job listings manually before applying. AI scoring is only a guide and may not always reflect the true quality or fit of a role.

---

## License

This project is open source and available under the MIT License.
```

If you want, I can do one more pass after this and give you a **more product-facing README** version instead of this technical MVP version.