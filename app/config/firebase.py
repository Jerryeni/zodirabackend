import firebase_admin
from firebase_admin import credentials, firestore, auth, storage
from google.cloud import firestore as fs
import os
import json
from decouple import config

# Initialize Firebase Admin SDK
def initialize_firebase():
    if not firebase_admin._apps:
        try:
            # Required service account fields
            project_id = config('FIREBASE_PROJECT_ID')
            private_key_id = config('FIREBASE_PRIVATE_KEY_ID')
            private_key = config('FIREBASE_PRIVATE_KEY').replace('\\n', '\n')
            client_email = config('FIREBASE_CLIENT_EMAIL')

            # Optional fields
            client_id = config('FIREBASE_CLIENT_ID', default=None)
            storage_bucket = config('FIREBASE_STORAGE_BUCKET', default=None)

            # Build service account dict (include client_id only if provided)
            service_account_info = {
                "type": "service_account",
                "project_id": project_id,
                "private_key_id": private_key_id,
                "private_key": private_key,
                "client_email": client_email,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{client_email.replace('@', '%40')}",
                "universe_domain": "googleapis.com",
            }
            if client_id:
                service_account_info["client_id"] = client_id

            cred = credentials.Certificate(service_account_info)

            init_kwargs = {}
            if storage_bucket:
                init_kwargs["storageBucket"] = storage_bucket

            firebase_admin.initialize_app(cred, init_kwargs)
        except Exception as e:
            # Surface a concise, actionable error
            raise RuntimeError(f"Firebase initialization failed: {e}")

    return firestore.client(), storage.bucket()

# Get Firestore client
def get_firestore_client():
    return firestore.client()

# Get Storage bucket
def get_storage_bucket():
    return storage.bucket()