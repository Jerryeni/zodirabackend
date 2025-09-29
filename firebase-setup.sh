#!/bin/bash

# ZODIRA Firebase Project Setup Script (Python-based)
# This script sets up a complete Firebase project for the ZODIRA astrology app

echo "🚀 ZODIRA Firebase Project Setup (Python)"
echo "=========================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud SDK not found. Please install it first:"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1 > /dev/null; then
    echo "🔐 Authenticating with Google Cloud..."
    gcloud auth login
fi

# Get project ID
read -p "Enter your Firebase project ID (e.g., zodira-astrology): " PROJECT_ID

# Set project
echo "🔧 Setting up project: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required Google Cloud APIs..."
gcloud services enable firestore.googleapis.com
gcloud services enable firebase.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable identitytoolkit.googleapis.com
gcloud services enable storage-api.googleapis.com

# Create service account for admin SDK
echo "🔑 Creating service account for Firebase Admin SDK..."
SERVICE_ACCOUNT_NAME="zodira-admin-sdk"
SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"

# Check if service account already exists
if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL &> /dev/null; then
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --description="Service account for ZODIRA backend Firebase Admin SDK" \
        --display-name="ZODIRA Admin SDK"
else
    echo "✅ Service account already exists"
fi

# Grant necessary permissions
echo "🔐 Granting permissions to service account..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/datastore.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/firebase.admin"

# Generate and download service account key
echo "📥 Generating and downloading service account key..."
if [ ! -f "config/serviceAccountKey.json" ]; then
    gcloud iam service-accounts keys create config/serviceAccountKey.json \
        --iam-account=$SERVICE_ACCOUNT_EMAIL
    echo "✅ Service account key saved to config/serviceAccountKey.json"
else
    echo "✅ Service account key already exists"
fi

# Create storage buckets
echo "🏗️  Creating Cloud Storage buckets..."
if ! gsutil ls -b gs://$PROJECT_ID.appspot.com &> /dev/null; then
    gsutil mb -p $PROJECT_ID gs://$PROJECT_ID.appspot.com
else
    echo "✅ Default bucket already exists"
fi

if ! gsutil ls -b gs://$PROJECT_ID-profile-images &> /dev/null; then
    gsutil mb -p $PROJECT_ID gs://$PROJECT_ID-profile-images
else
    echo "✅ Profile images bucket already exists"
fi

if ! gsutil ls -b gs://$PROJECT_ID-reports &> /dev/null; then
    gsutil mb -p $PROJECT_ID gs://$PROJECT_ID-reports
else
    echo "✅ Reports bucket already exists"
fi

if ! gsutil ls -b gs://$PROJECT_ID-consultations &> /dev/null; then
    gsutil mb -p $PROJECT_ID gs://$PROJECT_ID-consultations
else
    echo "✅ Consultations bucket already exists"
fi

# Set up CORS for storage buckets
echo "🌐 Setting up CORS for storage buckets..."
cat > cors-config.json << EOF
[
  {
    "origin": ["*"],
    "method": ["GET", "POST", "PUT", "DELETE"],
    "maxAgeSeconds": 3600,
    "responseHeader": ["Content-Type", "Authorization"]
  }
]
EOF

gsutil cors set cors-config.json gs://$PROJECT_ID.appspot.com
gsutil cors set cors-config.json gs://$PROJECT_ID-profile-images
gsutil cors set cors-config.json gs://$PROJECT_ID-reports
gsutil cors set cors-config.json gs://$PROJECT_ID-consultations

# Clean up
rm cors-config.json

# Update environment configuration
echo "⚙️  Updating environment configuration..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
FIREBASE_SERVICE_ACCOUNT_KEY_PATH=config/serviceAccountKey.json
FIREBASE_PROJECT_ID=$PROJECT_ID
FIREBASE_STORAGE_BUCKET=$PROJECT_ID.appspot.com

# Razorpay Configuration (add your keys)
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
EOF
    echo "✅ Created .env file"
else
    echo "⚠️  .env file already exists. Please update it manually with:"
    echo "   FIREBASE_PROJECT_ID=$PROJECT_ID"
    echo "   FIREBASE_STORAGE_BUCKET=$PROJECT_ID.appspot.com"
fi

echo ""
echo "🎉 Firebase project setup completed!"
echo ""
echo "📋 Manual steps required:"
echo "1. Go to Firebase Console: https://console.firebase.google.com/project/$PROJECT_ID"
echo "2. Enable Authentication providers (Phone, Google, Facebook)"
echo "3. Enable Firestore Database"
echo "4. Enable Storage"
echo "5. Deploy security rules (see FIREBASE_SETUP.md)"
echo "6. Update .env with actual Razorpay credentials"
echo ""
echo "🔗 Firebase Console: https://console.firebase.google.com/project/$PROJECT_ID"
echo "📚 Setup Guide: See FIREBASE_SETUP.md for detailed instructions"