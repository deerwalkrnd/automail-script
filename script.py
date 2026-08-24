import os
import base64
import pandas as pd

from decouple import AutoConfig
from smtplib import SMTP

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


config = AutoConfig()


# =========================
# Configuration
# =========================

send_to = "./csv/extra.csv"

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


def encode_image_to_base64(path):
    with open(path, "rb") as img_file:
        encoded_string = base64.b64encode(
            img_file.read()
        ).decode("utf-8")

    return encoded_string


# =========================
# Send Emails
# =========================

def send_mail():

    host = "smtp.gmail.com"
    port = 587

    email = config("APP_EMAIL")
    password = config("APP_PASSWORD")

    # =========================
    # Load Template
    # =========================

    email_template = load_template(template_path)

    # =========================
    # Load Logo
    # =========================

    if not os.path.exists(logo_path):
        print(f"Logo not found: {logo_path}")
        return

    logo_base64 = encode_image_to_base64(logo_path)

    # CID used inside HTML
    logo_cid = "logo_image"

    # =========================
    # Read CSV
    # =========================

    if not os.path.exists(send_to):
        print(f"CSV not found: {send_to}")
        return

    df = pd.read_csv(send_to)

    print(f"Total emails: {len(df)}")
    print(
        f"Sending emails to: "
        f"{df['Email'].tolist()}"
    )

    # =========================
    # Connect to Gmail
    # =========================

    with SMTP(host, port) as server:

        server.starttls()

        print(
            f"Trying to log in with {email}"
        )

        server.login(
            email,
            password
        )

        print(
            f"Logged in with {email}"
        )

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

            if not os.path.exists(image_filename):

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

            msg = MIMEMultipart()

            msg["From"] = (
                f"Graduation Ceremony "
                f"<{email}>"
            )

            msg["To"] = recipient_email
            msg["Subject"] = subject

            # =========================
            # Personalize HTML
            # =========================

            email_content = email_template.replace(
                "{{Name}}",
                recipient_name
            )


            # Replace the logo path from HTML
            #
            # Your HTML should contain:
            #
            # ../images/logo/Logo.png
            #
            # or the corresponding path you currently use.
            #
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

                encoders.encode_base64(
                    part
                )

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

            logo_part = MIMEBase(
                "image",
                "png",
                filename="logo.png"
            )

            logo_part.set_payload(
                base64.b64decode(
                    logo_base64
                )
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
                    f"Email sent to "
                    f"{recipient_name} "
                    f"at {recipient_email}"
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

    print("Sending graduation invitations...")

    send_mail()