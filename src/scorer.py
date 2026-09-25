# =============================================
# JOB SCORER
# Ranks jobs based on your preferences:
# 1. Recency                            - 40 pts
# 2. Skill match                        - 25 pts
# 3. Title relevance and keyword match  - 20 pts
# 4. Location match                     - 10 pts
# 5. Company size                       -  5 pts
# Adds:
# - domain preference boost
# - mandatory non-matching domain reject
# - early filtering for irrelevant titles
# - penalty for missing descriptions
# =============================================

import os
import re
import sys
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import LOCATIONS, PROFILE, SKILLS

MIN_DESCRIPTION_CHARS = int(PROFILE.get("min_description_chars", 0))
EXCLUDED_TITLE_KEYWORDS = [
    value.lower() for value in PROFILE.get("excluded_title_keywords", [])
]

WELL_KNOWN_COMPANIES = [
    "bosch", "daimler", "mercedes", "bmw", "volkswagen", "sap", "siemens",
    "deutsche bank", "allianz", "bayer", "basf", "adidas", "porsche",
    "zalando", "delivery hero", "scout24", "henkel", "continental",
    "infineon", "fresenius", "munich re", "pwc", "deloitte", "kpmg",
    "mckinsey", "bcg", "accenture", "ibm", "microsoft", "google",
    "amazon", "meta", "apple", "oracle", "wipro", "infosys", "tcs",
    "hdfc", "icici", "axis bank", "cognizant", "capgemini", "ntt data"
]

POSITIVE_TITLE_KEYWORDS = [
    "senior data analyst",
    "data analyst",
    "business analyst",
    "bi analyst",
    "business intelligence",
    "reporting analyst",
    "power bi",
    "analytics",
    "dashboard",
    "reporting",
    "mis analyst",
    "data governance",
    "data quality"
]

NEGATIVE_TITLE_KEYWORDS = [
    "sales",
    "account executive",
    "account manager",
    "product manager",
    "architect",
    "devops",
    "private banking",
    "certification",
    "channel manager",
    "soc analyst",
    "security",
    "administrator",
    "software engineer",
    "recruiter",
    "marketing"
]

SOFT_NEGATIVE_TITLE_KEYWORDS = [
    "consultant",
    "manager",
    "specialist"
]

DOMAIN_PREFERENCES = [item.lower() for item in PROFILE.get("domain_preferences", [])]
STRICT_DOMAIN_MATCH_DOMAINS = [
    item.lower() for item in PROFILE.get("strict_domain_match_domains", [])
]
NON_MATCHING_DOMAIN_KEYWORDS = [
    item.lower() for item in PROFILE.get("non_matching_domain_keywords", [])
]


def has_soft_requirement_context(text, domain):
    """
    Returns True if the domain appears in a clearly non-mandatory context.
    """

    patterns = [
        rf"{re.escape(domain)}.{{0,60}}(?:preferred|nice to have|good to have|plus|desirable|optional|non[- ]mandatory|not mandatory|not required)",
        rf"(?:preferred|nice to have|good to have|plus|desirable|optional|non[- ]mandatory|not mandatory|not required).{{0,60}}{re.escape(domain)}",
    ]

    return any(re.search(pattern, text) for pattern in patterns)


def has_hard_requirement_context(text, domain):
    """
    Returns True if the domain appears in a clearly mandatory context.
    Soft contexts are checked first so 'non-mandatory' does not trigger.
    """

    if has_soft_requirement_context(text, domain):
        return False

    patterns = [
        rf"{re.escape(domain)}.{{0,60}}(?:required|must have|mandatory|essential)",
        rf"(?:required|must have|mandatory|essential).{{0,60}}{re.escape(domain)}",
        rf"(?:minimum|at least)\s+\d+\+?\s+years?.{{0,40}}{re.escape(domain)}",
        rf"\d+\+?\s+years?\s+of\s+experience.{{0,60}}{re.escape(domain)}",
        rf"(?:experience in|experience with|background in|prior experience in|proven experience in).{{0,60}}{re.escape(domain)}",
    ]

    return any(re.search(pattern, text) for pattern in patterns)


