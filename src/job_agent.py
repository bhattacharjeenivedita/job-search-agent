# =============================================
# JOB SEARCH AGENT
# This script searches job portals and
# collects matching job listings for you
# =============================================

import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import sys

# This line imports your settings from the config folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import KEYWORDS, LOCATIONS, PORTALS, YOUR_EMAIL, LANGUAGES, LINKEDIN_KEYWORDS, LINKEDIN_LOCATIONS


# =============================================
# STEP 1 — SEARCH STEPSTONE
# =============================================

def search_stepstone(keyword, location):
    """
    Searches StepStone for jobs matching
    the given keyword and location.
    Returns a list of job listings found.
    """

    # Use StepStone's English-specific subdomain
    # This targets international/English job listings only
    url = "https://www.stepstone.de/en/jobs/suche"

    params = {
        "q": keyword,
        "where": location,
        "sort": "date",
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    jobs = []

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # -----------------------------------------------
        # APPROACH 1: Read structured JSON data in page
        # This is the most reliable source of clean data
        # -----------------------------------------------
        script_tags = soup.find_all("script", type="application/ld+json")
        
        for script in script_tags:
            try:
                data = json.loads(script.string)
                items = []

                if isinstance(data, dict) and data.get("@type") == "JobPosting":
                    items = [data]
                elif isinstance(data, list):
                    items = [i for i in data if isinstance(i, dict) and i.get("@type") == "JobPosting"]

                for item in items:
                    title = item.get("title", "").strip()
                    if not title:
                        continue

                    company = item.get("hiringOrganization", {}).get("name", "").strip()
                    job_location = (
                        item.get("jobLocation", {})
                            .get("address", {})
                            .get("addressLocality", location)
                    )
                    job_url = item.get("url", "").strip()

                    # Make sure the link is a proper job URL
                    if job_url and not job_url.startswith("http"):
                        job_url = "https://www.stepstone.de" + job_url
                    if not job_url:
                        job_url = f"https://www.stepstone.de/jobs/{keyword.replace(' ', '-')}/in-{location.replace(' ', '-')}"

                    jobs.append({
                        "title": title,
                        "company": company if company else "See listing",
                        "location": job_location,
                        "portal": "StepStone",
                        "keyword": keyword,
                        "link": job_url,
                        "date_found": datetime.now().strftime("%Y-%m-%d")
                    })

            except Exception:
                continue

        # -----------------------------------------------
        # APPROACH 2: Look for Next.js / embedded JSON
        # StepStone often stores data in a __NEXT_DATA__
        # script tag — very rich source of job details
        # -----------------------------------------------
        if not jobs:
            next_data_tag = soup.find("script", id="__NEXT_DATA__")
            if next_data_tag:
                try:
                    next_data = json.loads(next_data_tag.string)
                    # Dig into the nested structure to find job listings
                    listings = (
                        next_data
                        .get("props", {})
                        .get("pageProps", {})
                        .get("searchResult", {})
                        .get("results", [])
                    )
                    for item in listings:
                        title = item.get("title", "").strip()
                        company = item.get("companyName", "").strip()
                        job_location = item.get("location", location).strip()
                        job_url = item.get("jobUrl", "") or item.get("url", "")

                        if not title:
                            continue

                        if job_url and not job_url.startswith("http"):
                            job_url = "https://www.stepstone.de" + job_url

                        jobs.append({
                            "title": title,
                            "company": company if company else "See listing",
                            "location": job_location,
                            "portal": "StepStone",
                            "keyword": keyword,
                            "link": job_url,
                            "date_found": datetime.now().strftime("%Y-%m-%d")
                        })
                except Exception:
                    pass

        # -----------------------------------------------
        # APPROACH 3: HTML fallback — read article cards
        # Used only if both JSON approaches find nothing
        # -----------------------------------------------
        if not jobs:
            job_cards = soup.find_all("article")
            for card in job_cards:

                # Get title
                title_tag = card.find(["h2", "h3"])
                title = title_tag.get_text(strip=True) if title_tag else None
                if not title or len(title) < 5:
                    continue

                # Get company — look for data attributes first
                company = None
                for attr in ["data-company", "data-employer"]:
                    if card.get(attr):
                        company = card[attr].strip()
                        break

                # If no data attribute, search child elements
                if not company:
                    for tag in card.find_all(["span", "div", "p"]):
                        text = tag.get_text(strip=True)
                        # Company names are usually short and different from the title
                        # We also strip any location/salary text that gets mixed in
                        if text and text != title and 3 < len(text) < 60:
                            # Clean up garbage text that sometimes gets appended
                            for noise in ["Gehalt anzeigen", "Home-Office", "Teilweise",
                                         "Vollzeit", "Festanstellung", "Praktikum",
                                         "Berlin", "München", "Hamburg", "Stuttgart",
                                         "Frankfurt", "Köln", "Düsseldorf", "Remote"]:
                                text = text.replace(noise, "").strip()
                            # If after cleaning it's still a reasonable length, use it
                            if 3 < len(text) < 60:
                                company = text
                                break

                # Get link — prefer direct job posting URLs over company pages
                link = None
                for a_tag in card.find_all("a", href=True):
                    href = a_tag["href"]
                    # A real job posting URL contains /stellenangebote-- or /job-
                    if any(pattern in href for pattern in [
                        "stellenangebote", "/job-", "/jobs/", "-job-"
                    ]):
                        link = href if href.startswith("http") else "https://www.stepstone.de" + href
                        break

                # Fallback: use the first link in the card if no job URL found
                if not link:
                    first_link = card.find("a", href=True)
                    if first_link:
                        href = first_link["href"]
                        link = href if href.startswith("http") else "https://www.stepstone.de" + href
                    else:
                        link = f"https://www.stepstone.de/jobs/{keyword.replace(' ', '-')}/in-{location.replace(' ', '-')}"

                jobs.append({
                    "title": title,
                    "company": company if company else "See listing",
                    "location": location,
                    "portal": "StepStone",
                    "keyword": keyword,
                    "link": link,
                    "date_found": datetime.now().strftime("%Y-%m-%d")
                })

    except Exception as e:
        print(f"  Could not reach StepStone: {e}")

    return jobs

# =============================================
# STEP 2 — SEARCH ALL PORTALS
# =============================================

# =============================================
# SEARCH ARBEITNOW
# Free official API — no key needed!
# Specialises in German & European jobs
# =============================================

def search_arbeitnow(keyword, location):
    """
    Searches Arbeitnow's free official API for
    jobs matching the given keyword and location.
    Returns clean structured data including
    full job descriptions for better skill matching.
    """

    url = "https://www.arbeitnow.com/api/job-board-api"

    params = {
        "q": keyword,
        "location": location,
    }

    headers = {
        "Accept": "application/json",
        "User-Agent": "JobSearchAgent/1.0",
    }

    jobs = []

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"  Arbeitnow: unexpected status {response.status_code}")
            return jobs

        data = response.json()
        listings = data.get("data", [])

        for item in listings:
            title = item.get("title", "").strip()
            if not title:
                continue

            company = item.get("company_name", "See listing").strip()
            job_location = item.get("location", location).strip()
            job_url = item.get("url", "").strip()
            description = item.get("description", "").strip()
            remote = item.get("remote", False)

            # If remote flag is set, note it in location
            if remote and "remote" not in job_location.lower():
                job_location = f"{job_location} (Remote)"

            jobs.append({
                "title": title,
                "company": company,
                "location": job_location,
                "portal": "Arbeitnow",
                "keyword": keyword,
                "link": job_url,
                "description": description,
                "date_found": datetime.now().strftime("%Y-%m-%d")
            })

    except Exception as e:
        print(f"  Could not reach Arbeitnow: {e}")

    return jobs

