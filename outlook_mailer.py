import urllib.parse, webbrowser

def open_outlook_web_email(to_email: str, subject: str, body: str, host: str = "office"):
    base = "https://outlook.office.com/mail/deeplink/compose" if host == "office" \
        else "https://outlook.live.com/mail/0/deeplink/compose"
    params = {"to": to_email or "", "subject": subject or "", "body": body or ""}
    url = base + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    webbrowser.open(url)
