# =============================================
# JOB SCORER
# Ranks jobs based on your preferences:
# 1. Recency (most recent first)       — 40 pts
# 2. Skill match                       — 25 pts
# 3. Title match (exact keyword match) — 20 pts
# 4. Location match                    — 10 pts
# 5. Company size (well known)         —  5 pts
# =============================================

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import KEYWORDS, LOCATIONS, SKILLS

# Well known large companies — jobs here get a small bonus
WELL_KNOWN_COMPANIES = [
    "bosch", "daimler", "mercedes", "bmw", "volkswagen", "sap", "siemens",
    "deutsche bank", "allianz", "bayer", "basf", "adidas", "porsche",
    "zalando", "delivery hero", "scout24", "henkel", "continental",
    "infineon", "fresenius", "munich re", "pwc", "deloitte", "kpmg",
    "mckinsey", "bcg", "accenture", "ibm", "microsoft", "google",
    "amazon", "meta", "apple", "oracle", "wipro", "infosys", "tcs",
]


def score_job(job):
    """
    Gives each job a score out of 100 based on
    your ranking preferences.

    Scoring breakdown:
    - Recency      : up to 40 points
    - Skill match  : up to 25 points
    - Title match  : up to 20 points
    - Location     : up to 10 points
    - Company size : up to  5 points
    """

    score = 0
    reasons = []

    # ---- 1. RECENCY (40 points) ----
    # All freshly scraped jobs get full recency score
    score += 40
    reasons.append("fresh listing")

    # ---- 2. SKILL MATCH (25 points) ----
    # Check title AND description if available
    title_lower = job.get("title", "").lower()
    description_lower = job.get("description", "").lower()

    # Combine title and description for matching
    # Title matches count double since they're more relevant
    matched_in_title = [
        skill for skill in SKILLS
        if skill.lower() in title_lower
    ]
    matched_in_description = [
        skill for skill in SKILLS
        if skill.lower() in description_lower
        and skill not in matched_in_title
    ]

    matched_skills = matched_in_title + matched_in_description

    if matched_skills:
        # Title matches worth more than description matches
        title_score = min(len(matched_in_title) * 10, 20)
        desc_score = min(len(matched_in_description) * 3, 5)
        skill_score = min(title_score + desc_score, 25)
        score += skill_score
        reasons_parts = []
        if matched_in_title:
            reasons_parts.append(f"in title: {', '.join(matched_in_title)}")
        if matched_in_description:
            reasons_parts.append(f"in description: {', '.join(matched_in_description)}")
        reasons.append(f"skill match — {' | '.join(reasons_parts)}")

    if matched_skills:
        # More skill matches = higher score, capped at 25
        skill_score = min(len(matched_skills) * 8, 25)
        score += skill_score
        reasons.append(f"skill match: {', '.join(matched_skills)}")
    
    # ---- 3. TITLE MATCH (20 points) ----
    keyword_lower = job.get("keyword", "").lower()

    if keyword_lower and keyword_lower in title_lower:
        # Exact keyword match in title
        score += 20
        reasons.append(f"exact title match '{job['keyword']}'")
    else:
        # Partial match — some words from keyword appear in title
        keyword_words = keyword_lower.split()
        matches = sum(1 for word in keyword_words if word in title_lower)
        partial = int((matches / max(len(keyword_words), 1)) * 10)
        score += partial
        if partial > 0:
            reasons.append(f"partial title match ({matches} words)")

    # ---- 4. LOCATION MATCH (10 points) ----
    job_location = job.get("location", "").lower()

    for preferred_location in LOCATIONS:
        if preferred_location.lower() in job_location:
            score += 10
            reasons.append(f"location match '{preferred_location}'")
            break
    else:
        # Remote jobs get partial location points
        if "remote" in job_location or "home" in job_location:
            score += 5
            reasons.append("remote friendly")

    # ---- 5. COMPANY SIZE (5 points) ----
    company_lower = job.get("company", "").lower()

    for known_company in WELL_KNOWN_COMPANIES:
        if known_company in company_lower:
            score += 5
            reasons.append("well known company")
            break

    return score, reasons


def rank_and_filter_jobs(jobs, top_n=5):
    """
    Scores all jobs, sorts them by score,
    and returns the top N per portal.
    """

    print(f"\n  Scoring {len(jobs)} jobs...")

    # Score every job
    for job in jobs:
        job["score"], job["score_reasons"] = score_job(job)

    # Group by portal
    by_portal = {}
    for job in jobs:
        portal = job.get("portal", "Other")
        if portal not in by_portal:
            by_portal[portal] = []
        by_portal[portal].append(job)

    # Sort each portal's jobs by score and take top N
    top_jobs = []
    for portal, portal_jobs in by_portal.items():
        sorted_jobs = sorted(
            portal_jobs,
            key=lambda x: x["score"],
            reverse=True
        )
        top = sorted_jobs[:top_n]
        top_jobs.extend(top)

        # Show scoring summary in terminal
        print(f"\n  {portal} — top {len(top)} of {len(sorted_jobs)} jobs:")
        for job in top:
            print(f"    [{job['score']}/100] {job['title']}")
            print(f"           {' · '.join(job['score_reasons'])}")

    return top_jobs