# =============================================
# LANGUAGE FILTER
# Detects job language and rejects:
# 1. Jobs written in German
# 2. Jobs that require German as a skill
# =============================================

from langdetect import detect, LangDetectException

def is_english_friendly(job):
    """
    Returns True only if:
    - The job is written in English
    - AND does not require German language skills
    """
    title = job.get("title", "")
    description = job.get("description", "").lower()
    title_lower = title.lower()

    # CHECK 1: Arbeitnow language field — trust completely
    language = job.get("language", "")
    if language:
        return language.lower() == "en"

    # CHECK 2: Detect language of description
    if description and len(description) > 50:
        try:
            detected = detect(description)
            if detected != "en":
                return False
        except LangDetectException:
            pass

    # CHECK 3: Detect language of title
    if title and len(title) > 5:
        try:
            detected = detect(title)
            if detected == "de":
                return False
        except LangDetectException:
            pass

    # CHECK 4: German required phrases
    german_required_phrases = [
        "german language required", "german is required",
        "fluent in german", "fluent german", "native german",
        "german speaker", "german proficiency",
        "c1 german", "c2 german", "b2 german",
        "deutschkenntnisse", "deutsch- und englisch",
        "sehr gute deutschkenntnisse", "gute deutschkenntnisse",
        "fließende deutschkenntnisse", "verhandlungssicheres deutsch",
        "deutsch in wort und schrift", "deutsche sprachkenntnisse",
    ]
    for phrase in german_required_phrases:
        if phrase in description or phrase in title_lower:
            return False

    return True


