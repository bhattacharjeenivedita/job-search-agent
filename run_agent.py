# =============================================
# MAIN RUNNER
# Run this every morning to:
# 1. Search all job portals
# 2. Score and rank results
# 3. Send top 5 per portal by email
# =============================================

import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.job_agent import run_search, display_results, save_results
from src.scorer import rank_and_filter_jobs
from src.email_digest import load_todays_jobs, build_email_html, send_email
from config.settings import TOP_JOBS_PER_PORTAL

print("\n" + "="*50)
print("  JOB SEARCH AGENT — DAILY RUN")
print(f"  {datetime.now().strftime('%A, %d %B %Y — %H:%M')}")
print("="*50)

# Step 1: Search all portals
print("\n📡 STEP 1: Searching job portals...")
all_jobs = run_search()
save_results(all_jobs)
print(f"\n  Total raw results: {len(all_jobs)} jobs")

# Step 2: Score and filter to top N per portal
print(f"\n🏆 STEP 2: Ranking and filtering to top {TOP_JOBS_PER_PORTAL} per portal...")
top_jobs = rank_and_filter_jobs(all_jobs, top_n=TOP_JOBS_PER_PORTAL)
print(f"  Kept {len(top_jobs)} top jobs for your digest")

# Step 3: Display top jobs in terminal
display_results(top_jobs)

# Step 4: Send email with top jobs only
print("\n📬 STEP 3: Sending email digest...")
html = build_email_html(top_jobs)
send_email(html, len(top_jobs))

print("\n✅ All done! Check your inbox for your top picks.")
print("="*50 + "\n")