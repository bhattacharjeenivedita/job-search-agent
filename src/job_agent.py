"""
India Job Agent
Uses: Adzuna India API (free) + Groq API (free) + Google Sheets (free) + Gmail
- Appends new jobs only, never overwrites
- Skips jobs already seen in previous runs
- Sends daily email digest after each run
"""
 
import os
import json
import time
import smtplib
import requests
import gspread
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.oauth2.service_account import Credentials
from groq import Groq
from datetime import datetime
from dotenv import load_dotenv
 
load_dotenv()
 
 
# ─────────────────────────────────────────────────────────────
# 1. API KEYS — from your .env file
# ─────────────────────────────────────────────────────────────
 
ADZUNA_APP_ID     = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY    = os.getenv("ADZUNA_APP_KEY", "")
GROQ_API_KEY      = os.getenv("GROQ_API_KEY", "")
GOOGLE_CREDS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")
SPREADSHEET_ID    = os.getenv("SPREADSHEET_ID", "")
GMAIL_ADDRESS     = os.getenv("YOUR_EMAIL", "")
GMAIL_APP_PASS    = os.getenv("EMAIL_PASSWORD", "")
 
# Recipients — add more emails to this list anytime
EMAIL_TO = [
    GMAIL_ADDRESS,
    # "someone.else@gmail.com",
]
 
# ─────────────────────────────────────────────────────────────
# 2. YOUR RESUME
# ─────────────────────────────────────────────────────────────

MY_RESUME = """
Name: Nivedita Bhattacharjee
Location: [Bangalore, India]

Experience:
Independent Data, Analytics & AI Projects
| Independent |
Remote
Apr 2026 – Present
AI-Powered Job Search Automation
Developing a Python-based job discovery and matching workflow using APIs, web scraping, deduplication and LLM-assisted ranking. Currently adapting the pipeline for the Indian job market, including India-specific job sources, role matching and filtering. Earlier prototype automated scheduled execution and email reporting through GitHub Actions.
Used
:
Python, REST APIs, Claude API, Git/GitHub, BeautifulSoup
Community Market Research & Analytics Dashboard
Designed a primary-research survey to analyse demand, pricing, preferences and geographic patterns for a local home-food concept; built an interactive Looker Studio dashboard for ongoing analysis.
Used
:
Google Forms, Google Sheets, Looker Studio
Social Media Performance Automation
Automated extraction and daily updating of Instagram engagement data into Google Sheets, creating a structured dataset to help a small content business compare post performance and plan content.
Used:
Google Apps Script, REST APIs, Apify, Google Sheets
Data Analyst
| TOPdesk | Kaiserslautern, Germany
Nov 2025 – Mar 2026
Performed exploratory analysis on operational datasets to investigate business questions, identify patterns and resolve reporting inconsistencies.
Wrote and optimized complex SQL queries and stored procedures for analysis and reporting.
Developed Qlik Sense dashboards and standardized KPI definitions to improve business reporting and decision-making.
Worked with stakeholders to translate business questions into analytical and reporting solutions.
Used:
SQL, Qlik Sense, Salesforce, JIRA, Agile
Data Engineer Intern
| LexGr
aph
| Berlin, Germany
Sep 2025 – Oct 2025
Automated collection of data from ~50,000 webpages using Python, BeautifulSoup and Selenium, reducing weeks of potential manual work to an overnight pipeline.
Transformed large volumes of unstructured legal data into a structured analytical dataset through data cleaning and validation.
Explored LLM-based approaches for analyzing unstructured legal documents and extracting useful information.
Used:
Visual Studio Code, Python, Git, BeautifulSoup, Selenium
Career Break — Upskilling
| Stuttgart, Germany
Aug 2024 – Aug 2025
Completed structured learning in Data Science, Machine Learning and Generative AI through DataCamp, AWS, NVIDIA Academy, KNIME AG and McKinsey Forward, alongside hands-on Python/ML projects.
Lead Data Analyst
| Deutsche Bank | Bangalore, India
Dec 2022 – Jul 2024
Automated recurring data analysis and validation processes using SQL and Python, reducing manual effort by approximately 40%.
Performed data profiling, cross-source validation and reconciliation across large enterprise banking datasets to identify missing, inconsistent and incorrectly mapped records.
ddlllll/fddlbdf
Investigated data-quality issues involving legal entities, client/reference data and regulatory attributes, identifying root causes and supporting remediation.
Used SQL and Python-based text-matching techniques to cross-reference internal and external data sources, improve LEI completion and support legal-entity identification.
Analysed entity relationships and reference data to support identification of underlying principals and improve completeness and accuracy of downstream data.
Worked with cross-functional teams across regulated banking processes, supporting data controls, audit requirements, governance and analytical delivery within Agile/JIRA environments.
Contributed to an automation/cost-optimisation initiative recognised at the Deutsche Bank Excellence Forum.
Used:
Python, SQL, JIRA, Excel Advanced, Hive, Process Automation
Senior Data Analyst
| Tata Consultancy Services | Bangalore, India
Oct 2018 – Nov 2022
Designed and developed Power BI dashboards for KPI monitoring and operational decision-making, replacing manual Excel-based reporting.
Analysed KYC and regulatory data to identify trends, exceptions and data-quality issues supporting risk and control processes.
Automated recurring reporting using SQL, RStudio and Power BI, improving reporting efficiency and reducing manual intervention.
Used SQL to extract, transform and analyse data from large banking datasets for regular and ad-hoc analytical requirements.
Collaborated with business stakeholders to translate reporting requirements into KPIs, dashboards and analytical solutions.
Used:
Excel Advanced, SQL, RStudio, Power BI, Regulatory Compliance
Data Analyst
| Tata Consultancy Services | Bangalore, India
Sep 2015 – Sep 2018
Performed data preparation, analysis, and reporting using SQL and Excel to support operational decision-making.
Optimised SQL queries to improve reporting performance and data accuracy across high-volume datasets.
Automated recurring reports using MS Access and RStudio, reducing manual effort across the reporting cycle.
Recognised internally for SQL-driven productivity improvements that measurably reduced reporting cycle times.
Used
: MS Access, SQL, Excel Advanced, RStudio

Skills:
Advanced SQL , Python , Power BI , Qlik Sense, Statistical Analysis , Exploratory Data Analysis , Pandas , NumPy , Data Quality & Reconciliation , ETL/Data Transformation , KPI Frameworks , Advanced Excel , R/RStudio , REST APIs , Web Scraping , Git/GitHub , Agile/JIRA ,  Generative AI / LLM Integration, Google Apps Script , Looker Studio , Selenium , Data Visualization , Data Profiling , Data Cleaning & Validation , Process Automation

Education:
Postgraduate Diploma — Statistical Methods & Analytics
| Indian Statistical Institute | 2015
Bachelor of Science — Mathematics
| Dibrugarh University | 2014

Certifications:
Completed:
Data Analyst Associate (DataCamp) • SQL Advanced (HackerRank) • KNIME Analytics Platform Basic Proficiency • Data Literacy (DataCamp) • AI Fundamentals (DataCamp) • Introduction to Generative AI (AWS) • AI for All: GenAI (NVIDIA Academy) • McKinsey Forward Program
Current learning:
NASA Open Science 101 / Open Science Essentials • Elements of AI / University of Helsinki coursework
"""