# =============================================
# SEARCH EUROJOBS
# English-first portal with strong Germany
# coverage — very scraper friendly!
# =============================================

def search_eurojobs(keyword, location):
    """
    Searches EuroJobs for English language jobs
    in Germany matching keyword and location.
    """

    url = "https://www.eurojobs.com/search-results"

    params = {
        "keywords": keyword,
        "location": location,
        "country": "Germany",
        "action": "search",
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-GB,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    jobs = []

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # EuroJobs job cards
        job_cards = (
            soup.find_all("div", class_=lambda x: x and "job" in (x or "").lower() and "card" in (x or "").lower()) or
            soup.find_all("li", class_=lambda x: x and "job" in (x or "").lower()) or
            soup.find_all("article")
        )

        for card in job_cards:
            # Get title
            title_tag = (
                card.find(["h2", "h3", "h4"]) or
                card.find("a", class_=lambda x: x and "title" in (x or "").lower())
            )
            title = title_tag.get_text(strip=True) if title_tag else None
            if not title or len(title) < 5:
                continue

            # Get company
            company_tag = card.find(["span", "div", "p"],
                class_=lambda x: x and "company" in (x or "").lower())
            company = company_tag.get_text(strip=True) if company_tag else "See listing"

            # Get link
            link_tag = card.find("a", href=True)
            if link_tag:
                href = link_tag["href"]
                link = href if href.startswith("http") else "https://www.eurojobs.com" + href
            else:
                link = url

            jobs.append({
                "title": title,
                "company": company,
                "location": location,
                "portal": "EuroJobs",
                "keyword": keyword,
                "link": link,
                "date_found": datetime.now().strftime("%Y-%m-%d")
            })

    except Exception as e:
        print(f"  Could not reach EuroJobs: {e}")

    return jobs


# =============================================
# SEARCH LINKEDIN
# Largest professional network — note that
# LinkedIn has strong bot protection so
# results may be limited
# =============================================

def search_linkedin(keyword, location):
    """
    Searches LinkedIn jobs for matching listings.
    Uses the public jobs search page — no login needed.
    Note: LinkedIn may block scraping attempts.
    """

    import time
    import random

    # LinkedIn's public job search URL — no login required
    url = "https://www.linkedin.com/jobs/search"

    params = {
        "keywords": keyword,
        "location": location,
        "f_TPR": "r86400",   # Posted in last 24 hours
        "sortBy": "DD",       # Sort by date
        "f_WT": "2",          # Remote friendly
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.linkedin.com/",
    }

    jobs = []

    try:
        # Small delay to appear more human
        time.sleep(random.uniform(2, 4))

        response = requests.get(url, params=params, headers=headers, timeout=15)

        if response.status_code in [403, 429, 999]:
            print(f"  LinkedIn: access blocked (status {response.status_code})")
            return jobs

        soup = BeautifulSoup(response.text, "html.parser")

        # LinkedIn job cards on public search page
        job_cards = (
            soup.find_all("div", class_=lambda x: x and "base-card" in (x or "")) or
            soup.find_all("li", class_=lambda x: x and "jobs-search" in (x or "")) or
            soup.find_all("div", class_=lambda x: x and "job-search-card" in (x or ""))
        )

        for card in job_cards:
            # Get title
            title_tag = (
                card.find("h3", class_=lambda x: x and "base-search-card__title" in (x or "")) or
                card.find("h3") or
                card.find("h4")
            )
            title = title_tag.get_text(strip=True) if title_tag else None
            if not title or len(title) < 5:
                continue

            # Get company
            company_tag = (
                card.find("h4", class_=lambda x: x and "base-search-card__subtitle" in (x or "")) or
                card.find("a", class_=lambda x: x and "hidden-nested-link" in (x or ""))
            )
            company = company_tag.get_text(strip=True) if company_tag else "See listing"

            # Get location
            location_tag = card.find("span", class_=lambda x: x and "job-search-card__location" in (x or ""))
            job_location = location_tag.get_text(strip=True) if location_tag else location

            # Get link
            link_tag = card.find("a", href=True)
            if link_tag:
                href = link_tag["href"]
                # Clean up LinkedIn tracking parameters
                link = href.split("?")[0] if "?" in href else href
                if not link.startswith("http"):
                    link = "https://www.linkedin.com" + link
            else:
                link = url

            jobs.append({
                "title": title,
                "company": company,
                "location": job_location,
                "portal": "LinkedIn",
                "keyword": keyword,
                "link": link,
                "date_found": datetime.now().strftime("%Y-%m-%d")
            })

    except Exception as e:
        print(f"  Could not reach LinkedIn: {e}")

    return jobs

# =============================================
# SEARCH XING
# =============================================

def search_xing(keyword, location):
    """
    Searches Xing jobs for matching listings.
    Fetches each job page to get description
    for accurate language detection.
    """

    import time
    import random
    from langdetect import detect, LangDetectException

    url = "https://www.xing.com/en/jobs/search"

    params = {
        "keywords": keyword,
        "location": location,
        "radius": "50",
        "publishedAt": "7",
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.xing.com/",
    }

    jobs = []

    try:
        time.sleep(random.uniform(2, 4))
        response = requests.get(url, params=params, headers=headers, timeout=15)

        if response.status_code in [403, 429, 999]:
            print(f"  Xing: access blocked (status {response.status_code})")
            return jobs

        soup = BeautifulSoup(response.text, "html.parser")

        # Try multiple card selectors
        job_cards = (
            soup.find_all("div", class_=lambda x: x and "job-listing" in (x or "").lower()) or
            soup.find_all("article", class_=lambda x: x and "job" in (x or "").lower()) or
            soup.find_all("li", class_=lambda x: x and "job" in (x or "").lower()) or
            soup.find_all("div", attrs={"data-testid": lambda x: x and "job" in (x or "").lower()})
        )

        for card in job_cards:
            # Get title — keep (m/w/d) as it appears in both languages
            title_tag = (
                card.find(["h2", "h3", "h4"]) or
                card.find("a", class_=lambda x: x and "title" in (x or "").lower())
            )
            title = title_tag.get_text(strip=True) if title_tag else None
            if not title or len(title) < 5:
                continue

            # Get company
            company_tag = card.find(
                ["span", "div", "p"],
                class_=lambda x: x and "company" in (x or "").lower()
            )
            company = company_tag.get_text(strip=True) if company_tag else "See listing"

            # Get link
            link_tag = card.find("a", href=True)
            if link_tag:
                href = link_tag["href"]
                link = href if href.startswith("http") else "https://www.xing.com" + href
            else:
                link = url

            # ---- FETCH JOB PAGE FOR DESCRIPTION ----
            # We visit each job page to get the full description
            # so langdetect has enough text to work accurately
            description = ""
            try:
                time.sleep(random.uniform(0.5, 1.5))
                job_response = requests.get(
                    link, headers=headers, timeout=10
                )
                job_soup = BeautifulSoup(job_response.text, "html.parser")

                # Try common description containers
                # Remove sidebar and navigation elements first
                # so langdetect only reads the actual job content
                for tag in job_soup.find_all([
                    "nav", "footer", "header", "aside",
                ]):
                    tag.decompose()

                # Also remove similar jobs sections
                for tag in job_soup.find_all(
                    "div", class_=lambda x: x and any(
                        word in (x or "").lower() for word in [
                            "similar", "related", "recommended",
                            "sidebar", "navigation", "footer",
                        ]
                    )
                ):
                    tag.decompose()

                # Now find the actual job description
                desc_tag = (
                    job_soup.find("div", class_=lambda x: x and "description" in (x or "").lower()) or
                    job_soup.find("div", class_=lambda x: x and "job-description" in (x or "").lower()) or
                    job_soup.find("section", class_=lambda x: x and "description" in (x or "").lower()) or
                    job_soup.find("div", attrs={"data-testid": "job-description"}) or
                    job_soup.find("main")
                )
                if desc_tag:
                    description = desc_tag.get_text(strip=True)
                elif job_soup.find("body"):
                    # Last resort — use body text after sidebar removal
                    description = job_soup.find("body").get_text(strip=True)


            except Exception:
                pass

            # ---- DETECT LANGUAGE ----
            # If we couldn't fetch a description (desc_len=0),
            # don't filter by language — we don't have enough
            # text to make a reliable decision.
            # Only filter if title is clearly German.

            if len(description) > 100:
                # We have a description — use ratio check
                text_to_check = description.lower()

                english_words = [
                    " the ", " and ", " your ", " you ", " our ", " we ",
                    " will ", " with ", " for ", " are ", " have ", " this ",
                    " that ", " from ", " as ", " an ", " be ", " or ",
                    "experience", "skills", "team", "role", "position",
                    "opportunity", "working", "responsibilities", "requirements",
                    "benefits", "company", "join", "about", "apply",
                ]
                german_words = [
                    " die ", " der ", " das ", " und ", " sie ", " wir ",
                    " mit ", " für ", " ist ", " sind ", " wird ", " haben ",
                    " ihre ", " unser ", " eine ", " einen ", " einem ",
                    "aufgaben", "kenntnisse", "erfahrung", "anforderungen",
                    "stellenangebot", "bewerbung", "arbeitszeit", "gehalt",
                ]

                english_count = sum(1 for w in english_words if w in text_to_check)
                german_count = sum(1 for w in german_words if w in text_to_check)

                if german_count > english_count:
                    continue

            else:
                # No description available — check title only
                # Only reject if title contains clearly German words
                clearly_german_title_words = [
                    "leiter", "leiterin", "mitarbeiter", "mitarbeiterin",
                    "entwickler", "entwicklerin", "berater", "beraterin",
                    "sachbearbeiter", "kaufmann", "kauffrau", "ingenieur",
                    "projektleiter", "teamleiter", "referent", "referentin",
                    "koordinator", "fachkraft", "werkstudent", "praktikant",
                ]
                title_lower = title.lower()
                if any(word in title_lower for word in clearly_german_title_words):
                    continue
                # Otherwise keep the job — better to include than miss

                jobs.append({
                "title": title,
                "company": company,
                "location": location,
                "portal": "Xing",
                "keyword": keyword,
                "link": link,
                "description": description,
                "date_found": datetime.now().strftime("%Y-%m-%d")
            })

    except Exception as e:
        print(f"  Could not reach Xing: {e}")

    return jobs

# =============================================
# SEARCH LINKEDIN VIA RAPIDAPI
# Uses RapidAPI's free LinkedIn Jobs scraper
# 100 free calls/month
# =============================================

# =============================================
# SEARCH LINKEDIN VIA RAPIDAPI
# =============================================

def search_linkedin_rapidapi(keyword, location):
    """
    Searches LinkedIn jobs via RapidAPI.
    Free tier: 100 calls/month.
    """

    from config.settings import RAPIDAPI_KEY

    if not RAPIDAPI_KEY:
        print("  LinkedIn: No RapidAPI key found — skipping")
        return []

    url = "https://linkedin-jobs-search.p.rapidapi.com/"

    payload = {
        "search_terms": keyword,
        "location": location,
        "page": "1"
    }

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "linkedin-jobs-search.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    jobs = []

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)

        if response.status_code == 403:
            print("  LinkedIn: Not subscribed or limit reached")
            return []

        if response.status_code != 200:
            print(f"  LinkedIn: Unexpected status {response.status_code}")
            return []

        data = response.json()

        if not isinstance(data, list):
            print(f"  LinkedIn: Unexpected response format")
            return []

        for item in data:
            title = item.get("job_title", "").strip()
            if not title:
                continue

            company = item.get("company_name", "See listing").strip()
            job_location = item.get("job_location", location).strip()

            # Use cleaned URL if available
            job_url = (
                item.get("linkedin_job_url_cleaned", "") or
                item.get("job_url", "")
            ).strip()

            description = item.get("job_description", "").strip()
            posted_date = item.get("posted_date", "").strip()

            jobs.append({
                "title": title,
                "company": company,
                "location": job_location,
                "portal": "LinkedIn",
                "keyword": keyword,
                "link": job_url,
                "description": description,
                "posted_date": posted_date,
                "date_found": datetime.now().strftime("%Y-%m-%d")
            })

    except Exception as e:
        print(f"  LinkedIn RapidAPI error: {e}")

    return jobs

