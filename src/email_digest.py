# =============================================
# EMAIL DIGEST
# This script formats all found jobs into a
# beautiful HTML email and sends it to you
# =============================================

import smtplib
import json
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import YOUR_EMAIL, EMAIL_PASSWORD, YOUR_NAME


# =============================================
# STEP 1 — LOAD TODAY'S JOB RESULTS
# =============================================

def load_todays_jobs():
    """
    Reads today's saved job results from
    the output folder and returns them.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"output/jobs_{today}.json"

    if not os.path.exists(filename):
        print(f"  No results file found for today ({filename})")
        print("  Please run job_agent.py first!")
        return []

    with open(filename, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    print(f"  Loaded {len(jobs)} jobs from {filename}")
    return jobs


# =============================================
# STEP 2 — BUILD THE HTML EMAIL
# =============================================

def build_email_html(jobs):
    """
    Takes the list of jobs and builds a
    beautiful HTML email to send.
    """

    today_pretty = datetime.now().strftime("%A, %d %B %Y")
    total = len(jobs)

    # Group jobs by portal
    by_portal = {}
    for job in jobs:
        portal = job.get("portal", "Other")
        if portal not in by_portal:
            by_portal[portal] = []
        by_portal[portal].append(job)

    # Build the job rows HTML
    job_rows_html = ""
    for portal, portal_jobs in by_portal.items():
        # Portal header
        job_rows_html += f"""
        <tr>
            <td colspan="3" style="
                background-color: #1a56db;
                color: #ffffff;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
                letter-spacing: 0.05em;
            ">
                {portal.upper()} — {len(portal_jobs)} jobs
            </td>
        </tr>
        """

        # Job rows
        for i, job in enumerate(portal_jobs):
            bg = "#ffffff" if i % 2 == 0 else "#f8fafc"

            # AI score badge colour
            ai_score = job.get("ai_score", 0)
            match_level = job.get("match_level", "")
            why_good = job.get("why_good", "")
            why_not = job.get("why_not", "")
            skills = ", ".join(job.get("key_matching_skills", []))

            if ai_score >= 85:
                badge_bg = "#dcfce7"
                badge_color = "#166534"
            elif ai_score >= 70:
                badge_bg = "#dbeafe"
                badge_color = "#1e40af"
            elif ai_score >= 50:
                badge_bg = "#fef9c3"
                badge_color = "#854d0e"
            else:
                badge_bg = "#fee2e2"
                badge_color = "#991b1b"

            job_rows_html += f"""
            <tr style="background-color: {bg};">
                <td colspan="3" style="padding: 12px 16px; border-bottom: 1px solid #e2e8f0;">
                    <div style="display: flex; align-items: flex-start; justify-content: space-between; gap: 12px;">
                        <div style="flex: 1;">
                            <a href="{job['link']}" style="color: #1a56db; text-decoration: none; font-size: 14px; font-weight: 600;">
                                {job['title']}
                            </a>
                            <div style="font-size: 13px; color: #4a5568; margin-top: 2px;">
                                {job['company']} · {job['location']}
                            </div>
                            {f'<div style="font-size: 12px; color: #22543d; margin-top: 4px;">✓ {why_good}</div>' if why_good else ''}
                            {f'<div style="font-size: 12px; color: #744210; margin-top: 2px;">⚠ {why_not}</div>' if why_not else ''}
                            {f'<div style="font-size: 12px; color: #2b6cb0; margin-top: 2px;">🔧 {skills}</div>' if skills else ''}
                        </div>
                        <div style="text-align: center; min-width: 70px;">
                            <div style="background: {badge_bg}; color: {badge_color}; border-radius: 8px; padding: 4px 8px; font-size: 18px; font-weight: 700;">
                                {ai_score}
                            </div>
                            <div style="font-size: 10px; color: {badge_color}; margin-top: 2px;">{match_level}</div>
                        </div>
                    </div>
                </td>
            </tr>
            """

    # Full email HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; background-color: #f0f4f8; font-family: Arial, sans-serif;">

        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f0f4f8; padding: 32px 0;">
            <tr>
                <td align="center">
                    <table width="640" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">

                        <!-- HEADER -->
                        <tr>
                            <td style="background-color: #1a56db; padding: 32px; text-align: center;">
                                <p style="margin: 0; font-size: 13px; color: #bfdbfe; letter-spacing: 0.1em; text-transform: uppercase;">Daily Job Digest</p>
                                <h1 style="margin: 8px 0 0; font-size: 26px; color: #ffffff; font-weight: 700;">
                                    Good morning, {YOUR_NAME}! 👋
                                </h1>
                                <p style="margin: 8px 0 0; font-size: 14px; color: #bfdbfe;">{today_pretty}</p>
                            </td>
                        </tr>

                        <!-- SUMMARY BANNER -->
                        <tr>
                            <td style="background-color: #eff6ff; padding: 16px 32px; border-bottom: 1px solid #dbeafe;">
                                <p style="margin: 0; font-size: 15px; color: #1e40af; text-align: center;">
                                    🎯 Found <strong>{total} matching jobs</strong> across {len(by_portal)} portal(s) today
                                </p>
                            </td>
                        </tr>

                        <!-- JOB TABLE -->
                        <tr>
                            <td style="padding: 24px 32px;">
                                <table width="100%" cellpadding="0" cellspacing="0" style="border-radius: 8px; overflow: hidden; border: 1px solid #e2e8f0;">
                                    <!-- Table header -->
                                    <tr style="background-color: #f8fafc;">
                                        <th style="padding: 10px 16px; text-align: left; font-size: 12px; color: #718096; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 2px solid #e2e8f0;">Job Title</th>
                                        <th style="padding: 10px 16px; text-align: left; font-size: 12px; color: #718096; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 2px solid #e2e8f0;">Company</th>
                                        <th style="padding: 10px 16px; text-align: left; font-size: 12px; color: #718096; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 2px solid #e2e8f0;">Location</th>
                                    </tr>
                                    {job_rows_html}
                                </table>
                            </td>
                        </tr>

                        <!-- FOOTER -->
                        <tr>
                            <td style="background-color: #f8fafc; padding: 24px 32px; text-align: center; border-top: 1px solid #e2e8f0;">
                                <p style="margin: 0; font-size: 13px; color: #718096;">
                                    Sent by your Job Search Agent 🤖 — Good luck today!
                                </p>
                                <p style="margin: 6px 0 0; font-size: 12px; color: #a0aec0;">
                                    Results are saved in your output/ folder for reference.
                                </p>
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>

    </body>
    </html>
    """

    return html


