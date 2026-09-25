# =============================================
# YOUR JOB SEARCH SETTINGS
# Edit these to match what you're looking for
# =============================================

import json
import os
from dotenv import load_dotenv

# Reads your secret .env file
load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILE_PATH = os.path.join(BASE_DIR, "data", "profile.json")


def load_profile():
    """
    Loads the user profile from data/profile.json.
    """

    if not os.path.exists(PROFILE_PATH):
        raise FileNotFoundError(f"Profile file not found: {PROFILE_PATH}")

    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


PROFILE = load_profile()

# ---- PRIVATE SETTINGS (from .env file) ----

YOUR_EMAIL = os.getenv("YOUR_EMAIL", "your.email@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
YOUR_NAME = PROFILE.get("name", os.getenv("YOUR_NAME", "there"))
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama").strip().lower()
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate").strip()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

# ---- JOB SEARCH CRITERIA ----

# Main keywords — used by StepStone and Arbeitnow
KEYWORDS = PROFILE.get("target_roles", [])

# LinkedIn specific — kept small to preserve
# RapidAPI free tier (100 calls/month)
LINKEDIN_KEYWORDS = PROFILE.get("target_roles", [])

# Main locations — used by StepStone and Arbeitnow
LOCATIONS = PROFILE.get("target_locations", [])

# LinkedIn specific locations — kept small
LINKEDIN_LOCATIONS = PROFILE.get("linkedin_locations", PROFILE.get("target_locations", []))

# Languages you want job listings in
LANGUAGES = PROFILE.get("preferred_languages", ["English"])

# Your skills — add or remove anytime!
SKILLS = PROFILE.get("skills", [])

# Job portals to search
PORTALS = [
    "linkedin",
]

# How many top jobs per portal in email
TOP_JOBS_PER_PORTAL = PROFILE.get("top_jobs_per_portal", 5)

# Daily digest send time (24hr format)
DIGEST_TIME = "08:00"

