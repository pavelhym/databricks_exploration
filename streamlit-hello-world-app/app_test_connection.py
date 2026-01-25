import streamlit as st
import os
import sys
import traceback
st.title("🔍 MLflow Diagnostic Tool")
# ============ ENVIRONMENT CHECK ============
st.header("1. Environment Variables")
critical_vars = {
   "DATABRICKS_HOST": os.environ.get("DATABRICKS_HOST"),
   "DATABRICKS_CLIENT_ID": "SET" if os.environ.get("DATABRICKS_CLIENT_ID") else "NOT SET",
   "DATABRICKS_CLIENT_SECRET": "SET" if os.environ.get("DATABRICKS_CLIENT_SECRET") else "NOT SET",
   "DATABRICKS_TOKEN": "SET" if os.environ.get("DATABRICKS_TOKEN") else "NOT SET",
   "MLFLOW_TRACKING_URI": os.environ.get("MLFLOW_TRACKING_URI"),
   "MLFLOW_REGISTRY_URI": os.environ.get("MLFLOW_REGISTRY_URI"),
}
for k, v in critical_vars.items():
   if v and v != "NOT SET":
       st.success(f"✅ {k}: {v}")
   else:
       st.error(f"❌ {k}: {v}")
# ============ SDK CONFIG CHECK ============
st.header("2. Databricks SDK Configuration")
try:
   from databricks.sdk.core import Config
   cfg = Config()
   st.success(f"✅ SDK Host: {cfg.host}")
   st.info(f"Auth Type: {cfg.auth_type}")
except Exception as e:
   st.error(f"❌ SDK Config failed: {e}")
   st.code(traceback.format_exc())
# ============ MLFLOW CONNECTION TEST ============
st.header("3. MLflow Connection Test")
try:
   import mlflow
   st.info(f"MLflow version: {mlflow.__version__}")
   # Set URIs
   os.environ["MLFLOW_USE_DATABRICKS_SDK_MODEL_ARTIFACTS_REPO_FOR_UC"] = "True"
   mlflow.set_tracking_uri("databricks")
   mlflow.set_registry_uri("databricks-uc")
   st.success("✅ MLflow URIs set successfully")
except Exception as e:
   st.error(f"❌ MLflow setup failed: {e}")
   st.code(traceback.format_exc())
# ============ LIST MODELS TEST ============
st.header("4. List Registered Models (API Test)")
try:
   from mlflow.tracking import MlflowClient
   client = MlflowClient()
   # Try to list models - this tests basic connectivity
   models = client.search_registered_models(max_results=5)
   st.success(f"✅ Found {len(models)} models")
   for m in models[:3]:
       st.write(f"  - {m.name}")
except Exception as e:
   st.error(f"❌ Failed to list models: {e}")
   st.code(traceback.format_exc())
# ============ SPECIFIC MODEL LOAD TEST ============
st.header("5. Load Specific Model")
model_uri = st.text_input("Model URI", value="models:/workspace.default.xgboost_units/2")
if st.button("Test Load Model"):
   try:
       st.info(f"Attempting to load: {model_uri}")
       # Method 1: Direct load
       st.write("**Method 1: Direct mlflow.pyfunc.load_model()**")
       model = mlflow.pyfunc.load_model(model_uri=model_uri)
       st.success(f"✅ Model loaded successfully!")
       st.write(f"Model type: {type(model)}")
   except Exception as e:
       st.error(f"❌ Model load failed: {type(e).__name__}")
       st.code(str(e))
       st.code(traceback.format_exc())
       # Try to get more details
       st.write("**Attempting to get model metadata...**")
       try:
           from mlflow.tracking import MlflowClient
           client = MlflowClient()
           # Parse model name from URI
           model_name = model_uri.replace("models:/", "").rsplit("/", 1)[0]
           version = model_uri.rsplit("/", 1)[1]
           st.write(f"Model name: {model_name}, Version: {version}")
           mv = client.get_model_version(model_name, version)
           st.write(f"Model version info: {mv}")
           st.write(f"Source: {mv.source}")
           st.write(f"Run ID: {mv.run_id}")
           st.write(f"Status: {mv.status}")
       except Exception as e2:
           st.error(f"Metadata fetch also failed: {e2}")
# ============ ALTERNATIVE: REST API TEST ============
st.header("6. Direct REST API Test")
if st.button("Test REST API"):
   try:
       import requests
       from databricks.sdk.core import Config
       cfg = Config()
       headers = cfg.authenticate()
       # Test Unity Catalog API
       url = f"{cfg.host}/api/2.1/unity-catalog/models"
       response = requests.get(url, headers=headers)
       st.write(f"Status: {response.status_code}")
       if response.status_code == 200:
           st.success("✅ REST API works!")
           data = response.json()
           st.json(data.get("registered_models", [])[:2])
       else:
           st.error(f"❌ REST API failed: {response.text}")
   except Exception as e:
       st.error(f"REST API test failed: {e}")
       st.code(traceback.format_exc())