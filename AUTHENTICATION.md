# Authentication Guide for Databricks CLI

## Local Authentication

### Method 1: Interactive Login (Recommended)

```bash
# This will open a browser for OAuth authentication
databricks auth login
```

This is the easiest method for local development. It will:
- Open your browser
- Ask you to log in to Databricks
- Automatically configure authentication

### Method 2: Using Personal Access Token (PAT)

If you prefer using a token:

1. **Create a Personal Access Token in Databricks:**
   - Log in to Databricks workspace
   - Click on your user icon (top right) → User Settings
   - Go to "Access Tokens" tab
   - Click "Generate New Token"
   - Copy the token (it's only shown once!)

2. **Set environment variables:**

   **Windows (PowerShell):**
   ```powershell
   $env:DATABRICKS_HOST = "https://dbc-5eabeaeb-998c.cloud.databricks.com"
   $env:DATABRICKS_TOKEN = "your-token-here"
   ```

   **Windows (Command Prompt):**
   ```cmd
   set DATABRICKS_HOST=https://dbc-5eabeaeb-998c.cloud.databricks.com
   set DATABRICKS_TOKEN=your-token-here
   ```

   **Linux/Mac:**
   ```bash
   export DATABRICKS_HOST="https://dbc-5eabeaeb-998c.cloud.databricks.com"
   export DATABRICKS_TOKEN="your-token-here"
   ```

3. **Verify authentication:**
   ```bash
   databricks auth env
   ```

### Method 3: Using Databricks Config File

You can also create a config file at `~/.databrickscfg`:

```ini
[DEFAULT]
host = https://dbc-5eabeaeb-998c.cloud.databricks.com
token = your-token-here
```

## Verify Authentication

After authenticating, verify it works:

```bash
# Check authentication status
databricks auth env

# Test with a simple command
databricks workspace ls
```

## Troubleshooting 401 Errors

If you get a 401 Unauthorized error:

1. **Check if you're authenticated:**
   ```bash
   databricks auth env
   ```

2. **Re-authenticate:**
   ```bash
   databricks auth login
   ```

3. **Check token expiration:**
   - Personal Access Tokens can expire
   - Generate a new token if needed

4. **Verify workspace host:**
   - Make sure the host URL is correct
   - Should be: `https://dbc-5eabeaeb-998c.cloud.databricks.com`
   - Don't include trailing slashes

5. **Check permissions:**
   - Your user needs "Can Manage Apps" permission
   - Your user needs "Can Manage Workspace" permission

## For CI/CD (GitHub Actions)

In CI/CD, authentication is handled via environment variables set in GitHub Secrets:
- `DATABRICKS_HOST`
- `DATABRICKS_TOKEN`

These are automatically used by the Databricks CLI in the workflow.
