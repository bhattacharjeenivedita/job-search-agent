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
from config.settings import KEYWORDS, LOCATIONS, PORTALS, YOUR_EMAIL, LANGUAGES


# =============================================
# STEP 1 — SEARCH STEPSTONE
# =============================================

def search_stepstone(keyword, location):
    """
    Searches StepStone for jobs matching
    the given keyword and location.
    Returns a list of job listings found.
    """

    url = "https://www.stepstone.de/jobs/suche"
    
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

