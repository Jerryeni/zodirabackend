# Firebase Account Migration Guide

## Step-by-Step Guide to Change Firebase Project

This guide provides detailed steps to migrate your ZODIRA project from one Firebase account to another.

## Prerequisites

- Access to the current Firebase project (for data export)
- New Google Cloud account with billing enabled
- Google Cloud SDK installed (`gcloud`)
- Firebase CLI installed (`npm install -g firebase-tools`)

## Step 1: Export Current Data (Optional)

If you need to preserve existing data, export it first:

```bash
# 1.1 Export Firestore data
gcloud firestore export gs://your-current-bucket/firestore-export

# 1.2 Export Authentication users (if needed)
# This requires special permissions and is complex
# Consider recreating users instead of migrating

# 1.3 Download Storage files (if needed)
gsutil cp -r gs://your-current-bucket gs://your-new-bucket
```

## Step 2: Create New Firebase Project

### 2.1 Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **"Create a project"**
3. Enter project details:
   - **Project name**: `ZODIRA Astrology App` (or your preferred name)
   - **Project ID**: Choose a unique ID (e.g., `zodira-astrology-new`)
4. **Enable Google Analytics** (optional)
5. Click **"Create project"**

### 2.2 Enable Required APIs

```bash
# Set your new project
gcloud config set project YOUR_NEW_PROJECT_ID

# Enable required APIs
gcloud services enable firestore.googleapis.com
gcloud services enable firebase.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable identitytoolkit.googleapis.com
gcloud services enable storage-api.googleapis.com
```

### 2.3 Set Up Firebase Services

#### Enable Firestore Database
1. In Firebase Console → **Firestore Database**
2. Click **"Create database"**
3. Choose **"Start in test mode"** (change to production rules later)
4. Select location (recommend: `asia-south1` for India)

#### Enable Authentication
1. In Firebase Console → **Authentication**
2. Click **"Get started"**
3. Go to **"Sign-in method"** tab
4. Enable:
   - **Phone** (for SMS OTP)
   - **Google** (for OAuth)
   - **Facebook** (if needed)

#### Enable Storage
1. In Firebase Console → **Storage**
2. Click **"Get started"**
3. Choose **"Start in test mode"**

## Step 3: Create Service Account

### 3.1 Create Service Account

```bash
# Create service account
SERVICE_ACCOUNT_NAME="zodira-admin-sdk"
SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT_NAME@YOUR_NEW_PROJECT_ID.iam.gserviceaccount.com"

gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
    --description="Service account for ZODIRA backend Firebase Admin SDK" \
    --display-name="ZODIRA Admin SDK"
```

### 3.2 Grant Permissions

```bash
# Grant required roles
gcloud projects add-iam-policy-binding YOUR_NEW_PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/datastore.user"

gcloud projects add-iam-policy-binding YOUR_NEW_PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding YOUR_NEW_PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/firebase.admin"
```

### 3.3 Generate and Download Key

```bash
# Generate new service account key
gcloud iam service-accounts keys create config/serviceAccountKey.json \
    --iam-account=$SERVICE_ACCOUNT_EMAIL

# Verify the key file was created
ls -la config/serviceAccountKey.json
```

## Step 4: Configure Storage Buckets

### 4.1 Create Storage Buckets

```bash
PROJECT_ID="YOUR_NEW_PROJECT_ID"

# Create additional storage buckets
gsutil mb -p $PROJECT_ID gs://$PROJECT_ID-profile-images
gsutil mb -p $PROJECT_ID gs://$PROJECT_ID-reports
gsutil mb -p $PROJECT_ID gs://$PROJECT_ID-consultations
```

### 4.2 Set Up CORS Configuration

```bash
# Create CORS configuration file
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

## Step 5: Update Project Configuration

### 5.1 Update Environment Variables

Edit your `.env` file with new Firebase details:

```env
# Firebase Configuration
FIREBASE_SERVICE_ACCOUNT_KEY_PATH=config/serviceAccountKey.json
FIREBASE_PROJECT_ID=YOUR_NEW_PROJECT_ID
FIREBASE_STORAGE_BUCKET=YOUR_NEW_PROJECT_ID.appspot.com

