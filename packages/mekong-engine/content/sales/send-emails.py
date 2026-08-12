#!/usr/bin/env python3
"""
OpenClaw RaaS Gateway — Email Sending Script
Send personalized outreach emails via Gmail SMTP or manual CSV export

Usage:
    python send-emails.py --mode manual     # Generate CSV for manual import
    python send-emails.py --mode smtp       # Send via Gmail SMTP (requires credentials)
"""

import csv
import smtplib
import argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

# Email template
EMAIL_TEMPLATE = """Hi {name},

I noticed {company} is building {product} — congrats on {milestone}!

I'm reaching out because we just launched OpenClaw RaaS Gateway, and I think it could help you:
• Reduce AI infrastructure costs by 50-80%
• Deploy AI agents in 5 minutes (not weeks)
• Only pay for actual AI executions (no idle waste)

We're looking for 10 design partners for our beta program. Would you be open to a 15-min chat this week?

Best,
{sender}

P.S. Free tier includes 10 MCU/month — no credit card required.
"""

SUBJECT_TEMPLATE = "Quick question about {company}'s AI deployment"

# Prospect data (50 prospects)
PROSPECTS = [
    {"name": "Anh", "company": "VinAI Labs", "product": "AI-powered logistics optimization", "milestone": "your recent partnership with Viettel", "email": "anh@vinai.io"},
    {"name": "Sarah", "company": "CodePilot", "product": "AI pair programming for enterprises", "milestone": "closing your Seed round", "email": "sarah@codepilot.io"},
    {"name": "Marcus", "company": "DataMind", "product": "AI analytics for SMBs", "milestone": "hitting 10K users", "email": "marcus@datamind.eu"},
    {"name": "Jennifer", "company": "MediBot", "product": "AI triage for clinics", "milestone": "your FDA breakthrough designation", "email": "jennifer@medibot.io"},
    {"name": "David", "company": "PaySmart", "product": "AI fraud detection for SEA markets", "milestone": "your Series A", "email": "david@paysmart.sg"},
    {"name": "Trang", "company": "LearnAI", "product": "personalized tutoring for Vietnamese students", "milestone": "partnering with MoET", "email": "trang@learnai.vn"},
    {"name": "Michael", "company": "ShopGenie", "product": "AI product recommendations", "milestone": "hitting $1M ARR", "email": "michael@shopgenie.io"},
    {"name": "Emma", "company": "LawBot", "product": "AI contract review for SMEs", "milestone": "your LawTech award", "email": "emma@lawbot.co.uk"},
    {"name": "Klaus", "company": "HireSmart", "product": "AI resume screening", "milestone": "expanding to 5 EU markets", "email": "klaus@hiresmart.de"},
    {"name": "Lisa", "company": "AdGenius", "product": "AI ad copy generation", "milestone": "your partnership with Shopify", "email": "lisa@adgenius.io"},
    {"name": "Alex", "company": "VoiceFlow AI", "product": "conversational voice agents", "milestone": "your YC acceptance", "email": "alex@voiceflow.ai"},
    {"name": "Sophie", "company": "DocumentAI", "product": "intelligent document processing", "milestone": "your enterprise pilot with ING", "email": "sophie@documentai.nl"},
    {"name": "Ryan", "company": "ChatBase", "product": "custom chatbots for SMBs", "milestone": "hitting 50K users", "email": "ryan@chatbase.io"},
    {"name": "Olivia", "company": "ImageGen Pro", "product": "AI image generation for marketers", "milestone": "your TechCrunch feature", "email": "olivia@imagegen.pro"},
    {"name": "James", "company": "CodeReview AI", "product": "automated code review", "milestone": "your partnership with GitHub", "email": "james@codereview.ai"},
    {"name": "Nathan", "company": "SalesBot", "product": "AI sales assistants", "milestone": "your first 100 enterprise customers", "email": "nathan@salesbot.io"},
    {"name": "Michelle", "company": "LegalMind", "product": "AI legal research", "milestone": "your partnership with TSMP Law", "email": "michelle@legalmind.sg"},
    {"name": "Priya", "company": "HealthAI", "product": "AI diagnostics for rural clinics", "milestone": "your Gates Foundation grant", "email": "priya@healthai.in"},
    {"name": "Emily", "company": "ContentCraft", "product": "AI content generation for agencies", "milestone": "hitting $500K ARR", "email": "emily@contentcraft.io"},
    {"name": "Pierre", "company": "DataBot", "product": "AI-powered business intelligence", "milestone": "your Series A from Partech", "email": "pierre@databot.fr"},
    {"name": "Carlos", "company": "SupportAI", "product": "AI customer support for LATAM", "milestone": "your expansion to 5 countries", "email": "carlos@supportai.br"},
    {"name": "Jessica", "company": "MeetingMind", "product": "AI meeting summaries", "milestone": "your partnership with Zoom", "email": "jessica@meetingmind.io"},
    {"name": "Thomas", "company": "RecruitAI", "product": "AI candidate matching", "milestone": "your partnership with Reed", "email": "thomas@recruitai.co.uk"},
    {"name": "Yuki", "company": "FinanceBot", "product": "AI financial planning", "milestone": "your license from JFSA", "email": "yuki@financebot.jp"},
    {"name": "Brandon", "company": "EmailAI", "product": "AI email optimization", "milestone": "hitting 1M emails processed", "email": "brandon@emailai.io"},
    {"name": "Noam", "company": "VideoGen", "product": "AI video generation", "milestone": "your partnership with Wix", "email": "noam@videogen.il"},
    {"name": "Maria", "company": "TranslateAI", "product": "real-time AI translation", "milestone": "supporting 50+ languages", "email": "maria@translateai.es"},
    {"name": "Robert", "company": "SecurityAI", "product": "AI threat detection", "milestone": "your SOC 2 certification", "email": "robert@securityai.io"},
    {"name": "Erik", "company": "DesignAI", "product": "AI UI design generation", "milestone": "your partnership with Figma", "email": "erik@designai.se"},
    {"name": "Amanda", "company": "InsightsAI", "product": "AI market research", "milestone": "your first Fortune 500 customer", "email": "amanda@insightsai.ca"},
    {"name": "Kevin", "company": "TestAI", "product": "AI test generation", "milestone": "your partnership with Jest", "email": "kevin@testai.io"},
    {"name": "Hans", "company": "WorkflowAI", "product": "AI workflow automation", "milestone": "hitting 500 enterprise customers", "email": "hans@workflowai.de"},
    {"name": "Rachel", "company": "CRM AI", "product": "AI-powered CRM", "milestone": "your partnership with Salesforce Ventures", "email": "rachel@crm-ai.au"},
    {"name": "Steven", "company": "DataClean", "product": "AI data cleaning", "milestone": "your enterprise tier launch", "email": "steven@dataclean.io"},
    {"name": "Linh", "company": "VoiceAI", "product": "Vietnamese voice recognition", "milestone": "your Vingroup partnership", "email": "linh@voiceai.vn"},
    {"name": "Daniel", "company": "AgentHub", "product": "multi-agent orchestration", "milestone": "your a16z investment", "email": "daniel@agenthub.io"},
    {"name": "Charlotte", "company": "DocuMind", "product": "AI document summarization", "milestone": "your partnership with LexisNexis", "email": "charlotte@documind.co.uk"},
    {"name": "Jan", "company": "PredictAI", "product": "predictive analytics", "milestone": "your partnership with Adyen", "email": "jan@predictai.nl"},
    {"name": "Wei", "company": "ChatFlow", "product": "conversational commerce", "milestone": "your Sea Limited partnership", "email": "wei@chatflow.sg"},
    {"name": "Patricia", "company": "AIOps", "product": "AI operations monitoring", "milestone": "your AWS partnership", "email": "patricia@aiops.io"},
    {"name": "Piotr", "company": "CodeAssist", "product": "AI code completion", "milestone": "your JetBrains partnership", "email": "piotr@codeassist.pl"},
    {"name": "Linda", "company": "SearchAI", "product": "semantic search", "milestone": "hitting 1B queries", "email": "linda@searchai.io"},
    {"name": "Antoine", "company": "FormAI", "product": "AI form processing", "milestone": "your partnership with DocuSign", "email": "antoine@formai.fr"},
    {"name": "Raj", "company": "AnalyticsAI", "product": "AI-powered analytics", "milestone": "your Sequoia India investment", "email": "raj@analyticsai.in"},
    {"name": "Felipe", "company": "NotifyAI", "product": "AI notifications", "milestone": "your partnership with WhatsApp", "email": "felipe@notifyai.br"},
    {"name": "Nicole", "company": "ScheduleAI", "product": "AI calendar optimization", "milestone": "your Google Calendar integration", "email": "nicole@scheduleai.io"},
    {"name": "Sofia", "company": "InvoiceAI", "product": "AI invoice processing", "milestone": "your BBVA partnership", "email": "sofia@invoiceai.mx"},
    {"name": "Gregory", "company": "ContractAI", "product": "AI contract analysis", "milestone": "your YC W25 batch", "email": "gregory@contractai.io"},
    {"name": "Min-jun", "company": "TrainAI", "product": "AI model fine-tuning", "milestone": "your Samsung Ventures investment", "email": "minjun@trainai.kr"},
    {"name": "Victoria", "company": "OptimizeAI", "product": "AI conversion optimization", "milestone": "your first 1000 A/B tests", "email": "victoria@optimizeai.io"},
]