def detect_mandatory_non_matching_domain(description_text):
    """
    Detects whether the job requires prior domain experience
    outside the candidate's scope.
    """

    mandatory_non_matching_domains = []

    for domain in NON_MATCHING_DOMAIN_KEYWORDS:
        if domain not in description_text:
            continue

        if domain in STRICT_DOMAIN_MATCH_DOMAINS:
            continue

        if has_hard_requirement_context(description_text, domain):
            mandatory_non_matching_domains.append(domain)

    return mandatory_non_matching_domains


def location_matches(job_location):
    """Return whether a job explicitly matches a configured location or remote preference."""

    normalized_location = job_location.lower()

    for preferred_location in LOCATIONS:
        preferred = preferred_location.lower().strip()
        if not preferred:
            continue
        if preferred == "remote" and "remote" in normalized_location:
            return True
        if preferred != "remote" and preferred in normalized_location:
            return True

    return False


def score_job(job):
    """
    Gives each job a score out of 100 based on
    ranking preferences and title relevance.
    """

    score = 0
    reasons = []

    title_lower = job.get("title", "").lower()
    description_lower = job.get("description", "").lower()
    keyword_lower = job.get("keyword", "").lower()
    job_location = job.get("location", "").lower()
    company_lower = job.get("company", "").lower()

    combined_text = f"{title_lower} {description_lower} {company_lower}"

    if not location_matches(job_location):
        reasons.append("location does not match the configured target locations")
        return 0, reasons, True

    excluded_title_hits = [
        keyword for keyword in EXCLUDED_TITLE_KEYWORDS if keyword in title_lower
    ]
    if excluded_title_hits:
        reasons.append(f"excluded seniority/title signal: {', '.join(excluded_title_hits)}")
        return 0, reasons, True

    if len(description_lower.strip()) < MIN_DESCRIPTION_CHARS:
        reasons.append(
            f"insufficient description for reliable scoring ({len(description_lower.strip())}/{MIN_DESCRIPTION_CHARS} characters)"
        )
        return 0, reasons, True

    positive_title_hits = [
        keyword for keyword in POSITIVE_TITLE_KEYWORDS
        if keyword in title_lower
    ]
    negative_title_hits = [
        keyword for keyword in NEGATIVE_TITLE_KEYWORDS
        if keyword in title_lower
    ]
    soft_negative_hits = [
        keyword for keyword in SOFT_NEGATIVE_TITLE_KEYWORDS
        if keyword in title_lower
    ]
    domain_hits = [
        domain for domain in DOMAIN_PREFERENCES
        if domain in combined_text
    ]

    mandatory_non_matching_domains = detect_mandatory_non_matching_domain(description_lower)

    if mandatory_non_matching_domains:
        reasons.append(
            f"mandatory non-matching domain requirement: {', '.join(mandatory_non_matching_domains)}"
        )
        return 0, reasons, True

    if negative_title_hits and not positive_title_hits:
        reasons.append(f"title penalty: {', '.join(negative_title_hits)}")
        return 0, reasons, True

    score += 40
    reasons.append("fresh listing")

    matched_in_title = [
        skill for skill in SKILLS
        if skill.lower() in title_lower
    ]
    matched_in_description = [
        skill for skill in SKILLS
        if skill.lower() in description_lower
        and skill not in matched_in_title
    ]

    if matched_in_title or matched_in_description:
        title_score = min(len(matched_in_title) * 10, 20)
        desc_score = min(len(matched_in_description) * 3, 5)
        skill_score = min(title_score + desc_score, 25)
        score += skill_score

        reasons_parts = []
        if matched_in_title:
            reasons_parts.append(f"in title: {', '.join(matched_in_title)}")
        if matched_in_description:
            reasons_parts.append(f"in description: {', '.join(matched_in_description)}")
        reasons.append(f"skill match - {' | '.join(reasons_parts)}")

    if keyword_lower and keyword_lower in title_lower:
        score += 20
        reasons.append(f"exact title match '{job.get('keyword', '')}'")
    else:
        keyword_words = keyword_lower.split()
        matches = sum(1 for word in keyword_words if word in title_lower)
        partial = int((matches / max(len(keyword_words), 1)) * 10)
        score += partial
        if partial > 0:
            reasons.append(f"partial title match ({matches} words)")

    if positive_title_hits:
        title_relevance_score = min(len(positive_title_hits) * 5, 15)
        score += title_relevance_score
        reasons.append(f"relevant title: {', '.join(positive_title_hits)}")

    if soft_negative_hits and not positive_title_hits:
        score -= 10
        reasons.append(f"soft title penalty: {', '.join(soft_negative_hits)}")

    if domain_hits:
        domain_score = min(len(domain_hits) * 4, 12)
        score += domain_score
        reasons.append(f"domain match: {', '.join(domain_hits)}")

    if not description_lower:
        score -= 15
        reasons.append("missing description")

    for preferred_location in LOCATIONS:
        if preferred_location.lower() in job_location:
            score += 10
            reasons.append(f"location match '{preferred_location}'")
            break

    for known_company in WELL_KNOWN_COMPANIES:
        if known_company in company_lower:
            score += 5
            reasons.append("well known company")
            break

    score = max(score, 0)
    return score, reasons, False


