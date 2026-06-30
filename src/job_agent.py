# =============================================
# JOB SEARCH AGENT
# Searches StepStone and Arbeitnow
# Saves results to output folder
# =============================================

import requests
from bs4 import BeautifulSoup
import json
import os
import time
from datetime import datetime
from langdetect import detect, LangDetectException
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import KEYWORDS, LOCATIONS, PORTALS, YOUR_EMAIL, LANGUAGES


# =============================================
# SEARCH STEPSTONE
# Uses English subdomain for international
# job listings only
# =============================================

def search_stepstone(keyword, location):
    """
    Searches StepStone's English subdomain for
    jobs matching the given keyword and location.
    """

    url = "https://www.stepstone.de/jobs/suche"

    params = {
        "q": keyword,
        "where": location,
        "sort": "date",
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.stepstone.de/",
    }

    jobs = []

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # APPROACH 1: Structured JSON data in page
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

        # APPROACH 2: Next.js embedded JSON
        if not jobs:
            next_data_tag = soup.find("script", id="__NEXT_DATA__")
            if next_data_tag:
                try:
                    next_data = json.loads(next_data_tag.string)
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

        # APPROACH 3: HTML fallback
        if not jobs:
            job_cards = soup.find_all("article")
            for card in job_cards:
                title_tag = card.find(["h2", "h3"])
                title = title_tag.get_text(strip=True) if title_tag else None
                if not title or len(title) < 5:
                    continue

                company = None
                for attr in ["data-company", "data-employer"]:
                    if card.get(attr):
                        company = card[attr].strip()
                        break

                if not company:
                    for tag in card.find_all(["span", "div", "p"]):
                        text = tag.get_text(strip=True)
                        if text and text != title and 3 < len(text) < 60:
                            for noise in ["Gehalt anzeigen", "Home-Office", "Teilweise",
                                         "Vollzeit", "Festanstellung", "Praktikum",
                                         "Berlin", "München", "Hamburg", "Stuttgart",
                                         "Frankfurt", "Köln", "Düsseldorf", "Remote"]:
                                text = text.replace(noise, "").strip()
                            if 3 < len(text) < 60:
                                company = text
                                break

                link = None
                for a_tag in card.find_all("a", href=True):
                    href = a_tag["href"]
                    if any(pattern in href for pattern in ["stellenangebote", "/job-", "/jobs/", "-job-"]):
                        link = href if href.startswith("http") else "https://www.stepstone.de" + href
                        break

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
# SEARCH ARBEITNOW
# Free official API — no key needed!
# =============================================

def search_arbeitnow(keyword, location):
    """
    Searches Arbeitnow's free official API.
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
        time.sleep(2)  # Avoid rate limiting
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
            language = item.get("language", "")

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
                "language": language,
                "date_found": datetime.now().strftime("%Y-%m-%d")
            })

    except Exception as e:
        print(f"  Could not reach Arbeitnow: {e}")

    return jobs


# =============================================
# SEARCH LINKEDIN VIA RAPIDAPI
# Free tier: 100 calls/month
# Re-enable on 1st of each month
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

        if response.status_code == 429:
            print("  LinkedIn: Monthly limit reached — resets 1st of next month")
            return []

        if response.status_code != 200:
            print(f"  LinkedIn: Unexpected status {response.status_code}")
            return []

        data = response.json()

        if not isinstance(data, list):
            print("  LinkedIn: Unexpected response format")
            return []

        for item in data:
            title = item.get("job_title", "").strip()
            if not title:
                continue

            company = item.get("company_name", "See listing").strip()
            job_location = item.get("job_location", location).strip()
            job_url = (
                item.get("linkedin_job_url_cleaned", "") or
                item.get("job_url", "")
            ).strip()
            description = item.get("job_description", "").strip()

            jobs.append({
                "title": title,
                "company": company,
                "location": job_location,
                "portal": "LinkedIn",
                "keyword": keyword,
                "link": job_url,
                "description": description,
                "date_found": datetime.now().strftime("%Y-%m-%d")
            })

    except Exception as e:
        print(f"  LinkedIn RapidAPI error: {e}")

    return jobs


# =============================================
# RUN ALL SEARCHES
# =============================================

def run_search():
    """
    Loops through all keywords and locations,
    searches each active portal, and returns
    all jobs found as one combined list.
    """

    print("\n" + "="*50)
    print("  JOB SEARCH AGENT STARTING...")
    print("="*50)

    all_jobs = []

    # ---- MAIN PORTALS: StepStone + Arbeitnow ----
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

    # ---- LINKEDIN — separate dedicated search ----
    # Uses smaller keyword/location list to preserve
    # free tier (100 calls/month). Re-enable on 1st July.
    if "linkedin" in PORTALS:
        from config.settings import LINKEDIN_KEYWORDS, LINKEDIN_LOCATIONS
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
# SAVE RESULTS TO FILE
# =============================================

def save_results(jobs):
    """
    Saves all found jobs to a JSON file
    in the output folder with today's date.
    """

    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"output/jobs_{today}.json"

    os.makedirs("output", exist_ok=True)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)

    print(f"\n  Results saved to: {filename}")
    return filename


# =============================================
# DISPLAY RESULTS IN TERMINAL
# =============================================

def display_results(jobs):
    """
    Prints all found jobs nicely in the terminal.
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
        print(f"     Score    : {job.get('ai_score', 'N/A')}/100 — {job.get('match_level', '')}")
        print(f"     Link     : {job['link']}")
        print(f"     Found on : {job['date_found']}")
        print("  " + "-"*45)


# =============================================
# RUN DIRECTLY
# =============================================

if __name__ == "__main__":
    jobs = run_search()
    display_results(jobs)
    save_results(jobs)
    print("\n  Done! Check your output folder for the full list.")
    print("="*50 + "\n")