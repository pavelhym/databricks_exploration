# Deployment Notes

## Important: Branch-Based Deployment

The CI/CD workflow automatically determines the target environment based on the git branch:

- **`main` branch** → deploys to **prod** environment
- **`develop` branch** → deploys to **staging** environment  
- **Any other branch** → deploys to **dev** environment

## To Deploy to Dev

### Option 1: Use a Feature Branch
```bash
git checkout -b feature/my-feature
git push origin feature/my-feature
# This will deploy to dev automatically
```

### Option 2: Manual Trigger
1. Go to GitHub Actions
2. Select "Deploy Streamlit App to Databricks"
3. Click "Run workflow"
4. Select "dev" from the dropdown
5. Click "Run workflow"

### Option 3: Push to a Non-Main Branch
```bash
git checkout -b dev-deployment
git push origin dev-deployment
# This will deploy to dev
```

## Current Issue: App Creation

If you see the error "App with name sales-forecast-app-{env} does not exist", the workflow will now:
1. Check if app exists
2. Create the app if it doesn't exist
3. Then deploy the bundle

This should resolve the "app does not exist" error.
