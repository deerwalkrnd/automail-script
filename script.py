import os
import base64
import pandas as pd

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# =========================
# OAuth Configuration
# =========================

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send"
]

CREDENTIALS_PATH = "./credentials.json"
TOKEN_PATH = "./token.json"


# =========================
# Configuration
# =========================

send_to = "./csv/extra.csv"

subject = "Invitation | Graduation Ceremony | Class of 2025"

image_path = "./images/"
invitation_path = "./images/invitation cards/"
template_path = "./templates/index.html"

logo_path = os.path.join(
    image_path,
    "logo/Logo.png"
)


# =========================
# Helper Functions
# =========================

def load_template(path):
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def get_gmail_service():
    """
    Authenticate with Google using OAuth 2.0
    and return an authenticated Gmail API client.
    """

    creds = None

    # =========================
    # Load Existing Token
    # =========================

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(
            TOKEN_PATH,
            SCOPES
        )

    # =========================
    # Refresh / Obtain Credentials
    # =========================

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:

            print("Refreshing Google OAuth token...")

            creds.refresh(Request())

        else:

            print("Starting Google OAuth authorization...")

            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH,
                SCOPES
            )

            creds = flow.run_local_server(
                port=0
            )

        # Save credentials for future runs
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    # =========================
    # Build Gmail API Client
    # =========================

    return build(
        "gmail",
        "v1",
        credentials=creds
    )


def create_email(
    sender_email,
    recipient_email,
    recipient_name,
    email_template,
    logo_path,
    image_filename,
    subject
):
    """
    Create the MIME email.
    """

    # =========================
    # Create Email
    # =========================

    msg = MIMEMultipart()

    msg["From"] = (
        f"Graduation Ceremony "
        f"<{sender_email}>"
    )

    msg["To"] = recipient_email
    msg["Subject"] = subject

    # =========================
    # Personalized HTML
    # =========================

    email_content = email_template.replace(
        "{{Name}}",
        recipient_name
    )

    # =========================
    # Embedded Logo
    # =========================

    logo_cid = "logo_image"

    email_content = email_content.replace(
        "../images/logo/Logo.png",
        f"cid:{logo_cid}"
    )

    # =========================
    # Attach HTML
    # =========================

    msg.attach(
        MIMEText(
            email_content,
            "html",
            "utf-8"
        )
    )

    # =========================
    # Attach Personalized Card
    # =========================

    with open(
        image_filename,
        "rb"
    ) as attachment:

        part = MIMEBase(
            "application",
            "octet-stream"
        )

        part.set_payload(
            attachment.read()
        )

        encoders.encode_base64(part)

        part.add_header(
            "Content-Disposition",
            "attachment",
            filename=os.path.basename(
                image_filename
            )
        )

        msg.attach(part)

    print(
        f"Attached personalized "
        f"image for {recipient_name}"
    )

    # =========================
    # Embed Logo
    # =========================

    with open(
        logo_path,
        "rb"
    ) as logo_file:

        logo_part = MIMEBase(
            "image",
            "png",
            filename="logo.png"
        )

        logo_part.set_payload(
            logo_file.read()
        )

        encoders.encode_base64(
            logo_part
        )

        logo_part.add_header(
            "Content-ID",
            f"<{logo_cid}>"
        )

        logo_part.add_header(
            "Content-Disposition",
            "inline",
            filename="logo.png"
        )

        msg.attach(logo_part)

    print(
        f"Embedded logo for "
        f"{recipient_name}"
    )

    return msg


def send_message(service, msg):
    """
    Send a MIME email through the Gmail API.
    """

    encoded_message = base64.urlsafe_b64encode(
        msg.as_bytes()
    ).decode("utf-8")

    body = {
        "raw": encoded_message
    }

    result = (
        service.users()
        .messages()
        .send(
            userId="me",
            body=body
        )
        .execute()
    )

    return result


# =========================
# Send Emails
# =========================

def send_mail():

    # =========================
    # Authenticate
    # =========================

    print("Authenticating with Google...")

    service = get_gmail_service()

    print("Authenticated with Google.")

    # =========================
    # Load Template
    # =========================

    email_template = load_template(
        template_path
    )

    # =========================
    # Check Logo
    # =========================

    if not os.path.exists(logo_path):

        print(
            f"Logo not found: {logo_path}"
        )

        return

    # =========================
    # Check CSV
    # =========================

    if not os.path.exists(send_to):

        print(
            f"CSV not found: {send_to}"
        )

        return

    df = pd.read_csv(send_to)

    print(
        f"Total emails: {len(df)}"
    )

    print(
        f"Sending emails to: "
        f"{df['Email'].tolist()}"
    )

    # =========================
    # Get Authenticated Account
    # =========================

    sender_email = "administration@deerwalk.edu.np"

    # =========================
    # Process Recipients
    # =========================

    for index, row in df.iterrows():

        recipient_name = str(
            row["Name"]
        ).strip()

        recipient_email = str(
            row["Email"]
        ).strip()

        print()

        print(
            f"Processing "
            f"{index + 1}/{len(df)}: "
            f"{recipient_name}"
        )

        # =========================
        # Personalized Invitation
        # =========================

        image_filename = os.path.join(
            invitation_path,
            f"{recipient_name}.png"
        )

        if not os.path.exists(
            image_filename
        ):

            print(
                f"Image not found for "
                f"{recipient_name}: "
                f"{image_filename}"
            )

            with open(
                "failed.csv",
                "a",
                encoding="utf-8"
            ) as f:

                f.write(
                    f'"{recipient_name}",'
                    f'"{recipient_email}",'
                    f'"{image_filename}",'
                    f'"Image not found"\n'
                )

            continue

        # =========================
        # Create Email
        # =========================

        msg = create_email(
            sender_email=sender_email,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            email_template=email_template,
            logo_path=logo_path,
            image_filename=image_filename,
            subject=subject
        )

        # =========================
        # Send Email
        # =========================

        try:

            result = send_message(
                service,
                msg
            )

            print(
                f"Email sent to "
                f"{recipient_name} "
                f"at {recipient_email}"
            )

            print(
                f"Message ID: "
                f"{result['id']}"
            )

            # =========================
            # Log Success
            # =========================

            with open(
                "sent.csv",
                "a",
                encoding="utf-8"
            ) as f:

                f.write(
                    f'"{recipient_name}",'
                    f'"{recipient_email}",'
                    f'"{image_filename}"\n'
                )

        except Exception as e:

            print(
                f"Failed to send email to "
                f"{recipient_name} "
                f"at {recipient_email}: {e}"
            )

            # =========================
            # Log Failure
            # =========================

            with open(
                "failed.csv",
                "a",
                encoding="utf-8"
            ) as f:

                f.write(
                    f'"{recipient_name}",'
                    f'"{recipient_email}",'
                    f'"{image_filename}",'
                    f'"{str(e)}"\n'
                )

    print()
    print("All emails processed")


# =========================
# Main
# =========================

if __name__ == "__main__":

    print(
        "Sending graduation invitations..."
    )

    send_mail()
