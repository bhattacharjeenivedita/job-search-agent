"""
India Job Agent — Mock Dry Run + Daily Email
- Replays saved results with no API calls
- Sends a formatted digest email via Gmail
- Run this to test email output before scheduling daily
"""

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


# ─────────────────────────────────────────────────────────────
# 1. EMAIL CONFIG — values come from your .env file
# ─────────────────────────────────────────────────────────────

GMAIL_ADDRESS  = os.getenv("YOUR_EMAIL", "your.email@gmail.com")
GMAIL_APP_PASS = os.getenv("EMAIL_PASSWORD", "")

# Recipients — add as many as you want
EMAIL_TO = [
    GMAIL_ADDRESS,                           # yourself by default
    # "friend@example.com",                  # uncomment to add more later
]

EMAIL_SUBJECT = "🎯 Your Daily India Job Digest — {date}"


# ─────────────────────────────────────────────────────────────
# 2. MOCK DATA — your real results pasted in
#    (swap this out for live Google Sheets data later)
# ─────────────────────────────────────────────────────────────

MOCK_RESULTS = [
    {
        "score": 9, "title": "Data Analyst", "company": "Credit Saison India",
        "location": "Bangalore, Karnataka", "salary": "Not disclosed",
        "summary": "Excellent fit due to extensive analytics experience in banking and financial services, strong SQL/Python skills, and quantitative education from ISI.",
        "matches": "Banking domain | SQL + Python | Bangalore location",
        "gaps": "None significant",
        "url": "https://www.adzuna.in",
        "date": datetime.now().strftime("%Y-%m-%d"),
    },
    {
        "score": 9, "title": "Data Analyst / Engineer", "company": "Kyndryl",
        "location": "Bangalore, Karnataka", "salary": "Not disclosed",
        "summary": "Strong fit for this hybrid role due to extensive background in enterprise data analytics, advanced SQL and Python expertise, and direct experience with automated ETL pipelines.",
        "matches": "ETL pipelines | SQL + Python | Enterprise analytics",
        "gaps": "Cloud platform experience not explicit",
        "url": "https://www.adzuna.in",
        "date": datetime.now().strftime("%Y-%m-%d"),
    },
    {
        "score": 9, "title": "Data Analyst – SQL/Power BI", "company": "Innover Digital",
        "location": "Bangalore, Karnataka", "salary": "Not disclosed",
        "summary": "Exceptional fit with extensive background in SQL, Power BI, data automation, and analytics across major global organizations.",
        "matches": "SQL | Power BI | Data automation",
        "gaps": "None significant",
        "url": "https://www.adzuna.in",
        "date": datetime.now().strftime("%Y-%m-%d"),
    },
    {
        "score": 9, "title": "Data Analyst", "company": "RECEX",
        "location": "Kolkata, West Bengal", "salary": "Not disclosed",
        "summary": "Exceptionally well-qualified with over eight years of data analysis, SQL expertise, and dashboard creation from top-tier financial and tech institutions.",
        "matches": "8+ years experience | SQL | Dashboards | Financial sector",
        "gaps": "Location — Kolkata vs current base",
        "url": "https://www.adzuna.in",
        "date": datetime.now().strftime("%Y-%m-%d"),
    },
    {
        "score": 8, "title": "Lead Data Analyst", "company": "Omnicom Media",
        "location": "Bangalore, Karnataka", "salary": "Not disclosed",
        "summary": "Strong fit with prior Lead Data Analyst experience and advanced quantitative skills, though domain background is banking rather than media and advertising.",
        "matches": "Lead analyst experience | Quantitative skills | Bangalore",
        "gaps": "Media/advertising domain",
        "url": "https://www.adzuna.in",
        "date": datetime.now().strftime("%Y-%m-%d"),
    },
    {
        "score": 8, "title": "Data Analyst", "company": "Cornerstone OnDemand",
        "location": "Pune, Maharashtra", "salary": "Not disclosed",
        "summary": "Strong fit due to extensive experience in data quality, data profiling, reference data management, and data governance using SQL and Python.",
        "matches": "Data quality | Data governance | SQL + Python",
        "gaps": "Location — Pune | Oracle ERP | Marketo",
        "url": "https://www.adzuna.in",
        "date": datetime.now().strftime("%Y-%m-%d"),
    },
    {
        "score": 8, "title": "Data Analyst", "company": "Millions Advisory",
        "location": "Pune, Maharashtra", "salary": "Not disclosed",
        "summary": "Strong fit with over eight years of analytics experience and deep expertise in Python and SQL, though lacks explicit Linux/Bash scripting experience.",
        "matches": "8+ years | Python + SQL | Analytics depth",
        "gaps": "Location — Pune | Linux/Bash scripting",
        "url": "https://www.adzuna.in",
        "date": datetime.now().strftime("%Y-%m-%d"),
    },
    {
        "score": 8, "title": "Data Analyst / Data Analytics", "company": "Aspyra HR Services",
        "location": "Pune, Maharashtra", "salary": "Not disclosed",
        "summary": "Strong fit due to extensive background in banking analytics, deep expertise in SQL and Hive, and dashboard creation experience, despite lacking explicit Tableau experience.",
        "matches": "Banking analytics | SQL + Hive | Dashboards",
        "gaps": "Tableau | Location — Pune",
        "url": "https://www.adzuna.in",
        "date": datetime.now().strftime("%Y-%m-%d"),
    },
    {
        "score": 7, "title": "Data Analyst", "company": "EXL",
        "location": "Pune, Maharashtra", "salary": "Not disclosed",
        "summary": "Strong analytical fit with deep banking experience and advanced SQL/Python skills, but lacks explicit PySpark and Credit & Lending subdomain experience.",
        "matches": "Banking domain | SQL + Python | Analytical depth",
        "gaps": "PySpark | Credit & Lending subdomain | Location — Pune",
        "url": "https://www.adzuna.in",
        "date": datetime.now().strftime("%Y-%m-%d"),
    },
    {
        "score": 6, "title": "Snowflake Data Analyst", "company": "Tata Consultancy Services",
        "location": "Bangalore, Karnataka", "salary": "Not disclosed",
        "summary": "Brings extensive data analysis experience and strong SQL skills, but lacks explicit hands-on Snowflake experience which is a core requirement.",
        "matches": "SQL | Data analysis | TCS prior history",
        "gaps": "Snowflake — core requirement missing",
        "url": "https://www.adzuna.in",
        "date": datetime.now().strftime("%Y-%m-%d"),
    },
]


