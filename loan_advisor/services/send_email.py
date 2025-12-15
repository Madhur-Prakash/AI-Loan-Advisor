from email.message import EmailMessage
from email.mime.application import MIMEApplication
import os
import base64
import pickle
from email.utils import formatdate
import time
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import traceback
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv
import requests

load_dotenv()


NO_REPLY_EMAIL = os.getenv("NO_REPLY_EMAIL")
PROJECT_ID = os.getenv("PROJECT_ID")
APPWRITE_API_KEY = os.getenv("APPWRITE_API_KEY")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = int(os.getenv("MAIL_PORT", 587))

# Define the scope for Gmail API
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def authenticate_gmail():
    """Authenticate and return Gmail API service."""
    creds = None

    # Load credentials from token.pickle if available
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    # If credentials are invalid or don't exist, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for future use
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return build("gmail", "v1", credentials=creds)

# @celery.task()
def send_email(to_email, subject, body, retries=3, delay=5):
    """Send an email using Gmail API with retry mechanism."""
    service = authenticate_gmail()
    for attempt in range(retries):
        try:

            # Create email message
            message = MIMEText(body, "html")  # Specify the MIME type as "html"
            message["to"] = to_email
            message["subject"] = subject
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            # Send email using Gmail API
            message = {"raw": raw_message}
            sent_message = service.users().messages().send(userId="me", body=message).execute()
            print(f"Email sent! Message ID: {sent_message['id']}")
            return sent_message
        except Exception as e:
            print(f"Failed to send email due to timeout: {e}. Retrying in {delay} seconds...")
            print(f"Error: {traceback.format_exc()}")
            time.sleep(delay)
    print("Failed to send email after multiple attempts.")


async def send_email_with_aiosmtplib(to_email, subject, body, file_path: str, retries=3, delay=5):
    
    for attempt in range(retries):
        try:
            # ---- Download file from Appwrite ----
            headers = {
                "X-Appwrite-Project": PROJECT_ID,
            }
            if APPWRITE_API_KEY:
                headers["X-Appwrite-Key"] = APPWRITE_API_KEY

            response = requests.get(file_path, headers=headers, timeout=30)
            response.raise_for_status()

            file_data = response.content
            filename = "sanction_letter.pdf"

            # ---- Build Email ----
            message = EmailMessage()
            message["From"] = NO_REPLY_EMAIL
            message["To"] = to_email
            message["Subject"] = subject
            message["Date"] = formatdate(localtime=True)

            # HTML body
            message.set_content("This email requires an HTML-capable client.")
            message.add_alternative(body, subtype="html")

            # PDF attachment
            attachment = MIMEApplication(file_data, _subtype="pdf")
            attachment.add_header(
                "Content-Disposition",
                "attachment",
                filename=filename
            )
            message.attach(attachment)

            # ---- Send via SMTP ----
            await aiosmtplib.send(
                message,
                hostname=MAIL_SERVER,
                port=MAIL_PORT,
                username=NO_REPLY_EMAIL,
                password=MAIL_PASSWORD,
                use_tls=True,
                timeout=30
            )

            print("Email sent successfully")
            return True

        except aiosmtplib.errors.SMTPAuthenticationError as e:
            print(f"Gmail authentication failed: {e}")
            print("Please check:")
            print("1. Enable 2-Factor Authentication on Gmail")
            print("2. Generate App Password (not regular password)")
            print("3. Use the 16-character App Password in MAIL_PASSWORD")
            raise
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            print(traceback.format_exc())
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise

def send_email_with_url_attachment(to_email, subject, body, file_url: str, retries=3, delay=5):
    
    service = authenticate_gmail()  

    for attempt in range(retries):
        try:
            # Download file from Appwrite URL with authentication
            headers = {
                "X-Appwrite-Project": PROJECT_ID,
            }
            # Add API key if available for server-side access
            if APPWRITE_API_KEY:
                headers["X-Appwrite-Key"] = APPWRITE_API_KEY
            
            response = requests.get(file_url, headers=headers)
            response.raise_for_status()

            file_data = response.content

            # Set proper PDF MIME type
            content_type = "application/pdf"
            main_type, sub_type = "application", "pdf"

            # Extract filename from URL or use default with .pdf extension
            filename = "sanction_letter.pdf"

            # Create multipart message
            message = MIMEMultipart()
            message["to"] = to_email
            message["subject"] = subject

            # Add HTML body
            message.attach(MIMEText(body, "html"))

            # Add PDF attachment with proper headers
            file_part = MIMEBase(main_type, sub_type)
            file_part.set_payload(file_data)
            encoders.encode_base64(file_part)
            file_part.add_header(
                "Content-Disposition",
                f'attachment; filename="{filename}"'
            )
            file_part.add_header("Content-Type", content_type)

            message.attach(file_part)

            # Encode to base64
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            send_body = {"raw": raw_message}

            # Send email
            sent_message = service.users().messages().send(
                userId="me",
                body=send_body
            ).execute()

            print(f"Email sent! Message ID: {sent_message['id']}")
            return sent_message

        except Exception as e:
            print(f"Failed to send email: {e}. Retrying in {delay} seconds...")
            print(traceback.format_exc())
            time.sleep(delay)




