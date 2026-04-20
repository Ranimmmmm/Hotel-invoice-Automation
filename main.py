# main.py
import os
import time
import argparse

from dotenv import load_dotenv
import pandas as pd

from config import (
    DEFAULT_HOTEL_COL,
    DEFAULT_CLIENT_COL,
    DEFAULT_DUE_COL,
    DEFAULT_TO_COL,
)
from excel_reader import read_sheet
from utils import init_log, log_result

# Search & scraping helpers
from utils import (
    google_cse_find_site,
    find_emails_for_website,
    is_blacklisted,
)

# Mail options
from web_outlook import open_outlook_web_email  # Outlook on the web (opens compose tab)
from smtp_mailer import send_smtp_email

def build_german_email(hotel_name: str, client_name: str, duration: str, sender_name: str):
    subject = f"Rechnung (NFI) – {client_name}"
    # Plain-text body; open_outlook_web_email will URL-encode it
    body = (
        f"Sehr geehrtes Team des {hotel_name},\n\n"
        f"ich bitte um die Zusendung der Rechnung (NFI) für folgende Buchung/Kundendaten:\n"
        f"- Kunde/Kundin: {client_name}\n"
        f"- Zeitraum/Buchung: {duration}\n\n"
        f"Vielen Dank im Voraus für Ihre Unterstützung.\n\n"
        f"Mit freundlichen Grüßen\n"
        f"{sender_name}\n"
    )
    return subject, body


