from appwrite.client import Client
from appwrite.services.storage import Storage
import os
client = Client()
APPWRITE_ENDPOINT =   os.getenv("APPWRITE_ENDPOINT")
APPWRITE_PROJECT = os.getenv("APPWRITE_PROJECT")
APPWRITE_KEY = os.getenv("APPWRITE_KEY")
(client
    .set_endpoint(APPWRITE_ENDPOINT)  
    .set_project(APPWRITE_PROJECT) 
    .set_key(APPWRITE_KEY)
)

storage = Storage(client)