def run_search():
    """
    Loops through all your keywords and locations
    and searches each active portal.
    Returns all jobs found as one combined list.
    """

    print("\n" + "="*50)
    print("  JOB SEARCH AGENT STARTING...")
    print("="*50)

    all_jobs = []

    for keyword in KEYWORDS:
        for location in LOCATIONS:
            print(f"\n  Searching: '{keyword}' in '{location}'...")

            if "stepstone" in PORTALS:
                results = search_stepstone(keyword, location)
                print(f"  StepStone: {len(results)} jobs found")
                all_jobs.extend(results)
                
            if "arbeitnow" in PORTALS:
                results = search_arbeitnow(keyword, location)
                print(f"  Arbeitnow: {len(results)} jobs found")
                all_jobs.extend(results)

            
            if "xing" in PORTALS:
                results = search_xing(keyword, location)
                print(f"  Xing: {len(results)} jobs found")
                all_jobs.extend(results)

            # ---- LINKEDIN — uses separate smaller keyword/location list ----
            # to preserve RapidAPI free tier (100 calls/month)
            if "linkedin" in PORTALS:
                print(f"\n  Searching LinkedIn with dedicated keywords...")
                for lkeyword in LINKEDIN_KEYWORDS:
                    for llocation in LINKEDIN_LOCATIONS:
                        print(f"\n  LinkedIn: '{lkeyword}' in '{llocation}'...")
                        results = search_linkedin_rapidapi(lkeyword, llocation)
                        print(f"  LinkedIn: {len(results)} jobs found")
                        all_jobs.extend(results)



    print(f"\n  Total jobs found: {len(all_jobs)}")
    return all_jobs


