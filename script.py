import os
import pandas as pd

from decouple import AutoConfig
from smtplib import SMTP

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders


config = AutoConfig()


# =========================
# Configuration
# =========================

send_to = "./csv/graduation-dwit.csv"

subject = "Invitation | Graduation Ceremony | Class of 2025"

image_path = "./images/"
invitation_path = "./images/invitation cards/Students/"
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


# =========================
# Send Emails
# =========================

def send_mail():

    host = "smtp.gmail.com"
    port = 587

    email = config("APP_EMAIL")
    password = config("APP_PASSWORD")

    # =========================
    # Load Email Template
    # =========================

    email_template = load_template(template_path)

    # =========================
    # Check Required Files
    # =========================

    if not os.path.exists(logo_path):
        print(f"Logo not found: {logo_path}")
        return

    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return

    if not os.path.exists(send_to):
        print(f"CSV file not found: {send_to}")
        return

    # =========================
    # Read CSV
    # =========================

    df = pd.read_csv(send_to)

    print(f"Total emails: {len(df)}")
    print(f"Sending emails to: {df['Email'].tolist()}")

    # =========================
    # Connect to Gmail SMTP
    # =========================

    with SMTP(host, port) as server:

        server.starttls()

        print(f"Trying to log in with {email}")

        server.login(email, password)

        print(f"Logged in with {email}")

        # =========================
        # Process Each Recipient
        # =========================

        for index, row in df.iterrows():

            recipient_name = str(row["Name"]).strip()
            recipient_email = str(row["Email"]).strip()

            print()
            print("=" * 60)
            print(
                f"Processing {index + 1}/{len(df)}: "
                f"{recipient_name} <{recipient_email}>"
            )
            print("=" * 60)

            # =========================
            # Personalized Invitation
            # =========================

            image_filename = os.path.join(
                invitation_path,
                f"{recipient_name}.png"
            )

            # Check personalized image
            if not os.path.exists(image_filename):

                print(
                    f"Image not found for {recipient_name}: "
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
            # Create Main Email
            # =========================
            #
            # multipart/mixed allows us to have:
            #
            #   1. HTML email with inline images
            #   2. Actual file attachments
            #
            # =========================

            msg = MIMEMultipart("mixed")

            msg["From"] = f"Graduation Ceremony <{email}>"
            msg["To"] = recipient_email
            msg["Subject"] = subject

            # =========================
            # Personalize HTML
            # =========================

            email_content = email_template.replace(
                "{{Name}}",
                recipient_name
            )

            # =========================
            # Create RELATED Container
            # =========================
            #
            # This container holds:
            #
            #   HTML
            #   Inline images referenced using CID
            #
            # =========================

            related = MIMEMultipart("related")

            # =========================
            # Attach HTML
            # =========================

            html_part = MIMEText(
                email_content,
                "html",
                "utf-8"
            )

            related.attach(html_part)

            # =========================
            # Embed Logo
            # =========================

            with open(logo_path, "rb") as logo_file:

                logo_part = MIMEImage(
                    logo_file.read(),
                    _subtype="png"
                )

                # This MUST match:
                #
                # <img src="cid:logo_image">
                #
                logo_part.add_header(
                    "Content-ID",
                    "<logo_image>"
                )

                # Tell email clients this is an inline resource
                logo_part.add_header(
                    "Content-Disposition",
                    "inline",
                    filename="logo.png"
                )

                # Optional but useful
                logo_part.add_header(
                    "Content-Location",
                    "logo.png"
                )

                related.attach(logo_part)

            print(
                f"Embedded logo for {recipient_name}"
            )

            # =========================
            # Attach RELATED Section
            # =========================

            msg.attach(related)

            # =========================
            # Attach Personalized Card
            # =========================

            with open(
                image_filename,
                "rb"
            ) as attachment:

                invitation_part = MIMEBase(
                    "application",
                    "octet-stream"
                )

                invitation_part.set_payload(
                    attachment.read()
                )

                encoders.encode_base64(
                    invitation_part
                )

                invitation_part.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=os.path.basename(
                        image_filename
                    )
                )

                msg.attach(invitation_part)

            print(
                f"Attached invitation for "
                f"{recipient_name}"
            )

            # =========================
            # Send Email
            # =========================

            try:

                server.sendmail(
                    email,
                    recipient_email,
                    msg.as_string()
                )

                print(
                    f"Email sent successfully to "
                    f"{recipient_name} "
                    f"({recipient_email})"
                )

                # =========================
                # Log Successful Email
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
                    f"({recipient_email})"
                )

                print(f"Error: {e}")

                # =========================
                # Log Failed Email
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
    print("=" * 60)
    print("All emails processed")
    print("=" * 60)


# =========================
# Main
# =========================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("Sending graduation invitations...")
    print("=" * 60)

    send_mail()