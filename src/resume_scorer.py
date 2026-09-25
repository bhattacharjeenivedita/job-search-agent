# =============================================
# RESUME SCORER
# Scores each job against the candidate profile
# using a configurable AI provider.
# =============================================

import re
import json
import os
import csv
from datetime import datetime
import sys

import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import (
    AI_PROVIDER,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    OLLAMA_MODEL,
    OLLAMA_URL,
)


# =============================================
# RESUME SUMMARY
# AI uses this to score each job
# =============================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESUME_FILE = os.path.join(BASE_DIR, "data", "resume_profile.txt")


def load_resume_text():
    """
    Loads the resume/profile text from a separate file.
    """

    if not os.path.exists(RESUME_FILE):
        raise FileNotFoundError(
            f"Resume file not found: {RESUME_FILE}"
        )

    with open(RESUME_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()

# =============================================
# HELPERS
# =============================================

def strip_html_tags(text):
    """
    Removes HTML tags from a job description.
    """

    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>|</div>|</li>|</h1>|</h2>|</h3>|</h4>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<li>", "- ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    return text


def clean_job_description(description):
    """
    Cleans job description text and keeps the most relevant parts
    for AI scoring.
    """

    if not description:
        return "No description available"

    text = strip_html_tags(description)

    # Normalize whitespace
    text = text.replace("&nbsp;", " ")
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)

    # Remove common footer / boilerplate phrases
    boilerplate_patterns = [
        r"find more .*? jobs .*?$",
        r"apply now.*?$",
        r"about us.*?$",
        r"hiring process.*?$",
        r"compensation details.*?$",
        r"benefits.*?$",
        r"why join us.*?$",
    ]

    cleaned_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        lower_line = stripped.lower()

        if any(re.search(pattern, lower_line) for pattern in boilerplate_patterns):
            continue

        cleaned_lines.append(stripped)

    cleaned_text = "\n".join(cleaned_lines)

    # Try to prioritize relevant sections if headings exist
    priority_keywords = [
        "responsibilities",
        "requirements",
        "qualifications",
        "skills",
        "what you bring",
        "what we're looking for",
        "role",
        "about the role",
        "your profile",
        "must have",
        "nice to have",
        "experience",
    ]

    priority_lines = []
    other_lines = []

    for line in cleaned_text.splitlines():
        lower_line = line.lower()
        if any(keyword in lower_line for keyword in priority_keywords):
            priority_lines.append(line)
        else:
            other_lines.append(line)

    ordered_text = "\n".join(priority_lines + other_lines)

    # Keep it compact but not blindly truncated too early
    return ordered_text[:2000]

def build_scoring_prompt(job):
    """
    Builds the scoring prompt for the active AI provider.
    """

    title = job.get("title", "Unknown")
    company = job.get("company", "Unknown")
    location = job.get("location", "Unknown")
    description = clean_job_description(job.get("description", ""))
    portal = job.get("portal", "Unknown")
    resume_text = load_resume_text()

    return f"""
You are a professional career advisor helping a data analyst find the best matching jobs.

Here is the candidate's resume:
{resume_text}

Here is a job listing:
Job Title: {title}
Company: {company}
Location: {location}
Portal: {portal}
Job Description:
{description}

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
- 85-100: Excellent Match - strong direct alignment in title, responsibilities, tools, and seniority
- 70-84: Good Match - clearly relevant analytics/BI/reporting role with good skill overlap and manageable gaps
- 55-69: Partial Match - relevant role with some overlap, but noticeable gaps in tools, seniority, domain, or responsibilities
- 0-54: Poor Match - weak alignment or clear mismatch

Important scoring instructions:
- Use the full score range realistically
- Be selective with scores above 80; only give 80+ when the role is strongly aligned to the candidate's actual experience
- Do not give high scores only because a job mentions data, analytics, BI, reporting, SQL, or dashboards once or twice
- Prefer direct alignment in title, day-to-day responsibilities, tools, and seniority
- Give strong credit for transferable analytics experience across industries when the analytical work itself is similar
- Domain match such as banking or regulatory reporting is a bonus, not a requirement
- Do not reduce the score too much only because the industry is different if the analytical work itself is strongly aligned
- Give strong credit when the role involves dashboarding, KPI reporting, SQL analysis, stakeholder reporting, business intelligence, reporting automation, or analytical problem-solving similar to the candidate's prior work
- Reduce the score only when the role is loosely related in actual responsibilities, not merely because the business domain is different
- Reduce the score when the role is mainly consulting, sales, product management, software engineering, infrastructure, or operations rather than hands-on analytics/reporting/business intelligence work
- Reduce the score when the seniority is significantly above the candidate's profile or the responsibilities are substantially different
- Roles in data analytics, BI, reporting, dashboarding, SQL, Power BI, Python, governance, audit support, healthcare analytics, business analytics, or data migration can score well if responsibilities align
- A role should not receive 75+ unless it is genuinely worth applying to based on likely fit
- Reduce the score sharply when the role requires prior domain experience the candidate does not have
- Do not reduce the score sharply if that domain experience is described as preferred, optional, non-mandatory, or not required

Automatic low-score situations:
- The role is mainly unrelated to analytics, BI, reporting, dashboards, or data-focused business analysis
- The role is primarily sales, product, generic consulting, infrastructure, or software engineering
- The role demands expertise or responsibilities the candidate clearly does not have
- The role has only superficial keyword overlap but poor actual fit

Be practical and calibrated. The goal is to identify genuinely worthwhile applications, not to inflate scores for loosely related jobs.

Only return the JSON object. No extra text, no markdown backticks.
"""


