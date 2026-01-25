# CI/CD Troubleshooting Guide

## 401 Authentication Error in GitHub Actions

If you're getting a 401 error in GitHub Actions but it works locally, check the following:

### 1. Verify GitHub Secrets are Set

Go to your GitHub repository:
- **Settings** → **Secrets and variables** → **Actions**
- Make sure you have:
  - `DATABRICKS_HOST` - Should be: `dbc-5eabeaeb-998c.cloud.databricks.com` (WITHOUT `https://`)
  - `DATABRICKS_TOKEN` - Your Personal Access Token

### 2. Check Secret Values

**Important:** The `DATABRICKS_HOST` should be:
- ✅ Correct: `dbc-5eabeaeb-998c.cloud.databricks.com`
- ❌ Wrong: `https://dbc-5eabeaeb-998c.cloud.databricks.com`

The Databricks CLI automatically adds the `https://` prefix, so don't include it in the secret.

### 3. Verify Token is Valid

1. Go to Databricks workspace
2. User Settings → Access Tokens
3. Check if your token is still active (not expired)
4. If expired, generate a new token and update the GitHub secret

### 4. Check Token Permissions

Your token needs these permissions:
- ✅ Can Manage Apps
- ✅ Can Manage Workspace
- ✅ Can Access SQL Warehouses (if your app uses SQL)

### 5. Test Locally with Same Credentials

Test if the token works locally:

```bash
# Set environment variables (Windows PowerShell)
$env:DATABRICKS_HOST = "dbc-5eabeaeb-998c.cloud.databricks.com"
$env:DATABRICKS_TOKEN = "your-token-here"

# Test authentication
databricks auth env

# Test bundle validation
databricks bundle validate -t prod
```

If this works locally but fails in CI/CD, the issue is likely:
- Secret not set correctly in GitHub
- Wrong format (e.g., extra spaces, wrong host format)

### 6. Check GitHub Actions Logs

In the GitHub Actions run, look for:
- The "Verify Databricks authentication" step
- Check if it shows:
  - ✅ DATABRICKS_HOST is set: ...
  - ✅ DATABRICKS_TOKEN is set (length: ...)

If you see "ERROR: DATABRICKS_HOST is not set" or "ERROR: DATABRICKS_TOKEN is not set", the secrets aren't configured.

### 7. Common Issues

**Issue: Secret shows as empty**
- Make sure you saved the secret after creating it
- Check for typos in secret names (case-sensitive!)
- Secrets must be named exactly: `DATABRICKS_HOST` and `DATABRICKS_TOKEN`

**Issue: Token expired**
- Generate a new token in Databricks
- Update the `DATABRICKS_TOKEN` secret in GitHub

**Issue: Wrong host format**
- Host should be: `dbc-5eabeaeb-998c.cloud.databricks.com`
- NOT: `https://dbc-5eabeaeb-998c.cloud.databricks.com`
- NOT: `dbc-5eabeaeb-998c.cloud.databricks.com/`

### 8. Debug Steps

Add this to your workflow temporarily to debug:

```yaml
- name: Debug environment
  run: |
    echo "Host length: ${#DATABRICKS_HOST}"
    echo "Token length: ${#DATABRICKS_TOKEN}"
    echo "Host starts with: ${DATABRICKS_HOST:0:5}"
```

This will help verify secrets are set without exposing them.

## Still Having Issues?

1. Double-check secret names are exactly: `DATABRICKS_HOST` and `DATABRICKS_TOKEN`
2. Verify the token works locally with the same values
3. Check GitHub Actions logs for the exact error message
4. Make sure your GitHub repository has Actions enabled