# =============================================
# STEP 3 — SAVE RESULTS TO A FILE
# =============================================

def save_results(jobs):
    """
    Saves all found jobs to a JSON file
    in the output folder with today's date.
    """

    # Create filename with today's date
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"output/jobs_{today}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)

    print(f"\n  Results saved to: {filename}")
    return filename


# =============================================
# STEP 4 — DISPLAY RESULTS IN TERMINAL
# =============================================

def display_results(jobs):
    """
    Prints all found jobs nicely in the terminal
    so you can see them right away.
    """

    print("\n" + "="*50)
    print("  TODAY'S JOB LISTINGS")
    print("="*50)

    if not jobs:
        print("\n  No jobs found. Try different keywords or locations.")
        return

    for i, job in enumerate(jobs, 1):
        print(f"\n  {i}. {job['title']}")
        print(f"     Company  : {job['company']}")
        print(f"     Location : {job['location']}")
        print(f"     Portal   : {job['portal']}")
        print(f"     Link     : {job['link']}")
        print(f"     Found on : {job['date_found']}")
        print("  " + "-"*45)


# =============================================
# RUN THE AGENT
# =============================================

if __name__ == "__main__":
    # Step 1: Search all portals
    jobs = run_search()

    # Step 2: Show results in terminal
    display_results(jobs)

    # Step 3: Save results to output folder
    save_results(jobs)

    print("\n  Done! Check your output folder for the full list.")
    print("="*50 + "\n")

