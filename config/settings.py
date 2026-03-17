# =============================================
# YOUR JOB SEARCH SETTINGS
# Edit these to match what you're looking for
# =============================================

import os
from dotenv import load_dotenv

# This line reads your secret .env file
# and makes its values available to Python
load_dotenv()

# ---- PRIVATE SETTINGS (from .env file) ----

# Your email address
YOUR_EMAIL = os.getenv("YOUR_EMAIL", "your.email@gmail.com")

# Your email password
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")

# Your name
YOUR_NAME = os.getenv("YOUR_NAME", "there")


# ---- JOB SEARCH CRITERIA (safe to share) ----

# Job titles or keywords you want to search for
KEYWORDS = [
    "Data Analyst",
    "Business Intelligence",
    "Business Analyst",
]

# Locations you want to work in
LOCATIONS = [
    "Stuttgart",
    "Baden Württemberg",
    "Remote",
]

# Languages you want job listings in
LANGUAGES = [
    "English"
    
]

# Your skills — add or remove anytime!
# The agent will score jobs higher if they mention these
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

PORTALS = [
    "stepstone",
    "arbeitnow",
    "linkedin",
    "xing",
]

# How many top jobs to show per portal in the email
TOP_JOBS_PER_PORTAL = 5

# Your email address (where the daily digest gets sent)
YOUR_EMAIL = "bhattacharje.nivedita@gmail.com"

# What time to send the daily digest (24hr format)
DIGEST_TIME = "08:00"