def parse_model_json(response_text):
    """
    Cleans model output and parses the JSON response.
    """

    response_text = response_text.strip()

    if "```json" in response_text:
        response_text = response_text.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```", 1)[1].split("```", 1)[0].strip()

    return json.loads(response_text)


def fallback_error_result(job, error_message):
    """
    Returns a fallback result when AI scoring fails.
    Falls back to the pre-filter score instead of always returning zero.
    """

    return {
        "score": 0,
        "match_level": "Scoring Unavailable",
        "why_good": "No AI assessment is available because scoring failed.",
        "why_not": f"AI scoring failed: {error_message}",
        "key_matching_skills": [],
        "score_source": "unavailable",
    }

def ensure_reasoning_fields(job, assessment):
    """
    Ensures scored jobs always have clear explanation fields.
    """

    title = job.get("title", "this role")
    matched_skills = assessment.get("key_matching_skills", []) or []

    why_good = str(assessment.get("why_good", "")).strip()
    why_not = str(assessment.get("why_not", "")).strip()
    match_level = str(assessment.get("match_level", "")).strip()
    score = assessment.get("score", 0)

    if not why_good:
        if matched_skills:
            why_good = (
                f"This role appears relevant because it matches skills such as "
                f"{', '.join(matched_skills[:3])}."
            )
        else:
            why_good = (
                f"This role was assessed as a {match_level.lower() or 'potential'} fit "
                f"based on title, skills, and experience alignment."
            )

    if not why_not:
        if score >= 80:
            why_not = "No major concerns were identified, but the job description should still be reviewed manually."
        elif score >= 60:
            why_not = "There may be some gaps in tools, domain experience, or exact role alignment."
        elif score >= 40:
            why_not = "This role has some relevant overlap, but there are notable gaps in fit."
        else:
            why_not = f"{title} appears to have significant gaps compared with the target profile."

    assessment["why_good"] = why_good
    assessment["why_not"] = why_not
    return assessment


def normalize_assessment(assessment):
    """
    Ensures score and match level are always present and valid.
    """

    raw_score = assessment.get("score", 0)

    try:
        score = int(float(raw_score))
    except (TypeError, ValueError):
        score = 0

    score = max(0, min(score, 100))

    match_level = str(assessment.get("match_level", "")).strip()
    if not match_level:
        if score >= 85:
            match_level = "Excellent Match"
        elif score >= 70:
            match_level = "Good Match"
        elif score >= 50:
            match_level = "Partial Match"
        else:
            match_level = "Poor Match"

    assessment["score"] = score
    assessment["match_level"] = match_level
    assessment["key_matching_skills"] = assessment.get("key_matching_skills", []) or []
    assessment["score_source"] = assessment.get("score_source", "ai")
    return assessment

# =============================================
# PROVIDERS
# =============================================

def score_job_with_ollama(job):
    """
    Scores a job using a local Ollama model.
    """

    prompt = build_scoring_prompt(job)

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=240)
    response.raise_for_status()
    data = response.json()

    return parse_model_json(data.get("response", ""))