def rank_and_filter_jobs(jobs, top_n=30):
    """
    Scores all jobs, sorts them by score,
    and returns the top N per portal.
    """

    print(f"\n  Scoring {len(jobs)} jobs...")

    for job in jobs:
        score, reasons, hard_reject = score_job(job)
        job["score"] = score
        job["score_reasons"] = reasons
        job["hard_reject"] = hard_reject
        job["pre_filter_status"] = "rejected" if hard_reject else "eligible"

    by_portal = {}
    for job in jobs:
        portal = job.get("portal", "Other")
        if portal not in by_portal:
            by_portal[portal] = []
        by_portal[portal].append(job)

    top_jobs = []
    for portal, portal_jobs in by_portal.items():
        eligible_jobs = [job for job in portal_jobs if not job["hard_reject"]]
        rejected_jobs = [job for job in portal_jobs if job["hard_reject"]]
        sorted_jobs = sorted(
            eligible_jobs,
            key=lambda x: x["score"],
            reverse=True
        )
        top = sorted_jobs[:top_n]
        top_jobs.extend(top)
        selected_ids = {id(job) for job in top}
        for job in eligible_jobs:
            job["pre_filter_status"] = (
                "selected_for_ai" if id(job) in selected_ids
                else "eligible_below_pre_filter_limit"
            )

        print(f"\n  {portal} - top {len(top)} of {len(sorted_jobs)} eligible jobs:")
        for job in top:
            print(f"    [{job['score']}/100] {job['title']}")
            print(f"           {' | '.join(job['score_reasons'])}")
        if rejected_jobs:
            print(f"  {portal} - rejected {len(rejected_jobs)} jobs before AI scoring:")
            for job in rejected_jobs:
                print(f"    - {job['title']}: {' | '.join(job['score_reasons'])}")

    return top_jobs


def save_pre_filter_audit(jobs):
    """Save every pre-filter decision so the shortlist is explainable."""

    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs("output", exist_ok=True)
    audit_file = f"output/pre_filter_audit_{today}.json"

    with open(audit_file, "w", encoding="utf-8") as file:
        json.dump(
            sorted(jobs, key=lambda job: job.get("score", 0), reverse=True),
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(f"  Pre-filter audit saved: {audit_file}")