# ─────────────────────────────────────────────────────────────
# 3. SEARCH SETTINGS
# ─────────────────────────────────────────────────────────────
 
ROLES  = ["data analyst", "senior data analyst"]
CITIES = ["Bangalore", "Pune", "Hyderabad", "Kolkata"]
 
RESULTS_COUNT = 10      # jobs per role+city combo
MIN_SCORE     = 6       # only save jobs scored 6+ to Sheets
GROQ_DELAY    = 2       # seconds between Groq calls
 
MUST_HAVE_ANY = [
    "sql", "python", "power bi", "data analyst", "analytics",
    "banking", "financial", "dashboard", "etl", "hive", "data engineer"
]
 
REJECT_IF_ANY = [
    "java developer", "devops", "react", "angular", "sap basis",
    "oracle dba", "network engineer", "hardware", "civil engineer"
]
 
 
# ─────────────────────────────────────────────────────────────
# GOOGLE SHEETS HELPERS
# ─────────────────────────────────────────────────────────────
 
HEADERS = [
    "Score", "Title", "Company", "Location",
    "Salary", "Summary", "Why It Matches", "Gaps", "Date Found", "Job URL"
]
 
def get_sheet():
    """Connect to Google Sheet and return the worksheet."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds  = Credentials.from_service_account_file(GOOGLE_CREDS_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    return spreadsheet.sheet1
 
 
def get_seen_job_urls(sheet) -> set:
    """
    Read all existing Job URLs from the sheet.
    Used to skip jobs we've already scored in previous runs.
    """
    try:
        all_rows = sheet.get_all_values()
        if len(all_rows) <= 1:      # only headers or empty
            return set()
        url_col_index = HEADERS.index("Job URL")
        seen = {row[url_col_index] for row in all_rows[1:] if len(row) > url_col_index}
        print(f"  📋 {len(seen)} jobs already in sheet — will skip these")
        return seen
    except Exception as e:
        print(f"  ⚠️  Could not read existing jobs: {e}")
        return set()
 
 
def ensure_headers(sheet):
    """Add headers if the sheet is empty."""
    existing = sheet.row_values(1)
    if not existing:
        sheet.append_row(HEADERS)
        print("  📄 Headers added to sheet")
 
 
def save_to_sheets(sheet, matches: list):
    """Append new matches to the sheet."""
    print(f"\n📊 Saving {len(matches)} new matches to Google Sheets...")
    for job in matches:
        sheet.append_row([
            job["score"], job["title"], job["company"], job["location"],
            job["salary"], job["summary"], job["matches"], job["gaps"],
            job["date"], job["url"],
        ])
    print(f"✅ Saved to sheet — {len(matches)} rows added")
 
 
# ─────────────────────────────────────────────────────────────
# STEP 1: Fetch jobs from Adzuna India
# ─────────────────────────────────────────────────────────────
 
def fetch_jobs(role: str, city: str) -> list:
    print(f"\n🔍 Searching: '{role}' in {city}...")
    url = (
        f"https://api.adzuna.com/v1/api/jobs/in/search/1"
        f"?app_id={ADZUNA_APP_ID}"
        f"&app_key={ADZUNA_APP_KEY}"
        f"&results_per_page={RESULTS_COUNT}"
        f"&what={role.replace(' ', '+')}"
        f"&where={city.replace(' ', '+')}"
        f"&content-type=application/json"
    )
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"  ❌ Adzuna error {response.status_code}")
            return []
        jobs = response.json().get("results", [])
        print(f"  ✅ Found {len(jobs)} listings")
        return jobs
    except Exception as e:
        print(f"  ❌ Request failed: {e}")
        return []
 
 
# ─────────────────────────────────────────────────────────────
# STEP 2: Pre-filter by keyword
# ─────────────────────────────────────────────────────────────
 
def pre_filter(jobs: list, seen_urls: set) -> list:
    kept = []
    skipped_seen    = 0
    skipped_keyword = 0
 
    for job in jobs:
        url  = job.get("redirect_url", "")
        text = (job.get("title", "") + " " + job.get("description", "")).lower()
 
        # Skip already seen jobs
        if url in seen_urls:
            skipped_seen += 1
            continue
 
        # Reject obvious mismatches
        if any(kw in text for kw in REJECT_IF_ANY):
            skipped_keyword += 1
            continue
 
        # Keep only relevant jobs
        if any(kw in text for kw in MUST_HAVE_ANY):
            kept.append(job)
        else:
            skipped_keyword += 1
 
    print(f"  🔎 Kept {len(kept)} | Skipped {skipped_seen} already seen | {skipped_keyword} irrelevant")
    return kept
 
 
# ─────────────────────────────────────────────────────────────
# STEP 3: Score each job with Groq
# ─────────────────────────────────────────────────────────────
 
def score_job(job: dict, client: Groq) -> dict | None:
    title       = job.get("title", "N/A")
    company     = job.get("company", {}).get("display_name", "N/A")
    location    = job.get("location", {}).get("display_name", "N/A")
    description = job.get("description", "No description")[:2000]
    salary_min  = job.get("salary_min", "")
    salary_max  = job.get("salary_max", "")
    job_url     = job.get("redirect_url", "N/A")
 
    salary = (
        f"INR {int(salary_min):,} - {int(salary_max):,}"
        if salary_min and salary_max else "Not disclosed"
    )
 
    prompt = f"""