# ─────────────────────────────────────────────────────────────
# BUILD EMAIL HTML
# ─────────────────────────────────────────────────────────────

def score_color(score):
    if score >= 9:
        return "#1a7f3c", "#d4edda"    # dark green text, light green bg
    elif score >= 7:
        return "#856404", "#fff3cd"    # amber
    else:
        return "#5a5a5a", "#f0f0f0"    # gray


def build_email_html(jobs: list) -> str:
    today      = datetime.now().strftime("%A, %d %B %Y")
    top_count  = len([j for j in jobs if j["score"] >= 9])
    good_count = len([j for j in jobs if j["score"] >= 7])

    # Pattern summary
    all_gaps = []
    for j in jobs:
        all_gaps += [g.strip() for g in j["gaps"].split("|") if g.strip() and g.strip().lower() != "none significant"]
    gap_counts = {}
    for g in all_gaps:
        gap_counts[g] = gap_counts.get(g, 0) + 1
    top_gaps = sorted(gap_counts.items(), key=lambda x: x[1], reverse=True)[:4]

    job_rows = ""
    for j in jobs:
        text_color, bg_color = score_color(j["score"])
        job_rows += f"""
        <tr>
          <td style="padding:16px;border-bottom:1px solid #e8e8e8;vertical-align:top;">
            <div style="display:flex;align-items:flex-start;gap:12px;">
              <span style="background:{bg_color};color:{text_color};font-weight:700;
                           font-size:18px;padding:6px 10px;border-radius:8px;
                           min-width:36px;text-align:center;display:inline-block;">
                {j["score"]}
              </span>
              <div style="flex:1;">
                <div style="font-weight:600;font-size:15px;color:#1a1a1a;">
                  {j["title"]}
                  <span style="font-weight:400;color:#666;font-size:13px;">
                    @ {j["company"]}
                  </span>
                </div>
                <div style="color:#888;font-size:12px;margin:3px 0 8px;">
                  📍 {j["location"]}
                  &nbsp;|&nbsp; 💰 {j["salary"]}
                </div>
                <div style="color:#333;font-size:13px;line-height:1.5;margin-bottom:8px;">
                  {j["summary"]}
                </div>
                <div style="font-size:12px;margin-bottom:4px;">
                  <span style="color:#1a7f3c;font-weight:600;">✓ Matches: </span>
                  <span style="color:#555;">{j["matches"]}</span>
                </div>
                <div style="font-size:12px;margin-bottom:10px;">
                  <span style="color:#c0392b;font-weight:600;">✗ Gaps: </span>
                  <span style="color:#555;">{j["gaps"]}</span>
                </div>
                <a href="{j["url"]}" style="background:#0a66c2;color:#fff;
                   text-decoration:none;padding:6px 14px;border-radius:6px;
                   font-size:12px;font-weight:600;display:inline-block;">
                  View Job →
                </a>
              </div>
            </div>
          </td>
        </tr>"""

    gap_pills = "".join(
        f'<span style="background:#fff3cd;color:#856404;padding:3px 10px;'
        f'border-radius:12px;font-size:12px;margin:3px;display:inline-block;">'
        f'{g} ({c}×)</span>'
        for g, c in top_gaps
    )

    return f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <div style="max-width:640px;margin:24px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

    <!-- Header -->
    <div style="background:#0a66c2;padding:28px 32px;">
      <div style="color:#fff;font-size:22px;font-weight:700;">🎯 Your Daily Job Digest</div>
      <div style="color:#cce0ff;font-size:14px;margin-top:4px;">{today}</div>
    </div>

    <!-- Summary bar -->
    <div style="background:#f0f7ff;padding:16px 32px;border-bottom:1px solid #e0ecff;
                display:flex;gap:32px;flex-wrap:wrap;">
      <div style="text-align:center;">
        <div style="font-size:28px;font-weight:700;color:#1a7f3c;">{top_count}</div>
        <div style="font-size:12px;color:#555;">Top matches (9-10)</div>
      </div>
      <div style="text-align:center;">
        <div style="font-size:28px;font-weight:700;color:#856404;">{good_count}</div>
        <div style="font-size:12px;color:#555;">Good matches (7+)</div>
      </div>
      <div style="text-align:center;">
        <div style="font-size:28px;font-weight:700;color:#333;">{len(jobs)}</div>
        <div style="font-size:12px;color:#555;">Total scored</div>
      </div>
    </div>

    <!-- Recurring gaps -->
    <div style="padding:16px 32px;background:#fffdf0;border-bottom:1px solid #f0e8c0;">
      <div style="font-size:12px;font-weight:600;color:#856404;margin-bottom:6px;">
        ⚠️ Skills appearing as gaps across roles — worth adding to your resume:
      </div>
      <div>{gap_pills}</div>
    </div>

    <!-- Job list -->
    <table style="width:100%;border-collapse:collapse;">
      {job_rows}
    </table>

    <!-- Footer -->
    <div style="padding:20px 32px;background:#f9f9f9;border-top:1px solid #eee;
                font-size:12px;color:#999;text-align:center;">
      Sent by your India Job Agent · Powered by Adzuna + Gemini
    </div>

  </div>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────
