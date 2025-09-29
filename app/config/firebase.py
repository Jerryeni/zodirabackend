import firebase_admin
from firebase_admin import credentials, firestore, auth, storage
from google.cloud import firestore as fs
import os
from decouple import config

# Initialize Firebase Admin SDK
def initialize_firebase():
    if not firebase_admin._apps:
        # Use service account key for production
        cred = credentials.Certificate(config('FIREBASE_SERVICE_ACCOUNT_PATH'))
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