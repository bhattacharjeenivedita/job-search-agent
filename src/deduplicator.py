# =============================================
# DEDUPLICATOR
# Tracks jobs seen across multiple days
# so you never see the same job twice
# =============================================

import json
import os
from datetime import datetime

SEEN_JOBS_FILE = "output/seen_jobs.json"


def load_seen_jobs():
    """
    Loads the list of job links we've
    already seen in previous runs.
    """
    if not os.path.exists(SEEN_JOBS_FILE):
        return set()

    with open(SEEN_JOBS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return set(data.get("seen_links", []))


def save_seen_jobs(seen_links):
    """
    Saves the updated list of seen job links
    back to the tracking file.
    """
    os.makedirs("output", exist_ok=True)
    with open(SEEN_JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "seen_links": list(seen_links),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M")
        }, f, indent=2)


def filter_new_jobs(jobs):
    """
    Removes any jobs we've already seen
    in previous runs. Updates the seen
    jobs file with today's new jobs.
    """

    seen_links = load_seen_jobs()
    new_jobs = []
    skipped = 0

    for job in jobs:
        link = job.get("link", "").strip()
        title_company = f"{job.get('title','').lower()}|{job.get('company','').lower()}"

        if link and link in seen_links:
            skipped += 1
            continue

        new_jobs.append(job)
        if link:
            seen_links.add(link)

    # Save updated seen jobs
    save_seen_jobs(seen_links)

    print(f"  Cross-day deduplication: {skipped} already seen, {len(new_jobs)} new jobs")
    return new_jobs