# SEND EMAIL
# ─────────────────────────────────────────────────────────────

def send_email(jobs: list, recipients: list, dry_run: bool = False):
    today   = datetime.now().strftime("%d %b %Y")
    subject = EMAIL_SUBJECT.format(date=today)
    html    = build_email_html(jobs)

    if dry_run:
        # Save to file so you can preview without sending
        with open("email_preview.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("✅ Dry run complete — open email_preview.html in your browser to see the email.")
        print(f"   Would send to: {', '.join(recipients)}")
        print(f"   Subject: {subject}")
        print(f"   Jobs in digest: {len(jobs)}")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = ", ".join(recipients)
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASS)
            server.sendmail(GMAIL_ADDRESS, recipients, msg.as_string())
        print(f"✅ Email sent to: {', '.join(recipients)}")
    except smtplib.SMTPAuthenticationError:
        print("❌ Gmail auth failed. Check your App Password — see SETUP.md Step 4.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")


# ─────────────────────────────────────────────────────────────
# MAIN — set dry_run=True to preview, False to actually send
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("  Job Digest — Mock Dry Run")
    print("=" * 50)

    # Sort by score
    jobs = sorted(MOCK_RESULTS, key=lambda x: x["score"], reverse=True)

    print(f"\n📋 Pattern summary:")
    scores = [j["score"] for j in jobs]
    print(f"   Scores: {scores}")
    print(f"   Average score: {sum(scores)/len(scores):.1f}/10")
    print(f"   Top matches (9+): {len([s for s in scores if s >= 9])}")
    print(f"   Good matches (7-8): {len([s for s in scores if 7 <= s < 9])}")
    print(f"   Borderline (6): {len([s for s in scores if s == 6])}")

    print(f"\n📧 Building email digest...")

    # Change to dry_run=False once you have Gmail App Password set up
    send_email(jobs, EMAIL_TO, dry_run=False)