def main():
    parser = argparse.ArgumentParser(description="Hotel invoice email helper (Google CSE + Outlook Web)")
    parser.add_argument("--file", "-f", required=True, help="Path to Excel/CSV with hotels")
    parser.add_argument("--client-col", default=DEFAULT_CLIENT_COL)
    parser.add_argument("--due-col", default=DEFAULT_DUE_COL)
    parser.add_argument("--to-col", default=DEFAULT_TO_COL)
    parser.add_argument("--hotel-col", default=DEFAULT_HOTEL_COL)


    # Mail + behavior
    parser.add_argument("--sender-name", default="[Your Name]")
    parser.add_argument("--client-name", default=None, help="If set, use this client name for all rows (ignores missing Client column)")
    parser.add_argument("--save-updated", action="store_true", help="When adding missing client column, save an updated copy of the sheet")
    parser.add_argument("--pause", type=float, default=2.0, help="Pause (seconds) between rows")
    parser.add_argument("--mailer", choices=["web", "outlook", "smtp", "none"], default="web",
                        help="web/outlook=open compose; smtp=send directly; none=log only")
    parser.add_argument("--outlook-host", choices=["live", "office"], default="live", help="Which Outlook web host to use")
    parser.add_argument("--smtp-host", default=None)
    parser.add_argument("--smtp-port", type=int, default=587)
    parser.add_argument("--smtp-user", default=None)
    parser.add_argument("--smtp-pass", default=None)
    parser.add_argument("--from-email", default=None)

    # Google Custom Search JSON API
    parser.add_argument("--google-api-key", default=None, help="Overrides GOOGLE_API_KEY from .env")
    parser.add_argument("--google-cx", default=None, help="Overrides GOOGLE_CX (Programmable Search Engine ID) from .env")

    args = parser.parse_args()

    # Load env and resolve Google creds
    load_dotenv()
    google_api_key = args.google_api_key or os.getenv("GOOGLE_API_KEY")
    google_cx = args.google_cx or os.getenv("GOOGLE_CX")
    if not google_api_key or not google_cx:
        raise SystemExit("ERROR: Missing GOOGLE_API_KEY/GOOGLE_CX. Set via --google-api-key/--google-cx or .env")

    # Read input
    df = read_sheet(args.file)

    # If client column is missing but a fallback name is provided, create it
    client_col_available = args.client_col in df.columns
    if not client_col_available and args.client_name:
        df[args.client_col] = str(args.client_name)
        client_col_available = True
        if args.save_updated:
            root, ext = os.path.splitext(args.file)
            out_path = f"{root}_updated{ext if ext.lower() in ('.xlsx', '.xls', '.csv') else '.xlsx'}"
            if ext.lower() == ".csv":
                df.to_csv(out_path, index=False)
            else:
                df.to_excel(out_path, index=False)
            print(f"[save] wrote updated file with '{args.client_col}' column → {out_path}")

    # Validate columns (client column can be missing if --client-name provided)
    required_cols = [args.due_col, args.to_col, args.hotel_col]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise SystemExit(f"Missing column(s) {missing}. Available: {list(df.columns)}")
    if not client_col_available and not args.client_name:
        raise SystemExit(f"Missing column '{args.client_col}' and no --client-name provided. Available: {list(df.columns)}")

    init_log()

    for idx, row in df.iterrows():
        
        if client_col_available:
            client_name = str(row.get(args.client_col, "")).strip()
        else:
            client_name = str(args.client_name).strip()
        stay_due = str(row.get(args.due_col, "")).strip()
        stay_to = str(row.get(args.to_col, "")).strip()
        stay_duration = f"{stay_due} to {stay_to}".strip()
        hotel_name = str(row.get(args.hotel_col, "")).strip()

        if not hotel_name:
            print(f"[skip] row {idx}: empty hotel")
            continue

        print(f"[.] row {idx} → {hotel_name}")

        notes = ""
        website_candidate = ""
        found_emails = []

        # 1) Find likely official/contact site via Google CSE
        try:
            links = google_cse_find_site(
                f"{hotel_name} official site contact",
                api_key=google_api_key,
                cx=google_cx,
                num=5,
                pause=1.0,
            )
            chosen = next((l for l in links if not is_blacklisted(l)), links[0] if links else None)
            website_candidate = chosen or ""
        except Exception as e:
            notes += f"search_error:{e};"

        # 2) Extract emails from candidate site
        if website_candidate:
            try:
                found_emails = find_emails_for_website(website_candidate)
            except Exception as e:
                notes += f"scrape_error:{e};"

        # 3) Fallback search: "<hotel> contact"
        if not found_emails and website_candidate:
            try:
                links = google_cse_find_site(
                    f"{hotel_name} contact",
                    api_key=google_api_key,
                    cx=google_cx,
                    num=5,
                    pause=1.0,
                )
                for l in links[:4]:
                    if is_blacklisted(l):
                        continue
                    emails_try = find_emails_for_website(l)
                    if emails_try:
                        found_emails = emails_try
                        website_candidate = l
                        break
            except Exception:
                pass

        # 4) Send / open compose (German email)
        status = "skipped_no_email"
        if found_emails:
            to_email = found_emails[0]
            try:
                subject, body = build_german_email(hotel_name, client_name, stay_duration, args.sender_name)
                if args.mailer in ("web", "outlook"):
                    open_outlook_web_email(to_email, subject, body, host=args.outlook_host)
                    status = "email_opened_web"
                    print(f"[web] compose opened ({args.outlook_host}) → {to_email}")
                elif args.mailer == "smtp":
                    required = [args.smtp_host, args.smtp_port, args.smtp_user, args.smtp_pass, args.from_email]
                    if not all(required):
                        raise ValueError("Missing SMTP settings: --smtp-host/--smtp-port/--smtp-user/--smtp-pass/--from-email")
                    send_smtp_email(
                        smtp_host=args.smtp_host,
                        smtp_port=args.smtp_port,
                        smtp_user=args.smtp_user,
                        smtp_pass=args.smtp_pass,
                        from_email=args.from_email,
                        to_email=to_email,
                        subject=subject,
                        body=body,
                    )
                    status = "email_sent_smtp"
                    print(f"[smtp] email sent → {to_email}")
                else:
                    status = "email_found_dry"
                    print(f"[dry] email found → {to_email}")
            except Exception as e:
                notes += f"send_error:{e};"
                status = "send_failed"
                print(f"[err] send_failed: {e}")
        else:
            notes += "no_email_found;"
            print(f"[!] no email found for {hotel_name}")

        # 5) Log
        log_result(
            idx,
            hotel_name,
            client_name,
            stay_duration,
            website_candidate,
            found_emails,
            status,
            notes,
        )

        time.sleep(max(0.0, args.pause))

    print("Done. Check Outlook (if using --mailer web/outlook) and hotel_search_log.csv")


if __name__ == "__main__":
    main()
