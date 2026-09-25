"""
India Job Agent — Sauvik Chakraborty
Functional Safety / ADAS / Systems Safety Engineer
Uses: Adzuna India API (free) + Groq API (free) + Google Sheets (free) + Gmail
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
# 1. API KEYS — shared from .env file
# ─────────────────────────────────────────────────────────────

ADZUNA_APP_ID     = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY    = os.getenv("ADZUNA_APP_KEY", "")
GROQ_API_KEY      = os.getenv("GROQ_API_KEY", "")
GOOGLE_CREDS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")
SPREADSHEET_ID    = os.getenv("SPREADSHEET_ID_SAUVIK", "")   # separate sheet for Sauvik
GMAIL_ADDRESS     = os.getenv("YOUR_EMAIL", "")
GMAIL_APP_PASS    = os.getenv("EMAIL_PASSWORD", "")

# Sauvik's email — add his own when ready
EMAIL_TO = [
    GMAIL_ADDRESS,            # Nivedita gets a copy for now
    # "sauvik@gmail.com",     # uncomment when Sauvik wants his own digest
]


# ─────────────────────────────────────────────────────────────
# 2. SAUVIK'S RESUME
# ─────────────────────────────────────────────────────────────

MY_RESUME = """
Name: Sauvik Chakraborty
Location: Bangalore, India (relocating from Stuttgart, Germany)
Notice Period: Available to join at short notice
Languages: English (C1 Business Fluent), German (B1), Bengali (Native)

Summary:
Systems Safety Engineer with 13 years of experience in safety-critical E/E development
on commercial vehicle and automotive platforms. Deep expertise in ADAS, active safety,
radar/sensor-fusion systems, functional safety (ISO 26262, SOTIF/ISO 21448), and
cybersecurity (ISO 21434). Proven track record leading HARA, safety concept development,
FMEA/FMEDA, FTA, DFA, and safety case generation. Strong embedded software background
(C/C++, MATLAB/Simulink) and vehicle network experience (CAN, CAN-FD, Automotive Ethernet).
TÜV SÜD ISO 26262 Level I Certified.

Professional Experience:

Systems Safety Engineer – Active Safety (Radar) Systems
Daimler Truck AG, Stuttgart | May 2024 – Present
- HARA: hazard identification, ASIL allocation, FTTI, safety concept definition for radar
  and braking-related ADAS functions
- Functional Safety Concept (FSC) and Technical Safety Concept (TSC) development including
  safety mechanisms, safety architecture across HW/SW/communication interfaces
- FMEA/FMEDA, FTA, Dependent Failure Analysis (DFA), Common-Cause Analysis
- SOTIF analysis (ISO 21448): acceptance criteria, system-level simulations,
  MATLAB/Simulink, Vector CANape/CANoe
- ISO 21434 TARA (Threat Analysis & Risk Assessment) for powertrain control units
- Safety audits, assessments, supplier data review and approval
- IBM DOORS: full requirements traceability from safety goals to TSRs
- HIL and prototype vehicle testing, V&V planning
- DIA (Development Interface Agreement), Safety Plans, Safety Case evidence packages

Systems Safety Engineer – ADAS
ZF Friedrichshafen AG | March 2021 – March 2024
- Technical Safety Concept for safety-critical ADAS subcomponents (full SW architecture)
- HARA, FMEA, FTA, DFA across electrical, mechanical, thermal failure domains
- Safety architecture for E/E, software and hardware subsystems; HSI for CAN/CAN-FD
- System Safety Assessments (SSA) for radar, sensor-fusion, and braking systems
- HIL/SIL/MIL validation strategies, vehicle network interface testing, road release approvals
- ISO 21434 TARA participation
- DIA, Safety Plans, all associated safety documentation

Functional Safety Engineer – Battery Management Systems
Samsung SDI Battery Systems GmbH, Graz, Austria | Oct 2019 – Feb 2021
- Safety concepts and software safety architecture for BMS
- Safety mechanism definition, HW/SW interface safety requirements
- Safety analyses: fault effects, failure propagation across HW/SW/communication
- Requirements traceability throughout development lifecycle
- Verification plans for safety functions; confirmation reviews

Sr. Embedded Software Engineer – Engine Control Systems
Mercedes-Benz R&D, Bangalore | Nov 2016 – Aug 2019
- Embedded software development for ECUs
- HiL test automation, error analyses, root cause analysis
- Onsite assignment at Mercedes Benz AG Stuttgart

Embedded Software Engineer – Engine Control & Aftertreatment Systems
Robert Bosch Engineering & Business Solutions, Bangalore | May 2013 – Oct 2016
- MATLAB/Simulink model development, Stateflow, MIL/SIL/PIL testing
- SDLC: requirements to functional testing, V&V
- Fuel injection and aftertreatment systems

