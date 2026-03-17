# =============================================
# MAIN RUNNER
# Run this file every morning to:
# 1. Search all job portals
# 2. Send you the email digest
# Just one command: python run_agent.py
# =============================================

import sys
import os
from datetime import datetime

# Make sure Python can find our src and config folders
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.job_agent import run_search, display_results, save_results
from src.email_digest import load_todays_jobs, build_email_html, send_email

print("\n" + "="*50)
print("  JOB SEARCH AGENT — DAILY RUN")
print(f"  {datetime.now().strftime('%A, %d %B %Y — %H:%M')}")
print("="*50)

# Step 1: Run the search and save results
print("\n📡 STEP 1: Searching job portals...")
jobs = run_search()
display_results(jobs)
save_results(jobs)

# Step 2: Send the email digest
print("\n📬 STEP 2: Sending email digest...")
jobs = load_todays_jobs()
if jobs:
    html = build_email_html(jobs)
    send_email(html, len(jobs))
else:
    print("  No jobs found to email.")

print("\n✅ All done! Check your inbox.")
print("="*50 + "\n")