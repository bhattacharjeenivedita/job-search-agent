# =============================================
# RESUME SCORER
# Uses Claude AI to score each job against
# Nivedita's resume and return a match score
# with a plain-English explanation
# =============================================

import anthropic
import json
import os
from datetime import datetime
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================
# RESUME SUMMARY
# Claude uses this to score each job
# =============================================

RESUME = """
NAME: Nivedita Bhattacharjee
ROLE: Data Analyst | SQL | Power BI | Python
LOCATION: Stuttgart, Germany
AVAILABLE FROM: April 2026

SUMMARY:
Data analyst with several years of experience in data analytics, reporting,
and process automation. Specialises in building dashboards, data models,
and reporting solutions. Comfortable collaborating with cross-functional
teams and translating business needs into clear reporting solutions.

WORK EXPERIENCE:
1. Data Analyst — TOPdesk, Kaiserslautern (Nov 2025 – Present)
   - Developed and improved reporting solutions for operational data
   - Built and optimized SQL queries for large datasets
   - Created dashboards to support product and support teams
   - Worked with stakeholders to gather and translate requirements
   - Contributed to standardizing data definitions and improving data quality

2. Data Engineer Intern — LexGraph, Berlin (Sep–Oct 2025)
   - Automated data collection from ~50,000 webpages using Python
   - Built structured legal database from large unstructured datasets
   - Explored LLMs for automated analysis of legal data
   - Tools: Python, BeautifulSoup, Selenium, VS Code

3. Data Analyst — Deutsche Bank, Bangalore (Dec 2022 – Jul 2024)
   - Built and maintained data pipelines using SQL and Python
   - Automated reporting workflows, reducing manual effort by ~40%
   - Supported regulatory reporting and data validation processes
   - Worked with international stakeholders in Agile projects

4. Data Analyst — Tata Consultancy Services, Bangalore (Sep 2015 – Nov 2022)
   - Designed and developed Power BI dashboards for operational and risk reporting
   - Built data models and improved reporting structures
   - Automated reporting processes using SQL, Power BI, and R
   - Analysed large datasets to identify trends and support business decisions

EDUCATION:
- Post Graduate Diploma in Statistical Methods and Analytics
  Indian Statistical Institute (2015)
- Bachelor of Science in Mathematics
  Dibrugarh University (2014)

SKILLS:
Power BI, SQL, Python, RStudio, Qlik, Excel, Data Visualization,
Data Cleaning, Data Analysis, JIRA, KNIME, MS Access, Pandas,
Scikit-learn, Data Governance, Automation, Machine Learning Basics,
Data Pipelines, Database Management

LANGUAGES:
- English: C1 (Expert)
- German: A2 (currently improving to B1)

CERTIFICATIONS:
- Data Analyst Associate — DataCamp
- SQL Advanced — HackerRank
- Introduction to Generative AI — AWS
- Data Literacy — DataCamp
- AI Fundamentals — DataCamp
- McKinsey Forward Program

ACHIEVEMENTS:
- Recognised for strong SQL skills that improved team productivity
- Contributed to cost optimisation project at Deutsche Bank Excellence Forum

IMPORTANT CONSTRAINTS:
- German language level is only A2 (beginner) — currently improving to B1
- Must score very low any job requiring German at B2, C1 or C2 level
- Jobs requiring "Deutschkenntnisse" at advanced level are NOT suitable
- Jobs requiring "verhandlungssicheres Deutsch" are NOT suitable
- Only suitable if job requires no German OR basic German (A1/A2) OR English only
"""


# =============================================
# SCORE A SINGLE JOB WITH CLAUDE
# =============================================

