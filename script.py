import os
import base64
from smtplib import SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import pandas as pd
from decouple import AutoConfig

config = AutoConfig()

send_to = "csv/check.csv"
subject = "You're invited to DeerUtsav 10.0!"
image_path = "./images/"
invitation_path = "./images/invitation cards/"
template_path = "./templates/index.html"
logo_path = os.path.join(image_path, "logo/mainLogo.png") 

def load_template(template_path):
    with open(template_path, 'r') as file:
        template = file.read()
    return template

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        encoded_string = base64.b64encode(img_file.read()).decode('utf-8')
    return encoded_string

def send_mail():
    host = "smtp.gmail.com"
    port = 587

    email = config("APP_EMAIL")
    password = config("APP_PASSWORD")

    with SMTP(host, port) as server:
        server.starttls()
        print(f"Trying to log in with {email}")
        server.login(email, password)
        print(f"Logged in with {email}")

        df = pd.read_csv(send_to)
        print(f"Total emails: {len(df)}")
        print(f"Sending emails to: {df['Email'].tolist()}")

        email_template = load_template(template_path)
        logo_base64 = encode_image_to_base64(logo_path)
        logo_cid = "logo_image"

        for index, row in df.iterrows():
            recipient_name = row['Name']
            recipient_email = row['Email']
            image_filename = os.path.join(invitation_path, f"{recipient_name}.png")

            if not os.path.exists(image_filename):
                print(f"Image {image_filename} not found for {recipient_name}, skipping email.")
                with open("failed.csv", "a") as f:
                    f.write(f"{recipient_name}, {recipient_email}, {image_filename} - Image not found\n")
                continue

            msg = MIMEMultipart()
            msg['From'] = f"DeerUtsav <{email}>"
            msg['To'] = recipient_email
            msg['Subject'] = subject

            email_content = email_template.replace("{{Name}}", recipient_name)
            email_content = email_content.replace("../images/logo/mainLogo.png", f"cid:{logo_cid}")

            msg.attach(MIMEText(email_content, "html"))

            # Attach the personalized image
            with open(image_filename, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {os.path.basename(image_filename)}",
                )
                msg.attach(part)
            print(f"Attached personalized image {image_filename} to email for {recipient_name}")

            # Attach the embedded logo image
            logo_part = MIMEBase("image", "png", filename="logo.png")
            logo_part.set_payload(base64.b64decode(logo_base64))
            encoders.encode_base64(logo_part)
            logo_part.add_header("Content-ID", f"<{logo_cid}>")
            logo_part.add_header("Content-Disposition", "inline", filename="logo.png")
            msg.attach(logo_part)
            print(f"Embedded logo image into email for {recipient_name}")

            try:
                server.sendmail(email, recipient_email, msg.as_string())
                print(f"Email sent to {recipient_name} at {recipient_email}")
                with open("sent.csv", "a") as f:
                    f.write(f"{recipient_name}, {recipient_email}, {image_filename}\n")
            except Exception as e:
                print(f"Failed to send email to {recipient_name} at {recipient_email}: {e}")
                with open("failed.csv", "a") as f:
                    f.write(f"{recipient_name}, {recipient_email}, {image_filename} - {e}\n")

        print("All emails processed")

if __name__ == "__main__":
    print("Sending email")
    send_mail()
