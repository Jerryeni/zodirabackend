# Firebase Migration Checklist

## Quick Reference Guide

### Phase 1: Pre-Migration Planning
- [ ] Assess data migration needs (users, profiles, etc.)
- [ ] Choose new project name and ID
- [ ] Set up billing on new Google Cloud account
- [ ] Install required tools (gcloud, firebase-tools)

### Phase 2: New Firebase Project Setup
- [ ] Create new Firebase project in console
- [ ] Enable required APIs (Firestore, Auth, Storage, etc.)
- [ ] Set up Firestore database in desired region
- [ ] Enable Authentication providers (Phone, Google, Facebook)
- [ ] Enable Cloud Storage

### Phase 3: Service Account & Permissions
- [ ] Create service account (`zodira-admin-sdk`)
- [ ] Grant required roles:
  - `roles/datastore.user`
  - `roles/storage.admin`
  - `roles/firebase.admin`
- [ ] Generate and download service account key
- [ ] Store key securely in `config/serviceAccountKey.json`

### Phase 4: Storage Configuration
- [ ] Create additional storage buckets:
  - `PROJECT_ID-profile-images`
  - `PROJECT_ID-reports`
  - `PROJECT_ID-consultations`
- [ ] Configure CORS settings for all buckets
- [ ] Test bucket permissions

### Phase 5: Environment Configuration
- [ ] Update `.env` file:
  ```env
  FIREBASE_PROJECT_ID=your-new-project-id
  FIREBASE_STORAGE_BUCKET=your-new-project-id.appspot.com
  FIREBASE_SERVICE_ACCOUNT_KEY_PATH=config/serviceAccountKey.json
  ```
- [ ] Update authorized domains in Firebase Console
- [ ] Update OAuth redirect URIs if using Google Auth

### Phase 6: Security Rules Deployment
- [ ] Deploy Firestore security rules
- [ ] Deploy Storage security rules
- [ ] Test security rules with authentication

### Phase 7: Testing & Verification
- [ ] Run `python test_firebase_connection.py`
- [ ] Test user registration and authentication
- [ ] Test database read/write operations
- [ ] Test file upload/download to storage
- [ ] Test OTP delivery (email/SMS)
- [ ] Test payment integration (if applicable)

### Phase 8: External Service Updates
- [ ] Update webhook URLs in SMS provider
- [ ] Update webhook URLs in payment gateway
- [ ] Update OAuth callback URLs
- [ ] Test all external integrations

### Phase 9: Deployment
- [ ] Deploy backend to new environment
- [ ] Update DNS settings if needed
- [ ] Monitor application logs
- [ ] Verify all features work correctly

### Phase 10: Post-Migration Cleanup
- [ ] Archive old Firebase project (optional)
- [ ] Delete old service account keys
- [ ] Update documentation with new project details
- [ ] Monitor costs and usage

## Quick Commands Reference

```bash
# Set new project
gcloud config set project YOUR_NEW_PROJECT_ID

# Create service account
gcloud iam service-accounts create zodira-admin-sdk \
    --description="ZODIRA Admin SDK" \
    --display-name="ZODIRA Admin SDK"

# Generate key
gcloud iam service-accounts keys create config/serviceAccountKey.json \
    --iam-account=zodira-admin-sdk@YOUR_NEW_PROJECT_ID.iam.gserviceaccount.com

# Test connection
python test_firebase_connection.py
```

## Common Issues & Solutions

### Permission Denied Errors
- Check service account roles in IAM
- Verify key file path and permissions
- Ensure project ID is correct

### CORS Issues
- Verify CORS configuration on storage buckets
- Check authorized domains in Firebase Auth

### Authentication Failures
- Confirm authorized domains include your domain
- Check OAuth redirect URIs configuration
- Verify service account key is valid

## Emergency Contacts

- **Firebase Console**: https://console.firebase.google.com/
- **Google Cloud Console**: https://console.cloud.google.com/
- **Firebase Documentation**: https://firebase.google.com/docs
- **Stack Overflow**: Tag `firebase` and `python`

## Success Criteria

✅ All tests in `test_firebase_connection.py` pass
✅ User registration and login work
✅ Database operations function correctly
✅ File storage operations work
✅ OTP delivery functions
✅ External integrations work
✅ Application deploys successfully
✅ No errors in application logs

---

*Last updated: $(date)*
*Migration Guide Version: 1.0*