def score_job_with_claude(job):
    """
    Sends a job listing and Nivedita's resume to Claude.
    Returns a score 0-100 with plain-English reasoning.
    """

    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("CLAUDE_API_KEY", "")
    client = anthropic.Anthropic(api_key=api_key)

    title = job.get("title", "Unknown")
    company = job.get("company", "Unknown")
    location = job.get("location", "Unknown")
    description = job.get("description", "No description available")
    portal = job.get("portal", "Unknown")

    prompt = f"""
You are a professional career advisor helping a data analyst find the best matching jobs.

Here is the candidate's resume:
{RESUME}

Here is a job listing:
Job Title: {title}
Company: {company}
Location: {location}
Portal: {portal}
Job Description:
{description[:2000]}

Please evaluate how well this job matches the candidate's profile.
Respond with ONLY a JSON object in this exact format, nothing else:
{{
    "score": <number between 0 and 100>,
    "match_level": "<one of: Excellent Match, Good Match, Partial Match, Poor Match>",
    "why_good": "<1-2 sentences on why this is a good fit>",
    "why_not": "<1 sentence on any gaps or concerns>",
    "key_matching_skills": ["skill1", "skill2", "skill3"]
}}

Scoring guide:
- 85-100: Excellent Match — strong skill overlap, right seniority, good location
- 70-84: Good Match — most requirements met, minor gaps
- 50-69: Partial Match — some relevant skills but notable gaps
- 0-49: Poor Match — not suitable

AUTOMATIC DISQUALIFIERS — score must be below 40 if any apply:
- Job requires German at B2, C1 or C2 level
- Job requires "verhandlungssicheres Deutsch"
- Job requires "Deutschkenntnisse" at advanced level
- Job is completely unrelated to data analytics or reporting
- Job requires 5+ years of specialised experience the candidate clearly lacks

Only return the JSON object. No extra text, no markdown backticks.
"""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text.strip()

        # Clean up in case of any markdown formatting
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        result = json.loads(response_text)
        return result

    except Exception as e:
        print(f"    Claude scoring error for '{title}': {e}")
        return {
            "score": 0,
            "match_level": "Error",
            "why_good": "Could not score this job",
            "why_not": str(e),
            "key_matching_skills": []
        }


# =============================================
# SCORE ALL JOBS AND RETURN TOP N
# =============================================

def score_all_jobs(jobs, top_n=5, min_score=50):
    """
    1. Deduplicates jobs by link and title+company
    2. Scores each job using Claude AI
    3. Saves ALL scored jobs to a review file
    4. Filters out jobs below min_score for email
    5. Returns top N per portal for email digest
    """

    # ---- DEDUPLICATION ----
    seen_links = set()
    seen_title_company = set()
    unique_jobs = []

    for job in jobs:
        link = job.get("link", "").strip()
        title = job.get("title", "").strip().lower()
        company = job.get("company", "").strip().lower()
        identity = f"{title}|{company}"

        if link and link in seen_links:
            continue
        if identity in seen_title_company:
            continue

        seen_links.add(link)
        seen_title_company.add(identity)
        unique_jobs.append(job)

    removed = len(jobs) - len(unique_jobs)
    print(f"\n  Deduplication: removed {removed} duplicates")
    print(f"  {len(unique_jobs)} unique jobs to score")
    print(f"  Minimum score threshold: {min_score}/100\n")

    # ---- SCORE EACH JOB ----
    all_scored = []

    for i, job in enumerate(unique_jobs, 1):
        title = job.get("title", "Unknown")
        print(f"  [{i}/{len(unique_jobs)}] Scoring: {title[:50]}...")

        assessment = score_job_with_claude(job)

        job["ai_score"] = assessment.get("score", 0)
        job["match_level"] = assessment.get("match_level", "Unknown")
        job["why_good"] = assessment.get("why_good", "")
        job["why_not"] = assessment.get("why_not", "")
        job["key_matching_skills"] = assessment.get("key_matching_skills", [])

        print(f"      Score: {job['ai_score']}/100 — {job['match_level']}")

        # Add to full list regardless of score
        all_scored.append(job)

    # ---- SAVE ALL SCORED JOBS FOR MANUAL REVIEW ----
    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs("output", exist_ok=True)
    review_file = f"output/all_scored_jobs_{today}.json"

    with open(review_file, "w", encoding="utf-8") as f:
        json.dump(
            sorted(all_scored, key=lambda x: x["ai_score"], reverse=True),
            f, ensure_ascii=False, indent=2
        )
    print(f"\n  All scored jobs saved for review: {review_file}")

    # ---- FILTER FOR EMAIL ----
    email_jobs = [j for j in all_scored if j["ai_score"] >= min_score]
    print(f"  {len(email_jobs)} jobs scored {min_score}+ for email digest")

    if not email_jobs:
        print(f"  No jobs above {min_score} — try lowering min_score in run_agent.py")
        return []

    # ---- GROUP BY PORTAL AND TAKE TOP N ----
    by_portal = {}
    for job in email_jobs:
        portal = job.get("portal", "Other")
        if portal not in by_portal:
            by_portal[portal] = []
        by_portal[portal].append(job)

    top_jobs = []
    for portal, portal_jobs in by_portal.items():
        sorted_jobs = sorted(portal_jobs, key=lambda x: x["ai_score"], reverse=True)
        top = sorted_jobs[:top_n]
        top_jobs.extend(top)
        print(f"  {portal}: kept top {len(top)} jobs")

    # Final sort by score
    top_jobs.sort(key=lambda x: x["ai_score"], reverse=True)
    print(f"\n  Final email digest: {len(top_jobs)} jobs")

    return top_jobs