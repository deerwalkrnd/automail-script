import base64
import os
import smtplib
import ssl
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
CREDENTIALS_PATH = "./credentials.json"
TOKEN_PATH = "./token.json"
RECIPIENTS_PATH = "./csv/newguestlist.csv"
TEMPLATE_PATH = "./templates/index.html"
LOGO_PATH = "./logo_it4d.png"
SUBJECT = "Reminder: 9th IT4D Conference on November 20, 2026"
SENDER_EMAIL = "administration@deerwalk.edu.np"
CC_EMAIL = "pravin.thapalia@deerwalk.edu.np"


def load_dotenv(path=".env"):
    """Load simple KEY=VALUE settings without replacing environment variables."""
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip().strip("\"'")
            if key:
                os.environ.setdefault(key, value)


def get_smtp_settings():
    """Return SMTP credentials, preferring an app password over a login password."""
    email = os.getenv("APP_EMAIL") or os.getenv("GMAIL_EMAIL") or SENDER_EMAIL
    app_password = os.getenv("APP_PASSWORD") or os.getenv("GMAIL_APP_PASSWORD")
    account_password = os.getenv("EMAIL_PASSWORD") or os.getenv("GMAIL_PASSWORD")
    password = app_password or account_password
    return email, password


def get_smtp_connection(email, password):
    connection = smtplib.SMTP_SSL(
        "smtp.gmail.com", 465, context=ssl.create_default_context()
    )
    connection.login(email, password)
    return connection


def load_template(path):
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def get_gmail_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def create_email(
    sender_email,
    recipient_email,
    recipient_name,
    email_template,
):
    msg = MIMEMultipart("related")
    msg["From"] = f"IT4D Conference <{sender_email}>"
    msg["To"] = recipient_email
    msg["Cc"] = CC_EMAIL
    msg["Subject"] = SUBJECT

    safe_name = (
        recipient_name
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    html = email_template.replace("{{Name}}", safe_name or "there")

    alternative = MIMEMultipart("alternative")

    alternative.attach(
        MIMEText(
            f"""Dear {recipient_name or 'there'},

Just a gentle reminder of our invitation to join us at the 9th IT4D Conference on November 20, 2026.

Registration Time: 8:00 AM - 9:00 AM

We would be honoured by your presence and look forward to welcoming you.
To confirm your participation, please click on the RSVP button below.
RSVP: https://docs.google.com/forms/d/e/1FAIpQLSdLKQkXUzYShyzvo130K0x6ZB7g4dfzHtoD5P4vJz4jYBnq3Q/viewform

Warm regards,
Kumar Lamichhane""",
            "plain",
            "utf-8",
        )
    )

    alternative.attach(MIMEText(html, "html", "utf-8"))
    msg.attach(alternative)

    with open(LOGO_PATH, "rb") as logo_file:
        logo = MIMEImage(
            logo_file.read(),
            _subtype="png",
            name="logo_it4d.png",
        )

    logo.add_header("Content-ID", "<logo_image>")
    logo.add_header(
        "Content-Disposition",
        "inline",
        filename="logo_it4d.png",
    )

    msg.attach(logo)

    return msg


def send_message(service, msg):
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    return service.users().messages().send(userId="me", body={"raw": raw}).execute()


def send_mail():
    load_dotenv()
    for path in (TEMPLATE_PATH, LOGO_PATH, RECIPIENTS_PATH):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Required file not found: {path}")

    df = pd.read_csv(RECIPIENTS_PATH)
    if not {"Name", "Email"}.issubset(df.columns):
        raise ValueError(f"{RECIPIENTS_PATH} must contain Name and Email columns")

    smtp_email, smtp_password = get_smtp_settings()
    use_smtp = bool(smtp_password)
    sender_email = smtp_email if use_smtp else SENDER_EMAIL
    if use_smtp:
        print("Using Gmail SMTP with an app password." if (
            os.getenv("APP_PASSWORD") or os.getenv("GMAIL_APP_PASSWORD")
        ) else "Using Gmail SMTP with the configured account password.")
        transport = get_smtp_connection(smtp_email, smtp_password)
    else:
        if not os.path.exists(CREDENTIALS_PATH):
            raise FileNotFoundError(
                f"{CREDENTIALS_PATH} is required when no SMTP password is configured"
            )
        print("No SMTP password configured; using Gmail OAuth.")
        transport = get_gmail_service()

    template = load_template(TEMPLATE_PATH)
    for index, row in df.iterrows():
        name = "" if pd.isna(row["Name"]) else str(row["Name"]).strip()
        email = "" if pd.isna(row["Email"]) else str(row["Email"]).strip()
        if not email:
            print(f"Skipping row {index + 1}: missing email")
            continue
        try:
            message = create_email(
                sender_email=sender_email,
                recipient_email=email,
                recipient_name=name,
                email_template=template,
            )
            if use_smtp:
                transport.send_message(message)
                result_id = "SMTP accepted"
            else:
                result = send_message(transport, message)
                result_id = result["id"]
            print(f"Email sent to {name or email} ({result_id})")
            with open("sent.csv", "a", encoding="utf-8") as log:
                log.write(f'"{name}","{email}"\n')
        except Exception as error:
            print(f"Failed to send to {email}: {error}")
            with open("failed.csv", "a", encoding="utf-8") as log:
                log.write(f'"{name}","{email}","{str(error).replace(chr(34), chr(39))}"\n')

    if use_smtp:
        transport.quit()


if __name__ == "__main__":
    send_mail()
