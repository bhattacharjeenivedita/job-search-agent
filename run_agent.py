# =============================================
# MAIN RUNNER
# 1. Search all job portals
# 2. Deduplicate within run
# 3. Filter jobs seen in previous runs
# 4. Pre-filter with keyword scorer
# 5. Score top candidates with AI
# 6. Email top 5 per portal (score >= 60)
# =============================================

import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def load_jobs_from_file(filepath):
    """
    Loads previously saved raw jobs from a JSON file.
    """

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Jobs file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

from src.job_agent import run_search, display_results, save_results
from src.scorer import rank_and_filter_jobs, save_pre_filter_audit
from src.resume_scorer import score_all_jobs
from src.deduplicator import filter_new_jobs
from src.email_digest import load_todays_jobs, build_email_html, send_email
from config.settings import PROFILE, TOP_JOBS_PER_PORTAL

PRE_FILTER_LIMIT = PROFILE.get("pre_filter_limit", 15)
MIN_SCORE = PROFILE.get("min_score", 60)

USE_SAVED_JOBS = False  #True
#SAVED_JOBS_FILE = "output/jobs_2026-08-31.json"

print("\n" + "="*50)
print("  JOB SEARCH AGENT — DAILY RUN")
print(f"  {datetime.now().strftime('%A, %d %B %Y — %H:%M')}")
print("="*50)

# Step 1: Search all portals OR load saved jobs
if USE_SAVED_JOBS:
    print(f"\n📂 STEP 1: Loading saved jobs from {SAVED_JOBS_FILE}...")
    all_jobs = load_jobs_from_file(SAVED_JOBS_FILE)
    print(f"\n  Loaded {len(all_jobs)} raw jobs from saved file")
else:
    print("\n📡 STEP 1: Searching job portals...")
    all_jobs = run_search()
    save_results(all_jobs)
    print(f"\n  Total raw results: {len(all_jobs)} jobs")

# Step 2: Filter jobs seen in previous runs
print("\n🔄 STEP 2: Filtering already seen jobs...")
new_jobs = filter_new_jobs(all_jobs)
print(f"  {len(new_jobs)} genuinely new jobs today")

if not new_jobs:
    print("\n  No new jobs today — all already seen!")
    print("="*50 + "\n")
    exit()

# Step 3: Fast keyword pre-filter
print(f"\n⚡ STEP 3: Pre-filtering top {PRE_FILTER_LIMIT} candidates...")
pre_filtered = rank_and_filter_jobs(new_jobs, top_n=PRE_FILTER_LIMIT)
save_pre_filter_audit(new_jobs)
print(f"  {len(pre_filtered)} jobs selected for AI scoring")
for j in pre_filtered[:3]:  # Show first 3 as sample
    print(f"    Sample: {j.get('title','?')} | desc_len:{len(j.get('description',''))}")
for j in pre_filtered:
    print(f"    - [{j.get('score',0)}] {j['title']} | {j['portal']}")

# Step 4: Score with AI
print(f"\n🤖 STEP 4: Scoring with AI...")
top_jobs = score_all_jobs(pre_filtered, top_n=TOP_JOBS_PER_PORTAL, min_score=MIN_SCORE)

# Step 5: Display in terminal
display_results(top_jobs)

# Step 6: Send email
if top_jobs:
    print("\n📬 STEP 5: Sending email digest...")
    html = build_email_html(top_jobs)
    send_email(html, len(top_jobs))
    print(f"\n✅ Done! {len(top_jobs)} top matches sent to your inbox.")
else:
    print("\n  No jobs scored above the minimum threshold today - no email sent.")

print("="*50 + "\n")
