from appwrite.client import Client
import os
from dotenv import load_dotenv

load_dotenv()

API_ENDPOINT = os.getenv("API_ENDPOINT")
PROJECT_ID = os.getenv("PROJECT_ID")
APPWRITE_API_KEY = os.getenv("APPWRITE_API_KEY")
BUCKET_ID = os.getenv("BUCKET_ID")

client = Client()

(client
  .set_endpoint(API_ENDPOINT) # Your API Endpoint
  .set_project(PROJECT_ID) # Your project ID
  .set_key(APPWRITE_API_KEY) # Your secret API key
)