# Other existing variables remain the same
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
```

### 5.2 Update Firebase Configuration (if needed)

The existing `app/config/firebase.py` should work with the new credentials, but verify:

```python
# app/config/firebase.py
def initialize_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(config('FIREBASE_SERVICE_ACCOUNT_PATH'))
        firebase_admin.initialize_app(cred, {
            'storageBucket': config('FIREBASE_STORAGE_BUCKET')
        })
    return firestore.client(), storage.bucket()
```

### 5.3 Update Authorized Domains

1. In Firebase Console → **Project settings** → **General**
2. Add your domain to **"Authorized domains"**
3. Update **"OAuth redirect URIs"** if using Google OAuth

## Step 6: Deploy Security Rules

### 6.1 Deploy Firestore Rules

```bash
# Deploy using Firebase CLI (if you have firebase.json)
firebase deploy --only firestore:rules

# OR manually through Firebase Console:
# 1. Go to Firebase Console > Firestore Database > Rules
# 2. Copy contents of firestore.rules file
# 3. Click "Publish"
```

### 6.2 Deploy Storage Rules

```bash
# Deploy using Firebase CLI
firebase deploy --only storage

# OR manually through Firebase Console:
# 1. Go to Firebase Console > Storage > Rules
# 2. Copy contents of storage.rules file
# 3. Click "Publish"
```

## Step 7: Test New Configuration

### 7.1 Test Database Connection

Create a test script to verify the connection:

```python
# test_firebase_connection.py
from app.config.firebase import get_firestore_client, initialize_firebase
from datetime import datetime

def test_connection():
    try:
        # Initialize Firebase
        db, bucket = initialize_firebase()
        print("✅ Firebase initialized successfully")

        # Test write operation
        doc_ref = db.collection('test').document('migration-test')
        doc_ref.set({
            'message': 'Migration test successful!',
            'timestamp': datetime.utcnow(),
            'project_id': 'YOUR_NEW_PROJECT_ID'
        })
        print("✅ Test document written successfully")

        # Test read operation
        doc = doc_ref.get()
        if doc.exists:
            print("✅ Test document read successfully")
            print(f"📄 Document data: {doc.to_dict()}")
        else:
            print("❌ Test document not found")

        # Clean up
        doc_ref.delete()
        print("✅ Test document deleted")

        return True

    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
```

Run the test:

```bash
python test_firebase_connection.py
```

### 7.2 Test Authentication

```python
# test_auth.py
from firebase_admin import auth
from app.config.firebase import initialize_firebase

def test_auth():
    try:
        db, bucket = initialize_firebase()
        print("✅ Firebase Auth initialized")

        # Test creating a user (for testing purposes)
        try:
            user = auth.create_user(
                email='test-migration@example.com',
                email_verified=True,
                display_name='Migration Test User'
            )
            print(f"✅ Test user created: {user.uid}")

            # Clean up
            auth.delete_user(user.uid)
            print("✅ Test user deleted")

        except Exception as e:
            print(f"⚠️ User creation test failed: {e}")

        return True

    except Exception as e:
        print(f"❌ Auth test failed: {e}")
        return False

if __name__ == "__main__":
    test_auth()
```

### 7.3 Test Storage

```python
# test_storage.py
from app.config.firebase import get_storage_bucket
from app.config.firebase import initialize_firebase

def test_storage():
    try:
        db, bucket = initialize_firebase()
        print("✅ Firebase Storage initialized")

        # Test file upload
        blob = bucket.blob('test/migration-test.txt')
        blob.upload_from_string('Migration test successful!')
        print("✅ Test file uploaded")

        # Test file download
        content = blob.download_as_text()
        print(f"✅ Test file downloaded: {content}")

        # Clean up
        blob.delete()
        print("✅ Test file deleted")

        return True

    except Exception as e:
        print(f"❌ Storage test failed: {e}")
        return False

if __name__ == "__main__":
    test_storage()
```

## Step 8: Update Application Settings

### 8.1 Update Google OAuth Configuration

If using Google OAuth, update the OAuth consent screen:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **"APIs & Credentials"** → **"OAuth consent screen"**
3. Update authorized redirect URIs to match your new project

### 8.2 Update SMS Configuration

If using SMS services, update webhook URLs in your SMS provider dashboard to point to your new backend endpoints.

### 8.3 Update Payment Gateway

If using Razorpay or other payment gateways:
1. Update webhook URLs in your payment gateway dashboard
2. Ensure webhook secrets are updated if changed

## Step 9: Deploy and Monitor

### 9.1 Deploy Backend

```bash
# If using Cloud Run
gcloud run deploy zodira-backend \
    --source . \
    --platform managed \
    --region asia-south1 \
    --allow-unauthenticated

