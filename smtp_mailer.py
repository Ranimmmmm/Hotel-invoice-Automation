# smtp_mailer.py
import smtplib, ssl
from email.message import EmailMessage

def send_smtp_email(
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_pass: str,
    from_email: str,
    to_email: str,
    subject: str,
    body: str,
):
    msg = EmailMessage()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)          # plain text; or use msg.add_alternative(...) for HTML

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls(context=context)     # if port is 587
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
