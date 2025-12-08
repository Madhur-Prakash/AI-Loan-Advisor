import os
import base64
import pickle
import time
import mimetypes
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




