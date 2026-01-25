# CI/CD Deployment Guide for Databricks Asset Bundles (DABS)

This guide explains how to use Databricks Asset Bundles (DABS) to enable CI/CD for deploying your Streamlit app to Databricks.

## Overview

Databricks Asset Bundles (DABS) allows you to:
- Define your Databricks resources (apps, jobs, pipelines) as code
- Deploy to multiple environments (dev, staging, prod)
- Automate deployments via CI/CD pipelines
- Version control your Databricks configurations

## Prerequisites

1. **Databricks CLI** installed and configured
   ```bash
   # Install Databricks CLI
   curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh
   
   # Authenticate
   databricks auth login
   ```

2. **Databricks Personal Access Token (PAT)** or OAuth credentials
   - Create a PAT in Databricks: User Settings → Access Tokens
   - Or configure OAuth via `databricks auth login`

3. **Required permissions** in Databricks workspace:
   - Can Manage Apps
   - Can Manage Workspace (for workspace directory)

## Project Structure

```
databricks/
├── databricks.yml          # Bundle configuration
├── streamlit-hello-world-app/
│   ├── app.py              # Streamlit application
│   ├── app.yaml            # App configuration
│   └── requirements.txt    # Python dependencies
└── .github/workflows/      # GitHub Actions (if using GitHub)
    └── deploy-databricks.yml
```

## Configuration

### 1. Bundle Configuration (`databricks.yml`)

The `databricks.yml` file defines:
- **Resources**: Your Streamlit app
- **Targets**: Different environments (dev, staging, prod)
- **Variables**: Environment-specific configuration

Key sections:
- `resources.apps`: Defines your Streamlit app
- `targets`: Environment configurations (dev, staging, prod)
- `variables`: Environment variables for each target

### 2. App Configuration (`streamlit-hello-world-app/app.yaml`)

The `app.yaml` file defines how to run your Streamlit app:
- Command to execute
- Environment variables
- Resource requirements

## Local Deployment

### Validate Configuration

```bash
# Validate the bundle configuration
databricks bundle validate -t dev
```

### Deploy to Development

```bash
# Deploy to dev environment
databricks bundle deploy -t dev

# Deploy with dry-run (preview changes)
databricks bundle deploy -t dev --dry-run
```

### Deploy to Other Environments

```bash
# Deploy to staging
databricks bundle deploy -t staging

# Deploy to production
databricks bundle deploy -t prod
```

## CI/CD Setup

### GitHub Actions

1. **Set up GitHub Secrets**:
   - Go to your repository → Settings → Secrets and variables → Actions
   - Add the following secrets:
     - `DATABRICKS_HOST`: Your Databricks workspace URL (e.g., `https://dbc-xxxxx.cloud.databricks.com`)
     - `DATABRICKS_TOKEN`: Your Databricks Personal Access Token

2. **Workflow Behavior**:
   - **Pull Requests**: Validates configuration only (no deployment)
   - **Push to `develop`**: Deploys to staging environment
   - **Push to `main`**: Deploys to production environment
   - **Manual Trigger**: Allows you to choose target environment

3. **Manual Deployment**:
   - Go to Actions → Deploy Streamlit App to Databricks → Run workflow
   - Select target environment (dev/staging/prod)

### GitLab CI

1. **Set up GitLab CI/CD Variables**:
   - Go to your project → Settings → CI/CD → Variables
   - Add:
     - `DATABRICKS_HOST`: Your Databricks workspace URL
     - `DATABRICKS_TOKEN`: Your Databricks Personal Access Token

2. **Pipeline Behavior**:
   - **Merge Requests**: Validates configuration
   - **Push to `develop`**: Auto-deploys to dev
   - **Push to `staging`**: Manual deploy to staging
   - **Push to `main`**: Manual deploy to production

## Environment Variables

The following environment variables are configured per environment:

- `DATABRICKS_HOST`: Databricks workspace hostname
- `DATABRICKS_SQL_HTTP_PATH`: SQL Warehouse HTTP path
- `DATABRICKS_TOKEN`: Personal Access Token (set in CI/CD secrets, not in bundle)

### Adding More Environment Variables

Edit `databricks.yml` and add variables under each target:

```yaml
targets:
  dev:
    variables:
      MY_CUSTOM_VAR: "value"
      ANOTHER_VAR: "another-value"
```

## Deployment Workflow

1. **Development**:
   ```bash
   # Make changes to your app
   git checkout -b feature/my-feature
   # ... make changes ...
   git commit -m "Add new feature"
   git push origin feature/my-feature
   ```

2. **Create Pull Request**:
   - CI/CD validates the configuration
   - Review and merge when ready

3. **Automatic Deployment**:
   - Merging to `develop` → deploys to staging
   - Merging to `main` → deploys to production

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   ```bash
   # Re-authenticate
   databricks auth login
   ```

2. **Validation Errors**:
   ```bash
   # Check bundle syntax
   databricks bundle validate -t dev
   ```

3. **Deployment Failures**:
   - Check Databricks workspace permissions
   - Verify environment variables are set correctly
   - Check app.yaml syntax

4. **App Not Found After Deployment**:
   - Check workspace directory path in `databricks.yml`
   - Verify app name doesn't conflict with existing apps

### Debugging

```bash
# Enable verbose logging
databricks bundle deploy -t dev --debug

# Check bundle state
databricks bundle state -t dev
```

## Best Practices

1. **Environment Separation**:
   - Use different app names per environment (e.g., `sales-forecast-app-dev`, `sales-forecast-app-prod`)
   - Use environment-specific variables

2. **Version Control**:
   - Always commit `databricks.yml` changes
   - Use feature branches for testing

3. **Security**:
   - Never commit tokens or secrets to git
   - Use CI/CD secrets/variables for sensitive data
   - Rotate tokens regularly

4. **Testing**:
   - Test in dev environment first
   - Use dry-run before production deployments
   - Validate configuration in PRs

## Advanced Configuration

### Multiple Apps

To deploy multiple Streamlit apps:

```yaml
resources:
  apps:
    app1:
      name: my-first-app
      path: streamlit-app-1
    app2:
      name: my-second-app
      path: streamlit-app-2
```

### Custom Workspace Paths

```yaml
resources:
  apps:
    sales-forecast-app:
      workspace_dir: /Workspace/custom/path/apps
```

### Resource Limits

Configure app resources in `app.yaml`:

```yaml
resources:
  requests:
    cpu: "2"
    memory: "4Gi"
  limits:
    cpu: "4"
    memory: "8Gi"
```

## References

- [Databricks Asset Bundles Documentation](https://docs.databricks.com/dev-tools/bundles/index.html)
- [Databricks CLI Documentation](https://docs.databricks.com/dev-tools/cli/index.html)
- [Streamlit on Databricks](https://docs.databricks.com/apps/streamlit/index.html)

## Support

For issues or questions:
1. Check Databricks documentation
2. Review bundle validation output
3. Check CI/CD logs for detailed error messages