# If using other deployment methods, follow your standard deployment process
```

### 9.2 Monitor Logs

```bash
# Check Cloud Run logs
gcloud logs tail zodira-backend --region asia-south1

# Check Firebase functions logs (if using)
firebase functions:log
```

### 9.3 Verify All Services

1. **Authentication**: Test user registration and login
2. **Database**: Verify data read/write operations
3. **Storage**: Test file upload/download
4. **Email/SMS**: Verify OTP delivery
5. **Payments**: Test payment flow (if applicable)

## Step 10: Data Migration (If Needed)

### 10.1 Migrate User Data

If you need to migrate existing users:

```python
# migrate_users.py
from firebase_admin import auth
from app.config.firebase import get_firestore_client
import firebase_admin
from firebase_admin import credentials

def migrate_users():
    # This is a complex operation requiring both old and new Firebase apps
    # Consider recreating users instead of migrating for simplicity

    print("User migration requires careful planning")
    print("Consider asking users to re-register with OTP verification")
    print("This is often simpler and more secure than data migration")
```

### 10.2 Migrate Other Data

For other collections, you can:

1. **Export from old project**: Use Firestore export
2. **Import to new project**: Use Firestore import
3. **Manual migration**: Write scripts to read from old and write to new

## Step 11: Clean Up Old Project (Optional)

After successful migration and testing:

1. **Download any remaining data** you need
2. **Update DNS settings** if using custom domains
3. **Cancel old project** if no longer needed (optional)
4. **Delete old service account keys** for security

## Troubleshooting Common Issues

### Issue 1: Service Account Permission Denied

```bash
# Check service account permissions
gcloud projects get-iam-policy YOUR_NEW_PROJECT_ID \
    --flatten="bindings[].members" \
    --format="table(bindings.role,bindings.members)"

# Add missing permissions if needed
gcloud projects add-iam-policy-binding YOUR_NEW_PROJECT_ID \
    --member="serviceAccount:YOUR_SERVICE_ACCOUNT_EMAIL" \
    --role="roles/firebase.admin"
```

### Issue 2: CORS Errors

```bash
# Check CORS configuration
gsutil cors get gs://YOUR_BUCKET_NAME

# Update CORS if needed
gsutil cors set cors-config.json gs://YOUR_BUCKET_NAME
```

### Issue 3: Authentication Domain Issues

1. Verify authorized domains in Firebase Console
2. Check OAuth redirect URIs
3. Ensure your domain is properly configured

### Issue 4: Storage Upload Failures

```bash
# Check storage bucket permissions
gsutil iam get gs://YOUR_BUCKET_NAME

# Grant public access if needed
gsutil iam ch allUsers:objectViewer gs://YOUR_BUCKET_NAME
```

## Security Checklist After Migration

- [ ] Update all service account keys securely
- [ ] Remove old service account keys
- [ ] Update environment variables
- [ ] Test authentication flows
- [ ] Verify security rules are deployed
- [ ] Check CORS configurations
- [ ] Update webhook URLs in external services
- [ ] Test payment integrations
- [ ] Verify email/SMS delivery

## Rollback Plan

If issues occur after migration:

1. **Keep old configuration** as backup
2. **Test thoroughly** before going live
3. **Have rollback script** ready
4. **Monitor closely** for the first few days

## Support Resources

- [Firebase Migration Guide](https://firebase.google.com/docs/projects/manage-projects)
- [Firestore Export/Import](https://cloud.google.com/firestore/docs/manage-data/export-import)
- [Firebase Security Rules](https://firebase.google.com/docs/rules)
- [Google Cloud IAM](https://cloud.google.com/iam/docs)

## Estimated Timeline

- **Project Creation**: 30 minutes
- **Service Configuration**: 1 hour
- **Testing**: 2-3 hours
- **Data Migration**: 1-4 hours (if needed)
- **Total**: 4-8 hours

This migration process ensures a smooth transition to your new Firebase project while maintaining security and functionality.