def generate_manual_csv(output_file="email-send-manual.csv", sender_name="Your Name"):
    """Generate CSV for manual Gmail/Outlook import"""
    rows = []
    for i, p in enumerate(PROSPECTS, 1):
        subject = SUBJECT_TEMPLATE.format(company=p["company"])
        body = EMAIL_TEMPLATE.format(
            name=p["name"],
            company=p["company"],
            product=p["product"],
            milestone=p["milestone"],
            sender=sender_name
        )
        rows.append({
            "To": p["email"],
            "Subject": subject,
            "Body": body.replace("\n", "\\n"),
            "Sent Date": datetime.now().strftime("%Y-%m-%d"),
            "Status": "Draft"
        })

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["To", "Subject", "Body", "Sent Date", "Status"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {output_file} with {len(rows)} emails")
    print(f"Import this CSV into Gmail/Outlook or use mail merge")
    return output_file


def send_smtp_emails(sender_email, sender_password, sender_name="Your Name",
                     smtp_server="smtp.gmail.com", smtp_port=587, dry_run=True):
    """Send emails via Gmail SMTP"""

    sent_count = 0
    failed_count = 0

    for i, p in enumerate(PROSPECTS, 1):
        subject = SUBJECT_TEMPLATE.format(company=p["company"])
        body = EMAIL_TEMPLATE.format(
            name=p["name"],
            company=p["company"],
            product=p["product"],
            milestone=p["milestone"],
            sender=sender_name
        )

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = p["email"]
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        if dry_run:
            print(f"[DRY RUN] Would send to {p['email']}: {subject}")
            sent_count += 1
        else:
            try:
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(sender_email, sender_password)
                    server.send_message(msg)
                print(f"[SENT] {i}/50 - {p['email']}")
                sent_count += 1
            except Exception as e:
                print(f"[FAILED] {p['email']}: {str(e)}")
                failed_count += 1

        # Rate limiting: wait between emails
        if not dry_run:
            import time
            time.sleep(2)  # 2 seconds between emails

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Summary: {sent_count} sent, {failed_count} failed")
    return sent_count, failed_count


def update_tracking_csv(tracking_file="email-tracking.csv", sender_name="Your Name"):
    """Update the tracking CSV with sent status"""
    today = datetime.now().strftime("%Y-%m-%d")

    # Read existing tracking file
    rows = []
    with open(tracking_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["Sent Date"] = today
            row["Status"] = "Sent"
            rows.append(row)

    # Write back
    with open(tracking_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["#", "Name", "Company", "Email", "Sent Date", "Status", "Reply", "Notes"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        # Write header comment
        f.write("# OpenClaw RaaS Gateway — Email Tracking Sheet\n")
        f.write(f"# Updated: {today}\n\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Updated {tracking_file} with sent status")


def main():
    parser = argparse.ArgumentParser(description="Send OpenClaw outreach emails")
    parser.add_argument("--mode", choices=["manual", "smtp"], default="manual",
                       help="manual: Generate CSV for import, smtp: Send via Gmail")
    parser.add_argument("--sender", default="Your Name", help="Sender name")
    parser.add_argument("--email", help="Gmail address (for SMTP mode)")
    parser.add_argument("--password", help="Gmail app password (for SMTP mode)")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually send emails")

    args = parser.parse_args()

    print(f"OpenClaw RaaS Gateway — Email Sender")
    print(f"Mode: {args.mode}")
    print(f"Sender: {args.sender}")
    print(f"Total prospects: {len(PROSPECTS)}")
    print("-" * 50)

    if args.mode == "manual":
        output_file = generate_manual_csv(sender_name=args.sender)
        print(f"\nNext steps:")
        print(f"1. Open {output_file}")
        print(f"2. Import into Gmail/Outlook or use mail merge tool")
        print(f"3. Send in batches of 10 to avoid spam filters")
        print(f"4. Update email-tracking.csv with actual send status")
    else:
        if not args.email or not args.password:
            print("ERROR: SMTP mode requires --email and --password")
            print("For Gmail: Use App Password from https://myaccount.google.com/apppasswords")
            return 1

        if args.dry_run:
            print("DRY RUN MODE - No emails will be sent")

        send_smtp_emails(
            sender_email=args.email,
            sender_password=args.password,
            sender_name=args.sender,
            dry_run=args.dry_run
        )

        if not args.dry_run:
            update_tracking_csv(sender_name=args.sender)

    return 0


if __name__ == "__main__":
    exit(main())
