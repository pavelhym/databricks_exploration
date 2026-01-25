# Databricks Project with CI/CD

This project contains a Streamlit application for JARDIANCE Sales Forecasting, configured for deployment to Databricks using Databricks Asset Bundles (DABS) with CI/CD automation.

## Project Structure

```
databricks/
├── databricks.yml              # DABS bundle configuration
├── streamlit-hello-world-app/  # Streamlit application
│   ├── app.py                  # Main Streamlit app
│   ├── app.yaml                # App configuration
│   └── requirements.txt        # Python dependencies
├── .github/workflows/          # GitHub Actions CI/CD
│   └── deploy-databricks.yml
└── DEPLOYMENT.md               # Detailed deployment guide
```

## Quick Start

### Prerequisites

1. **Install Databricks CLI** (version 0.250.0 or above):
   ```bash
   curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh
   ```

2. **Authenticate**:
   ```bash
   databricks auth login
   ```

### Local Deployment

1. **Validate configuration**:
   ```bash
   databricks bundle validate -t dev
   ```

2. **Deploy to development**:
   ```bash
   databricks bundle deploy -t dev
   ```

3. **Deploy the app** (after bundle deployment):
   ```bash
   databricks bundle run sales-forecast-app -t dev
   ```

### CI/CD Setup

This project includes CI/CD workflows for automated deployment:

- **GitHub Actions**: See `.github/workflows/deploy-databricks.yml`

For detailed setup instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Environments

- **dev**: Development environment (default)
- **staging**: Staging environment
- **prod**: Production environment

## Documentation

- [QUICK_START.md](QUICK_START.md) - Quick start guide with step-by-step instructions
- [DEPLOYMENT.md](DEPLOYMENT.md) - Complete deployment guide with CI/CD setup
- [QUICK_START_RU.md](QUICK_START_RU.md) - Подробная инструкция на русском языке
- [Databricks Asset Bundles Docs](https://docs.databricks.com/dev-tools/bundles/index.html)

## Features

- ✅ Streamlit app for sales forecasting
- ✅ MLflow model integration
- ✅ Unity Catalog support
- ✅ Multi-environment deployment (dev/staging/prod)
- ✅ CI/CD automation (GitHub Actions)
- ✅ Infrastructure as Code with DABS