# ZODIRA Firebase Project Setup Guide

This guide provides complete instructions for setting up a Firebase project for the ZODIRA astrology application using Python and Google Cloud SDK.

## 📋 Prerequisites

- Python 3.8+ installed
- Google Cloud SDK installed (`gcloud`)
- Google Cloud account with billing enabled
- Firebase project access

## 🚀 Quick Setup (Automated)

Run the automated setup script:

```bash
chmod +x firebase-setup.sh
./firebase-setup.sh
```

The script will:
- Authenticate with Google Cloud
- Enable required APIs
- Create service account and download key
- Set up Cloud Storage buckets with CORS
- Generate environment configuration

## 🔧 Manual Setup Instructions

### 1. Google Cloud SDK Setup

```bash
# Install Google Cloud SDK (if not already installed)
# Download from: https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID
```

### 2. Create Firebase Project

Create a Firebase project via the Firebase Console:
1. Go to https://console.firebase.google.com/
2. Click "Create a project"
3. Enter project name: "ZODIRA Astrology App"
4. Choose project ID (e.g., `zodira-astrology`)
5. Enable Google Analytics (optional)

### 3. Enable Required APIs

```bash
# Enable Firestore API
gcloud services enable firestore.googleapis.com

# Enable Firebase services
gcloud services enable firebase.googleapis.com

# Enable Cloud Storage API
gcloud services enable storage.googleapis.com

# Enable Identity Toolkit API (for Auth)
gcloud services enable identitytoolkit.googleapis.com

# Enable Storage API
gcloud services enable storage-api.googleapis.com
```

### 4. Firebase Console Setup

