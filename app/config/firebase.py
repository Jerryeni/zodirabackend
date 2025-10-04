import firebase_admin
from firebase_admin import credentials, firestore, auth, storage
from google.cloud import firestore as fs
import os
import json
from decouple import config

# Initialize Firebase Admin SDK
def initialize_firebase():
    if not firebase_admin._apps:
        # Create credentials from environment variables
        service_account_info = {
            "type": "service_account",
            "project_id": config('FIREBASE_PROJECT_ID'),
            "private_key_id": config('FIREBASE_PRIVATE_KEY_ID'),
            "private_key": config('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
            "client_email": config('FIREBASE_CLIENT_EMAIL'),
            "client_id": config('FIREBASE_CLIENT_ID'),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{config('FIREBASE_CLIENT_EMAIL').replace('@', '%40')}",
            "universe_domain": "googleapis.com"
        }
        
        cred = credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(cred, {
            'storageBucket': config('FIREBASE_STORAGE_BUCKET')
        })

    return firestore.client(), storage.bucket()

# Get Firestore client
def get_firestore_client():
    return firestore.client()

# Get Storage bucket
def get_storage_bucket():
    return storage.bucket()