# =============================================
# YOUR JOB SEARCH SETTINGS
# Edit these to match what you're looking for
# =============================================

import os
from dotenv import load_dotenv

# Reads your secret .env file
load_dotenv()

# ---- PRIVATE SETTINGS (from .env file) ----

YOUR_EMAIL = os.getenv("YOUR_EMAIL", "your.email@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
YOUR_NAME = os.getenv("YOUR_NAME", "there")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")

# ---- JOB SEARCH CRITERIA ----

# Main keywords — used by StepStone and Arbeitnow
KEYWORDS = [
    "Data Analyst",
    "BI Analyst",
    "BI Developer",
    "Reporting Analyst",
]

# LinkedIn specific — kept small to preserve
# RapidAPI free tier (100 calls/month)
LINKEDIN_KEYWORDS = [
    "Data Analyst",
    "BI Analyst",
    "Power BI Developer",
]

# Main locations — used by StepStone and Arbeitnow
LOCATIONS = [
    "Remote",
    "Germany"
]

# LinkedIn specific locations — kept small
LINKEDIN_LOCATIONS = [
    "Germany",
    "Remote",
]

# Languages you want job listings in
LANGUAGES = [
    "English",
    "German",
]

# Your skills — add or remove anytime!
SKILLS = [
    # Programming
    "Python",
    "R",
    "SQL",
    # Data & Analytics
    "Data Analysis",
    "Data Analytics",
    "Power BI",
    "Excel",
    "Qlik",
    "QlikView",
    "QlikSense",
    # General
    "Reporting",
    "Dashboard",
    "Visualization",
]

# Job portals to search
PORTALS = [
    "stepstone",
    "arbeitnow",
]

# How many top jobs per portal in email
TOP_JOBS_PER_PORTAL = 5

# Daily digest send time (24hr format)
DIGEST_TIME = "08:00"

