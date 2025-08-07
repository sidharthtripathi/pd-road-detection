from appwrite.client import Client
from appwrite.services.storage import Storage
client = Client()

(client
    .set_endpoint("http://localhost/v1")  # Appwrite endpoint
    .set_project("6894b8a8003aecf5ee16")       # Replace with your Project ID
    .set_key("standard_e2a6310ef25297d1cde6579a559ae64e9ff320a70432faa16ab6000d5f6bd06421bf8a1e7b574b7ed8aad75406dd99078ee22a94ecd79bea5b747a3375676f912c790c31c45ecc085261a313784893fac501a5d91803f5c4ce41522e379bfcdba284bc88ca86b7b40a001c53f9022fb4493b8ff2d8d6bd77719b6d2ab7763c55")              # Replace with your API Key
)

storage = Storage(client)