def score_job_with_gemini(job):
    """
    Scores a job using the Gemini API.
    """

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is missing")

    prompt = build_scoring_prompt(job)

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        }
    }

    response = requests.post(url, json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()

    candidates = data.get("candidates", [])
    if not candidates:
        raise ValueError(f"No candidates returned by Gemini: {data}")

    content = candidates[0].get("content", {})
    parts = content.get("parts", [])
    if not parts:
        raise ValueError(f"No content parts returned by Gemini: {data}")

    response_text = parts[0].get("text", "")
    if not response_text:
        raise ValueError(f"Empty text returned by Gemini: {data}")

    return parse_model_json(response_text)


def score_job_with_claude(job):
    """
    Scores a job using Claude API.
    """

    import anthropic
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.getenv("CLAUDE_API_KEY", "")

    if not api_key:
        raise ValueError("CLAUDE_API_KEY is missing")

    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{"role": "user", "content": build_scoring_prompt(job)}],
    )

    return parse_model_json(message.content[0].text)


def score_job(job):
    """
    Dispatches scoring to the configured provider.
    """

    provider = AI_PROVIDER.lower()

    if provider == "ollama":
        return score_job_with_ollama(job)

    if provider == "gemini":
        return score_job_with_gemini(job)

    if provider == "claude":
        return score_job_with_claude(job)

    raise ValueError(f"Unsupported AI_PROVIDER: {AI_PROVIDER}")


# =============================================
# SCORE ALL JOBS AND RETURN TOP N
# =============================================

def score_all_jobs(jobs, top_n=5, min_score=50):
    """
    1. Deduplicates jobs by link and title+company
    2. Scores each job using the configured AI provider
    3. Saves ALL scored jobs to a review file
    4. Filters out jobs below min_score for email
    5. Returns top N per portal for email digest
    """

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
    print(f"  AI provider: {AI_PROVIDER}")
    print(f"  Minimum score threshold: {min_score}/100\n")

    all_scored = []

    for i, job in enumerate(unique_jobs, 1):
        title = job.get("title", "Unknown")
        print(f"  [{i}/{len(unique_jobs)}] Scoring: {title[:50]}...")

        try:
            assessment = score_job(job)
            assessment["score_source"] = "ai"
        except Exception as e:
            print(f"      Scoring error for '{title}': {e}")
            assessment = fallback_error_result(job, str(e))
        assessment = ensure_reasoning_fields(job, assessment)
        assessment = normalize_assessment(assessment)

        job["ai_score"] = assessment.get("score", 0)
        job["match_level"] = assessment.get("match_level", "Unknown")
        job["why_good"] = assessment.get("why_good", "")
        job["why_not"] = assessment.get("why_not", "")
        job["key_matching_skills"] = assessment.get("key_matching_skills", [])
        job["score_source"] = assessment.get("score_source", "ai")

        print(f"      Score: {job['ai_score']}/100 - {job['match_level']}")
        all_scored.append(job)

    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs("output", exist_ok=True)
    review_file = f"output/all_scored_jobs_{today}.json"

    with open(review_file, "w", encoding="utf-8") as f:
        json.dump(
            sorted(all_scored, key=lambda x: x["ai_score"], reverse=True),
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"\n  All scored jobs saved for review: {review_file}")

    csv_file = f"output/all_scored_jobs_{today}.csv"
    sorted_scored_jobs = sorted(all_scored, key=lambda x: x["ai_score"], reverse=True)

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "title",
                "company",
                "location",
                "portal",
                "keyword",
                "ai_score",
                "match_level",
                "score_source",
                "why_good",
                "why_not",
                "key_matching_skills",
                "link",
                "date_found",
            ],
        )
        writer.writeheader()
        for job in sorted_scored_jobs:
            row = {
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "location": job.get("location", ""),
                "portal": job.get("portal", ""),
                "keyword": job.get("keyword", ""),
                "ai_score": job.get("ai_score", 0),
                "match_level": job.get("match_level", ""),
                "score_source": job.get("score_source", "ai"),
                "why_good": job.get("why_good", ""),
                "why_not": job.get("why_not", ""),
                "key_matching_skills": ", ".join(job.get("key_matching_skills", [])),
                "link": job.get("link", ""),
                "date_found": job.get("date_found", ""),
            }
            writer.writerow(row)

    print(f"  CSV review file saved: {csv_file}")

    email_jobs = [
    j for j in all_scored
    if j["ai_score"] >= min_score
    and j.get("score_source", "ai") == "ai"
    and not j.get("hard_reject", False)
]
    print(f"  {len(email_jobs)} jobs scored {min_score}+ for email digest")

    if not email_jobs:
        print(f"  No jobs above {min_score} - try lowering min_score in run_agent.py")
        return []

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

    top_jobs.sort(key=lambda x: x["ai_score"], reverse=True)
    print(f"\n  Final email digest: {len(top_jobs)} jobs")

    return top_jobs