In Firebase Console (https://console.firebase.google.com):

1. **Enable Firestore Database**
   - Go to Firestore Database
   - Click "Create database"
   - Choose "Start in test mode" (configure security rules later)
   - Select a location (asia-south1 recommended for India)

2. **Enable Storage**
   - Go to Storage
   - Click "Get started"
   - Choose "Start in test mode" (configure security rules later)

3. **Enable Authentication**
   - Go to Authentication
   - Click "Get started"
   - Enable sign-in providers (Phone, Google, Facebook)

### 5. Service Account Setup

```bash
# Create service account
SERVICE_ACCOUNT_NAME="zodira-admin-sdk"
SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT_NAME@zodira-astrology.iam.gserviceaccount.com"

gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
    --description="Service account for ZODIRA backend Firebase Admin SDK" \
    --display-name="ZODIRA Admin SDK"

# Grant permissions
gcloud projects add-iam-policy-binding zodira-astrology \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/datastore.user"

gcloud projects add-iam-policy-binding zodira-astrology \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding zodira-astrology \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/firebase.admin"

# Generate and download key
gcloud iam service-accounts keys create config/serviceAccountKey.json \
    --iam-account=$SERVICE_ACCOUNT_EMAIL
```

### 6. Configure Firebase Authentication

In Firebase Console (https://console.firebase.google.com):

1. **Authentication** > **Sign-in method**
   - Enable **Phone** authentication
   - Enable **Google** authentication
   - Enable **Facebook** authentication (requires Facebook App setup)

2. **Project settings** > **General**
   - Add your domain to authorized domains
   - Configure OAuth redirect URIs

### 7. Deploy Security Rules

Since we're using a Python project, deploy security rules manually through Firebase Console:

1. **Firestore Security Rules**
   - Go to Firebase Console > Firestore Database > Rules
   - Copy the contents of `firestore.rules` file
   - Click "Publish"

2. **Storage Security Rules**
   - Go to Firebase Console > Storage > Rules
   - Copy the contents of `storage.rules` file
   - Click "Publish"

Alternatively, you can use the Firebase Admin SDK to deploy rules programmatically in your Python application.

### 8. Storage Bucket Configuration

```bash
# Create additional storage buckets
PROJECT_ID="zodira-astrology"

gsutil mb -p $PROJECT_ID gs://$PROJECT_ID-profile-images
gsutil mb -p $PROJECT_ID gs://$PROJECT_ID-reports
gsutil mb -p $PROJECT_ID gs://$PROJECT_ID-consultations

# Set up CORS
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

# Apply CORS to all buckets
gsutil cors set cors-config.json gs://$PROJECT_ID.appspot.com
gsutil cors set cors-config.json gs://$PROJECT_ID-profile-images
gsutil cors set cors-config.json gs://$PROJECT_ID-reports
gsutil cors set cors-config.json gs://$PROJECT_ID-consultations

# Clean up
rm cors-config.json
```

### 9. Environment Configuration

Update your `.env` file:

```env
FIREBASE_SERVICE_ACCOUNT_KEY_PATH=config/serviceAccountKey.json
FIREBASE_PROJECT_ID=zodira-astrology
FIREBASE_STORAGE_BUCKET=zodira-astrology.appspot.com

# Razorpay Configuration
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
```

## 🗄️ Database Schema

### Collections Structure

The Firestore database uses the following collections:

#### `/users/{userId}`
```json
{
  "userId": "firebase_auth_uid",
  "email": "user@example.com",
  "phone": "+91-9876543210",
  "displayName": "John Doe",
  "subscriptionType": "free",
  "language": "en",
  "timezone": "Asia/Kolkata",
  "preferences": {...},
  "profileComplete": true,
  "primaryProfileId": "profile_doc_id",
  "createdAt": "2024-01-01T00:00:00Z",
  "lastLoginAt": "2024-01-01T00:00:00Z",
  "isActive": true
}
```

#### `/users/{userId}/profiles/{profileId}`
```json
{
  "profileId": "auto-generated",
  "userId": "firebase_auth_uid",
  "name": "Arjun Patel",
  "birthDate": "1993-08-22",
  "birthTime": "19:15:00",
  "birthPlace": "Ahmedabad, Gujarat, India",
  "latitude": 23.022505,
  "longitude": 72.571365,
  "gender": "male",
  "zodiacSign": "Leo",
  "moonSign": "Cancer",
  "nakshatra": "Magha",
  "createdAt": "2024-01-01T00:00:00Z",
  "updatedAt": "2024-01-01T00:00:00Z",
  "isActive": true
}
```

#### `/marriage-matches/{matchId}`
```json
{
  "matchId": "auto-generated",
  "maleProfileId": "profile_doc_id",
  "femaleProfileId": "profile_doc_id",
  "userId": "firebase_auth_uid",
  "totalGunas": 28,
  "compatibilityScore": 85.5,
  "overallMatch": "Excellent Match",
  "gunaBreakdown": {...},
  "doshaAnalysis": {...},
  "recommendations": [...],
  "createdAt": "2024-01-01T00:00:00Z",
  "expiresAt": "2024-01-31T00:00:00Z"
}
```

#### `/astrologers/{astrologerId}`
```json
{
  "astrologerId": "auto-generated",
  "name": "Dr. Sharma",
  "rating": 4.8,
  "specialization": ["Marriage", "Career"],
  "hourlyRate": 1500,
  "availability": {...},
  "isActive": true,
  "isVerified": true
}
```

#### `/consultations/{consultationId}`
```json
{
  "consultationId": "auto-generated",
  "userId": "firebase_auth_uid",
  "astrologerId": "astrologer_doc_id",
  "scheduledDateTime": "2024-01-15T14:00:00Z",
  "status": "confirmed",
  "totalFee": 750,
  "paymentStatus": "paid"
}
```

#### `/predictions/{predictionId}`
```json
{
  "predictionId": "auto-generated",
  "userId": "firebase_auth_uid",
  "profileId": "profile_doc_id",
  "predictionType": "daily",
  "overallPrediction": "Today brings good fortune...",
  "luckyNumbers": [3, 7, 12],
  "luckyColors": ["Gold", "Green"],
  "generatedAt": "2024-01-01T00:00:00Z",
  "expiresAt": "2024-01-02T00:00:00Z"
}
```

#### `/payments/{paymentId}`
```json
{
  "paymentId": "auto-generated",
  "userId": "firebase_auth_uid",
  "consultationId": "consultation_doc_id",
  "amount": 750,
  "currency": "INR",
  "paymentGateway": "razorpay",
  "status": "completed",
  "createdAt": "2024-01-01T00:00:00Z"
}
```

## 🔒 Security Rules

### Firestore Security Rules

The `firestore.rules` file contains comprehensive security rules ensuring:
- Users can only access their own data
- Astrologer profiles are publicly readable
- Consultations require authentication
- Proper data validation

### Storage Security Rules

The `storage.rules` file defines access control for:
- **Profile Images**: User-owned with public read access
- **Reports**: Private astrology reports and charts
- **Consultations**: Audio/video recordings with access control
- **Public Assets**: Logos, icons with public access

## 🧪 Testing the Setup

### Test Firestore Connection

```python
from config.firebase_config import db

# Test write
doc_ref = db.collection('test').document('test-doc')
doc_ref.set({'message': 'Hello Firebase!', 'timestamp': datetime.utcnow()})

# Test read
doc = doc_ref.get()
print(doc.to_dict())
```

### Test Storage Upload

```python
from firebase_admin import storage
import os

bucket = storage.bucket()
blob = bucket.blob('test/test-file.txt')
blob.upload_from_string('Hello Storage!')
print(blob.public_url)
```

## 🔧 Troubleshooting

### Common Issues

1. **Service Account Key Issues**
   ```bash
   # Regenerate key if lost
   gcloud iam service-accounts keys create config/serviceAccountKey.json \
       --iam-account=zodira-admin-sdk@zodira-astrology.iam.gserviceaccount.com
   ```

2. **Permission Denied**
   ```bash
   # Check service account permissions
   gcloud projects get-iam-policy zodira-astrology \
       --flatten="bindings[].members" \
       --format="table(bindings.role,bindings.members)"
   ```

3. **CORS Issues**
   ```bash
   # Update CORS configuration
   gsutil cors set cors-config.json gs://your-bucket-name
   ```

## 📊 Monitoring & Analytics

### Firebase Console Monitoring

- **Authentication**: Monitor sign-up/sign-in metrics
- **Firestore**: Database usage and performance
- **Storage**: Storage usage and transfer costs
- **Functions**: Execution logs and performance (if using Cloud Functions)

### Cost Optimization

- Set up budget alerts in Google Cloud Console
- Monitor Firestore reads/writes
- Use appropriate storage classes
- Implement data archiving for old records

## 🚀 Deployment

### Backend Deployment

```bash
# Build and deploy to Cloud Run
gcloud run deploy zodira-backend \
    --source . \
    --platform managed \
    --region asia-south1 \
    --allow-unauthenticated
```

### Frontend Deployment

```bash
# Deploy to Firebase Hosting
firebase deploy --only hosting
```

## 📚 Additional Resources

- [Firebase Documentation](https://firebase.google.com/docs)
- [Google Cloud Firestore](https://cloud.google.com/firestore/docs)
- [Firebase Security Rules](https://firebase.google.com/docs/rules)
- [Firebase Admin SDK](https://firebase.google.com/docs/admin/setup)

## 🆘 Support

For issues with Firebase setup:
1. Check Firebase Console logs
2. Verify service account permissions
3. Test with Firebase Admin SDK examples
4. Review security rules for access issues