Technical Skills:
- Functional Safety Standards: ISO 26262 (TÜV SÜD Level I Certified), ISO 21448 SOTIF,
  ISO 21434 Cybersecurity, ISO 8800, ASPICE, AUTOSAR, MISRA
- Safety Methods: HARA, FHA, SSA, FMEA, FMEDA, FTA, DFA, HAZOP, STPA, SOTIF analysis,
  ASIL decomposition, SEooC, Safety Case, Safety Plan, DIA, FSC, TSC
- ADAS & Active Safety: Radar (short & long range), sensor fusion, LKA, BSIS, MOIS,
  UNECE R155, UNECE R159, SAE L2+/L3 functions, braking system interfaces
- Vehicle Networks: CAN, CAN-FD, Automotive Ethernet, UDS Diagnostics
- Tools: MATLAB/Simulink, Vector CANape/CANoe, IBM DOORS, PTC Integrity, INCA,
  LabCAR, ASCET, CANalyzer
- Programming: C/C++, Python, Stateflow
- Requirements Management: DOORS, Codebeamer, traceability

Education:
Bachelor of Engineering – Electronics & Communications
Rashtrasant Tukadoji Maharaj Nagpur University, India (2008–2012)
Subjects: Embedded Systems, Microprocessors, DSP, Digital Systems, Mechatronics

Certifications: TÜV SÜD ISO 26262 Level I Certified
"""


# ─────────────────────────────────────────────────────────────
# 3. SEARCH SETTINGS — Functional Safety / ADAS domain
# ─────────────────────────────────────────────────────────────

ROLES = [
    "functional safety engineer",
    "FuSa engineer",
    "ADAS safety engineer",
    "systems safety engineer",
    "functional safety architect",
]

CITIES = ["Bangalore", "Pune", "Hyderabad", "Chennai"]

RESULTS_COUNT = 10
MIN_SCORE     = 6
GROQ_DELAY    = 2
SHEET_NAME    = "Sauvik Job Tracker"

# Domain-specific keywords for pre-filtering
MUST_HAVE_ANY = [
    "functional safety", "fusa", "iso 26262", "iso26262", "adas",
    "safety engineer", "sotif", "iso 21448", "hara", "fmea", "fta",
    "asil", "safety architect", "safety concept", "automotive safety",
    "radar", "sensor fusion", "embedded safety", "e/e", "ecu",
    "iso 21434", "cybersecurity automotive", "aspice", "safety case",
    "autonomous driving", "advanced driver", "active safety"
]

REJECT_IF_ANY = [
    "food safety", "fire safety", "health safety", "safety officer",
    "safety manager construction", "occupational safety", "workplace safety",
    "process safety", "chemical safety", "nuclear safety", "data analyst",
    "software developer", "web developer", "react", "angular", "java developer",
    "devops", "network engineer", "civil engineer", "mechanical design"
]


# ─────────────────────────────────────────────────────────────
# GOOGLE SHEETS HELPERS
# ─────────────────────────────────────────────────────────────

HEADERS = [
    "Score", "Title", "Company", "Location",
    "Salary", "Summary", "Why It Matches", "Gaps", "Date Found", "Job URL"
]


def get_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds  = Credentials.from_service_account_file(GOOGLE_CREDS_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID).sheet1


def get_seen_job_keys(sheet) -> set:
    try:
        all_rows = sheet.get_all_values()
        if len(all_rows) <= 1:
            return set()
        title_col   = HEADERS.index("Title")
        company_col = HEADERS.index("Company")
        seen = {
            f"{row[title_col].strip().lower()}|{row[company_col].strip().lower()}"
            for row in all_rows[1:]
            if len(row) > company_col
        }
        print(f"  📋 {len(seen)} jobs already in sheet — will skip these")
        return seen
    except Exception as e:
        print(f"  ⚠️  Could not read existing jobs: {e}")
        return set()


def ensure_headers(sheet):
    if not sheet.row_values(1):
        sheet.append_row(HEADERS)


def save_to_sheets(sheet, matches: list):
    print(f"\n📊 Saving {len(matches)} new matches to Google Sheets...")
    for job in matches:
        sheet.append_row([
            job["score"], job["title"], job["company"], job["location"],
            job["salary"], job["summary"], job["matches"], job["gaps"],
            job["date"], job["url"],
        ])
    print(f"✅ Saved — {len(matches)} rows added to '{SHEET_NAME}'")


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
# STEP 2: Pre-filter by keyword + dedup
# ─────────────────────────────────────────────────────────────

def pre_filter(jobs: list, seen_keys: set) -> list:
    kept, skipped_seen, skipped_keyword = [], 0, 0
    for job in jobs:
        title   = job.get("title", "").strip().lower()
        company = job.get("company", {}).get("display_name", "").strip().lower()
        key     = f"{title}|{company}"
        text    = (job.get("title", "") + " " + job.get("description", "")).lower()

        if key in seen_keys:
            skipped_seen += 1
            continue
        if any(kw in text for kw in REJECT_IF_ANY):
            skipped_keyword += 1
            continue
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
You are a job fit analyst specialising in automotive functional safety and ADAS roles.
Compare this candidate's profile to the job posting carefully.

CANDIDATE RESUME:
{MY_RESUME}

JOB POSTING:
Title: {title}
Company: {company}
Location: {location}
Description: {description}

Pay special attention to:
- ISO 26262 experience and certification (TÜV SÜD Level I is a strong differentiator)
- SOTIF/ISO 21448, ISO 21434 cybersecurity experience
- ADAS/radar/sensor fusion background
- Safety analysis methods (HARA, FMEA, FTA, DFA, HAZOP)
- Safety concept development (FSC, TSC, Safety Case, DIA, Safety Plan)
- Tools: DOORS, CANoe, MATLAB/Simulink
- OEM or Tier-1 supplier experience (Daimler, ZF, Bosch, Mercedes)

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
                <a href="{j["url"]}" style="background:#cc0000;color:#fff;
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
        no_new = """<tr><td style="padding:32px;text-align:center;color:#888;">
          No new matches today — all jobs already seen or scored below threshold.
        </td></tr>"""

    return f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <div style="max-width:640px;margin:24px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
    <div style="background:#cc0000;padding:28px 32px;">
      <div style="color:#fff;font-size:22px;font-weight:700;">🚗 Sauvik's Daily FuSa Job Digest</div>
      <div style="color:#ffcccc;font-size:14px;margin-top:4px;">{today}</div>
    </div>
    <div style="background:#fff5f5;padding:16px 32px;border-bottom:1px solid #ffe0e0;">
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
          <div style="font-size:28px;font-weight:700;color:#333;">{run_stats.get("total_seen", 0)}</div>
          <div style="font-size:12px;color:#555;">All-time tracked</div>
        </td>
      </tr></table>
    </div>
    <div style="padding:16px 32px;background:#fffdf0;border-bottom:1px solid #f0e8c0;">
      <div style="font-size:12px;font-weight:600;color:#856404;margin-bottom:6px;">
        ⚠️ Recurring skill gaps across roles:
      </div>
      {gap_pills}
    </div>
    <table style="width:100%;border-collapse:collapse;">
      {job_rows}{no_new}
    </table>
    <div style="padding:20px 32px;background:#f9f9f9;border-top:1px solid #eee;font-size:12px;color:#999;text-align:center;">
      Sauvik's Job Agent · Adzuna + Groq · {today}
    </div>
  </div>
</body>
</html>"""


