# Deployment Setup Summary

## What Was Configured

### 1. Bundle Configuration (`databricks.yml`)
- ✅ App configured for dev environment: `sales-forecast-app-dev`
- ✅ Proper workspace root path: `/Workspace/.bundle/databricks/dev`
- ✅ App permissions configured (CAN_MANAGE for current user, CAN_USE for users group)

### 2. CI/CD Workflow (`.github/workflows/deploy-databricks.yml`)
The workflow now:
- ✅ Validates bundle configuration
- ✅ **Deletes existing app** before deploying (prevents conflicts)
- ✅ Deploys the new bundle version
- ✅ Attempts to retrieve service principal ID for permissions
- ✅ **Starts the application** after deployment

### 3. Database Access Permissions

The app needs access to:
- `workspace.default` catalog and schema
- Tables: `workspace.default.gross_sales_monthly`
- MLflow models: `workspace.default.xgboost_units`, `workspace.default.jardiance_arima_pkg_7`

## Granting Database Permissions

After the app is deployed, you need to grant Unity Catalog permissions to the app's service principal.

### Step 1: Get the Service Principal ID

After deployment, the CI/CD workflow will show the service principal ID in the logs. Alternatively, you can get it via:

```bash
databricks apps get --name sales-forecast-app-dev --output json | jq -r '.service_principal_client_id'
```

### Step 2: Grant Permissions

Run these SQL commands in Databricks SQL Editor (replace `<SERVICE_PRINCIPAL_ID>` with the actual ID):

```sql
-- Grant catalog access
GRANT USE CATALOG ON CATALOG workspace TO `<SERVICE_PRINCIPAL_ID>`;

-- Grant schema access
GRANT USE SCHEMA ON SCHEMA workspace.default TO `<SERVICE_PRINCIPAL_ID>`;

-- Grant SELECT on schema (allows reading tables)
GRANT SELECT ON SCHEMA workspace.default TO `<SERVICE_PRINCIPAL_ID>`;

-- Grant READ VOLUME if needed
GRANT READ VOLUME ON SCHEMA workspace.default TO `<SERVICE_PRINCIPAL_ID>`;
```

### Alternative: Use the SQL Script

A SQL script is available at `scripts/grant_app_permissions.sql`. Edit it with your service principal ID and run it in Databricks SQL.

## Deployment Process

### Manual Deployment (Dev)

```bash
# 1. Validate configuration
databricks bundle validate -t dev

# 2. Delete existing app (if needed)
databricks apps delete --name sales-forecast-app-dev

# 3. Deploy bundle
databricks bundle deploy -t dev

# 4. Start the app
databricks apps deploy --name sales-forecast-app-dev

# 5. Grant permissions (see above)
```

### Automatic Deployment via CI/CD

1. Push to `develop` branch → deploys to staging
2. Push to `main` branch → deploys to production
3. Manual trigger → choose target environment

The CI/CD workflow automatically:
- Deletes old app version
- Deploys new version
- Starts the app
- Provides service principal ID for permission grants

## Accessing the App

After deployment, access your app at:
```
https://dbc-5eabeaeb-998c.cloud.databricks.com/apps/sales-forecast-app-dev
```

## Troubleshooting

### App Not Starting
- Check app logs in Databricks UI
- Verify all dependencies are in `requirements.txt`
- Check `app.yaml` configuration

### Database Access Denied
- Verify service principal permissions are granted
- Check that the service principal ID is correct
- Ensure you have MANAGE privilege on the schema to grant permissions

### Deployment Fails
- Check GitHub Actions logs
- Verify `DATABRICKS_HOST` and `DATABRICKS_TOKEN` secrets are set
- Ensure token has "Can Manage Apps" permission

## Next Steps

1. ✅ Deploy to dev environment
2. ✅ Grant database permissions to service principal
3. ✅ Test the app functionality
4. ✅ Deploy to staging/production when ready