# =============================================
# STEP 3 — SEND THE EMAIL
# =============================================

def send_email(html_content, job_count):
    """
    Sends the HTML email to your inbox
    using Gmail's SMTP server.
    """

    today_pretty = datetime.now().strftime("%d %B %Y")
    subject = f"🎯 {job_count} New Jobs Found — {today_pretty}"

    # Set up the email
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = YOUR_EMAIL
    msg["To"] = YOUR_EMAIL

    # Attach the HTML content
    msg.attach(MIMEText(html_content, "html"))

    try:
        print(f"\n  Connecting to Gmail...")
        # Connect to Gmail's SMTP server
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(YOUR_EMAIL, EMAIL_PASSWORD)
        server.sendmail(YOUR_EMAIL, YOUR_EMAIL, msg.as_string())
        server.quit()
        print(f"  Email sent successfully to {YOUR_EMAIL}! ✅")

    except Exception as e:
        print(f"  Could not send email: {e}")
        print("  Check your EMAIL and EMAIL_PASSWORD in the .env file.")


# =============================================
# RUN THE EMAIL DIGEST
# =============================================

if __name__ == "__main__":
    print("\n" + "="*50)
    print("  EMAIL DIGEST STARTING...")
    print("="*50)

    # Load today's jobs
    jobs = load_todays_jobs()

    if jobs:
        # Build the email
        print("\n  Building email...")
        html = build_email_html(jobs)

        # Send it
        send_email(html, len(jobs))
    else:
        print("\n  No jobs to send. Run job_agent.py first!")

    print("\n" + "="*50 + "\n")