You are a job fit analyst. Compare this candidate's resume to the job posting.
 
CANDIDATE RESUME:
{MY_RESUME}
 
JOB POSTING:
Title: {title}
Company: {company}
Location: {location}
Description: {description}
 
Return ONLY valid JSON with no markdown, no extra text, no code fences:
{{
  "score": <integer from 1 to 10>,
  "summary": "<one sentence why this is or is not a good fit>",
  "match_reasons": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "gaps": ["<gap 1>", "<gap 2>"]
}}
"""
 
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        raw = response.choices[0].message.content.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        parsed = json.loads(raw)
 
        return {
            "score":    parsed.get("score", 0),
            "title":    title,
            "company":  company,
            "location": location,
            "salary":   salary,
            "summary":  parsed.get("summary", ""),
            "matches":  " | ".join(parsed.get("match_reasons", [])),
            "gaps":     " | ".join(parsed.get("gaps", [])),
            "url":      job_url,
            "date":     datetime.now().strftime("%Y-%m-%d"),
        }
 
    except json.JSONDecodeError:
        print(f"    ⚠️  Could not parse response for '{title}'")
        return None
    except Exception as e:
        print(f"    ⚠️  Groq error for '{title}': {e}")
        return None
 
 
# ─────────────────────────────────────────────────────────────
# STEP 4: Send daily email digest
# ─────────────────────────────────────────────────────────────
 
def score_color(score):
    if score >= 9:   return "#1a7f3c", "#d4edda"
    elif score >= 7: return "#856404", "#fff3cd"
    else:            return "#5a5a5a", "#f0f0f0"
 
 
def build_email_html(jobs: list, run_stats: dict) -> str:
    today      = datetime.now().strftime("%A, %d %B %Y")
    top_count  = len([j for j in jobs if j["score"] >= 9])
    good_count = len([j for j in jobs if j["score"] >= 7])
 
    # Recurring gaps analysis
    all_gaps = []
    for j in jobs:
        all_gaps += [g.strip() for g in j["gaps"].split("|")
                     if g.strip() and g.strip().lower() not in ("none", "none significant", "")]
    gap_counts = {}
    for g in all_gaps:
        gap_counts[g] = gap_counts.get(g, 0) + 1
    top_gaps = sorted(gap_counts.items(), key=lambda x: x[1], reverse=True)[:4]
 
    job_rows = ""
    for j in jobs:
        text_color, bg_color = score_color(j["score"])
        job_rows += f"""
        <tr>
          <td style="padding:16px;border-bottom:1px solid #e8e8e8;vertical-align:top;">
            <div style="display:flex;align-items:flex-start;gap:12px;">
              <span style="background:{bg_color};color:{text_color};font-weight:700;
                           font-size:18px;padding:6px 10px;border-radius:8px;
                           min-width:36px;text-align:center;display:inline-block;">
                {j["score"]}
              </span>
              <div style="flex:1;">
                <div style="font-weight:600;font-size:15px;color:#1a1a1a;">
                  {j["title"]}
                  <span style="font-weight:400;color:#666;font-size:13px;">@ {j["company"]}</span>
                </div>
                <div style="color:#888;font-size:12px;margin:3px 0 8px;">
                  📍 {j["location"]} &nbsp;|&nbsp; 💰 {j["salary"]}
                </div>
                <div style="color:#333;font-size:13px;line-height:1.5;margin-bottom:8px;">
                  {j["summary"]}
                </div>
                <div style="font-size:12px;margin-bottom:4px;">
                  <span style="color:#1a7f3c;font-weight:600;">✓ </span>
                  <span style="color:#555;">{j["matches"]}</span>
                </div>
                <div style="font-size:12px;margin-bottom:10px;">
                  <span style="color:#c0392b;font-weight:600;">✗ </span>
                  <span style="color:#555;">{j["gaps"]}</span>
                </div>
                <a href="{j["url"]}" style="background:#0a66c2;color:#fff;
                   text-decoration:none;padding:6px 14px;border-radius:6px;
                   font-size:12px;font-weight:600;display:inline-block;">
                  View Job →
                </a>
              </div>
            </div>
          </td>
        </tr>"""
 
    gap_pills = "".join(
        f'<span style="background:#fff3cd;color:#856404;padding:3px 10px;'
        f'border-radius:12px;font-size:12px;margin:3px;display:inline-block;">'
        f'{g} ({c}×)</span>'
        for g, c in top_gaps
    ) if top_gaps else "<span style='color:#888;font-size:12px;'>No recurring gaps today</span>"
 
    no_new = ""
    if not jobs:
        no_new = """
        <tr><td style="padding:32px;text-align:center;color:#888;">
          No new matches today — all jobs were already seen or scored below threshold.
        </td></tr>"""
 
    return f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <div style="max-width:640px;margin:24px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
    <div style="background:#0a66c2;padding:28px 32px;">
      <div style="color:#fff;font-size:22px;font-weight:700;">🎯 Your Daily Job Digest</div>
      <div style="color:#cce0ff;font-size:14px;margin-top:4px;">{today}</div>
    </div>
    <div style="background:#f0f7ff;padding:16px 32px;border-bottom:1px solid #e0ecff;">
      <table style="width:100%;"><tr>
        <td style="text-align:center;">
          <div style="font-size:28px;font-weight:700;color:#1a7f3c;">{top_count}</div>
          <div style="font-size:12px;color:#555;">Top matches (9-10)</div>
        </td>
        <td style="text-align:center;">
          <div style="font-size:28px;font-weight:700;color:#856404;">{good_count}</div>
          <div style="font-size:12px;color:#555;">Good matches (7+)</div>
        </td>
        <td style="text-align:center;">
          <div style="font-size:28px;font-weight:700;color:#333;">{len(jobs)}</div>
          <div style="font-size:12px;color:#555;">New today</div>
        </td>
        <td style="text-align:center;">
          <div style="font-size:28px;font-weight:700;color:#333;">{run_stats.get('total_seen', 0)}</div>
          <div style="font-size:12px;color:#555;">All-time tracked</div>
        </td>
      </tr></table>
    </div>
    <div style="padding:16px 32px;background:#fffdf0;border-bottom:1px solid #f0e8c0;">
      <div style="font-size:12px;font-weight:600;color:#856404;margin-bottom:6px;">
        ⚠️ Recurring skill gaps — worth adding to your resume:
      </div>
      {gap_pills}
    </div>
    <table style="width:100%;border-collapse:collapse;">
      {job_rows}{no_new}
    </table>
    <div style="padding:20px 32px;background:#f9f9f9;border-top:1px solid #eee;font-size:12px;color:#999;text-align:center;">
      Sent by your India Job Agent · Adzuna + Groq · {today}
    </div>
  </div>
</body>
</html>"""
 
 
def send_email(jobs: list, recipients: list, run_stats: dict):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASS:
        print("⚠️  Email skipped — YOUR_EMAIL or EMAIL_PASSWORD not set in .env")
        return
 
    today   = datetime.now().strftime("%d %b %Y")
    subject = f"🎯 India Job Digest — {len(jobs)} new matches · {today}"
    html    = build_email_html(jobs, run_stats)
 
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = ", ".join(recipients)
    msg.attach(MIMEText(html, "html"))
 
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASS)
            server.sendmail(GMAIL_ADDRESS, recipients, msg.as_string())
        print(f"📧 Email sent to: {', '.join(recipients)}")
    except smtplib.SMTPAuthenticationError:
        print("❌ Gmail auth failed — check your App Password in .env")
    except Exception as e:
        print(f"❌ Email failed: {e}")
 
 
# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
 
def main():
    print("=" * 50)
    print("  India Job Agent  (Groq + dedup + email)")
    print("=" * 50)
 
    # Connect to sheet once — reuse throughout
    print("\n🔗 Connecting to Google Sheets...")
    try:
        sheet = get_sheet()
        ensure_headers(sheet)
    except Exception as e:
        print(f"❌ Could not connect to Google Sheets: {e}")
        return
 
    # Load already-seen URLs to avoid duplicates
    seen_urls = get_seen_job_urls(sheet)
 
    # Init Groq
    groq_client = Groq(api_key=GROQ_API_KEY)
 
    # Fetch all jobs
    all_jobs = []
    seen_ids = set()
    for role in ROLES:
        for city in CITIES:
            jobs = fetch_jobs(role, city)
            for job in jobs:
                job_id = job.get("id", job.get("redirect_url", ""))
                if job_id not in seen_ids:
                    seen_ids.add(job_id)
                    all_jobs.append(job)
 
    if not all_jobs:
        print("\nNo jobs fetched. Check Adzuna keys.")
        return
 
    # Pre-filter: remove seen + irrelevant
    fresh_jobs = pre_filter(all_jobs, seen_urls)
    print(f"\n📥 {len(all_jobs)} fetched → {len(fresh_jobs)} fresh jobs to score")
 
    if not fresh_jobs:
        print("No new jobs to score today.")
        run_stats = {"total_seen": len(seen_urls)}
        send_email([], EMAIL_TO, run_stats)
        return
 
    # Score with Groq
    print(f"\n🤖 Scoring {len(fresh_jobs)} jobs with Groq...")
    scored = []
    for i, job in enumerate(fresh_jobs):
        title = job.get("title", "Unknown")
        print(f"  [{i+1}/{len(fresh_jobs)}] {title}")
        result = score_job(job, groq_client)
        if result:
            scored.append(result)
        time.sleep(GROQ_DELAY)
 
    # Filter by min score
    top = sorted(
        [j for j in scored if j["score"] >= MIN_SCORE],
        key=lambda x: x["score"],
        reverse=True,
    )
 
    print(f"\n🎯 {len(top)} jobs scored {MIN_SCORE}+/10:")
    for j in top:
        print(f"  [{j['score']}/10] {j['title']} @ {j['company']} ({j['location']})")
        print(f"         {j['summary']}")
 
    # Save to sheet
    if top:
        save_to_sheets(sheet, top)
 
    # Send email (even if no new matches — keeps the daily habit)
    run_stats = {"total_seen": len(seen_urls) + len(top)}
    send_email(top, EMAIL_TO, run_stats)
 
    print("\n✅ Agent finished.")
 
 
if __name__ == "__main__":
    main()