def send_email(jobs: list, recipients: list, run_stats: dict):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASS:
        print("⚠️  Email skipped — credentials not set in .env")
        return

    today   = datetime.now().strftime("%d %b %Y")
    subject = f"🚗 Sauvik's FuSa Job Digest — {len(jobs)} new matches · {today}"
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
        print("❌ Gmail auth failed — check EMAIL_PASSWORD in .env")
    except Exception as e:
        print(f"❌ Email failed: {e}")


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("  Sauvik's Job Agent  (FuSa / ADAS / Systems Safety)")
    print("=" * 55)

    print("\n🔗 Connecting to Google Sheets...")
    try:
        sheet = get_sheet()
        ensure_headers(sheet)
    except Exception as e:
        print(f"❌ Could not connect to Google Sheets: {e}")
        return

    seen_keys   = get_seen_job_keys(sheet)
    groq_client = Groq(api_key=GROQ_API_KEY)

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

    fresh_jobs = pre_filter(all_jobs, seen_keys)
    print(f"\n📥 {len(all_jobs)} fetched → {len(fresh_jobs)} fresh jobs to score")

    if not fresh_jobs:
        print("No new jobs to score today.")
        send_email([], EMAIL_TO, {"total_seen": len(seen_keys)})
        return

    print(f"\n🤖 Scoring {len(fresh_jobs)} jobs with Groq...")
    scored = []
    for i, job in enumerate(fresh_jobs):
        title = job.get("title", "Unknown")
        print(f"  [{i+1}/{len(fresh_jobs)}] {title}")
        result = score_job(job, groq_client)
        if result:
            scored.append(result)
        time.sleep(GROQ_DELAY)

    top = sorted(
        [j for j in scored if j["score"] >= MIN_SCORE],
        key=lambda x: x["score"],
        reverse=True,
    )

    print(f"\n🎯 {len(top)} jobs scored {MIN_SCORE}+/10:")
    for j in top:
        print(f"  [{j['score']}/10] {j['title']} @ {j['company']} ({j['location']})")
        print(f"         {j['summary']}")

    if top:
        save_to_sheets(sheet, top)

    run_stats = {"total_seen": len(seen_keys) + len(top)}
    send_email(top, EMAIL_TO, run_stats)

    print("\n✅ Agent finished.")


if __name__ == "__main__":
    main()
