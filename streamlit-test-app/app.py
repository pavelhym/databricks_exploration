import json
import os
import time
from datetime import datetime

import mlflow
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from databricks.sdk.core import Config
from mlflow.tracking import MlflowClient

from databricks import sql

st.set_page_config(page_title="Product X Sales Forecast", layout="wide")

st.title("🏥 Product X Sales Forecasting")
st.markdown("*Predictive analytics for sales*")

TOKEN = os.getenv("DATABRICKS_TOKEN")

# Only remove OAuth credentials if using PAT to avoid auth conflicts
if TOKEN:
    for key in ["DATABRICKS_CLIENT_ID", "DATABRICKS_CLIENT_SECRET"]:
        os.environ.pop(key, None)
WORKSPACE_HOST = os.getenv("DATABRICKS_HOST", "dbc-5eabeaeb-998c.cloud.databricks.com")
ARIMA_ENDPOINT = os.getenv("ARIMA_ENDPOINT_NAME", "jardiance_arima_pkg_7")
XGB_ENDPOINT = os.getenv("XGB_ENDPOINT_NAME", "xgboost_units")
XGB_ENDPOINT_OVERRIDE = os.getenv("XGB_ENDPOINT_URL")
XGB_FEATURE_SPEC = os.getenv("XGB_FEATURE_SPEC", "")

if not WORKSPACE_HOST.startswith("http"):
    WORKSPACE_URL = f"https://{WORKSPACE_HOST}"
else:
    WORKSPACE_URL = WORKSPACE_HOST

# Ensure DATABRICKS_HOST has https:// scheme
if "DATABRICKS_HOST" in os.environ:
    if not os.environ["DATABRICKS_HOST"].startswith("http"):
        os.environ["DATABRICKS_HOST"] = f"https://{os.environ['DATABRICKS_HOST']}"
else:
    os.environ["DATABRICKS_HOST"] = WORKSPACE_URL

# Configure MLflow for Unity Catalog
os.environ["MLFLOW_USE_DATABRICKS_SDK_MODEL_ARTIFACTS_REPO_FOR_UC"] = "True"

XGB_MODEL_NAME = os.getenv("XGB_UC_MODEL_NAME", "workspace.default.xgboost_units")
ARIMA_MODEL_NAME = os.getenv(
    "ARIMA_UC_MODEL_NAME", "workspace.default.jardiance_arima_pkg_7"
)
XGB_CATEGORICAL_MAP = os.getenv(
    "XGB_CATEGORICAL_MAP",
    json.dumps(
        {
            "product_id": {"JARDIANCE": 0, "OFEV": 1},
            "channel": {
                "CASH_RETAIL": 0,
                "CHARGEBACKS_340B": 1,
                "MANAGED_CARE": 2,
                "MEDICAID": 3,
                "MEDICARE_PART_D": 4,
            },
        }
    ),
)


@st.cache_resource(ttl=3600)  # Cache connection for 1 hour
def get_connection(http_path: str):
    """
    Get cached SQL Warehouse connection using Databricks SDK pattern.
    """
    from databricks.sdk.core import Config

    try:
        st.info("🔧 Step 1: Initializing Databricks SDK Config...")
        cfg = Config()

        # DEBUG: Print ALL Config attributes
        st.write("**🔍 DEBUG: Config Object Details**")
        st.code(f"Config type: {type(cfg)}")
        st.code(f"Config host: {cfg.host}")
        st.code(f"Config repr: {repr(cfg)}")

        # DEBUG: Print authenticate method
        st.write("**🔍 DEBUG: Authenticate Method**")
        st.code(f"authenticate type: {type(cfg.authenticate)}")
        st.code(f"authenticate: {cfg.authenticate}")

        # DEBUG: Call authenticate and print result
        st.write("**🔍 DEBUG: Calling cfg.authenticate()**")
        auth_result = cfg.authenticate()
        st.code(f"authenticate() result type: {type(auth_result)}")
        st.code(f"authenticate() result: {auth_result}")

        st.success(f"✅ Config initialized - Host: {cfg.host}")
    except Exception as e:
        st.error(f"❌ Failed to initialize Config: {type(e).__name__}: {e}")
        import traceback

        st.code(traceback.format_exc())
        raise

    try:
        st.info("🔌 Step 2: Connecting to SQL Warehouse...")
        st.code(f"server_hostname: {cfg.host}")
        st.code(f"http_path: {http_path}")
        st.code("credentials_provider: lambda: cfg.authenticate()")

        conn = sql.connect(
            server_hostname=cfg.host,
            http_path=http_path,
            credentials_provider=lambda: cfg.authenticate(),
            _socket_timeout=30,  # 30 second timeout for connection
        )
        st.success("✅ SQL Warehouse connection established!")
        return conn
    except Exception as e:
        st.error(f"❌ Failed to connect to SQL Warehouse: {type(e).__name__}: {e}")
        import traceback

        with st.expander("🔍 Full Connection Error"):
            st.code(traceback.format_exc())
        raise


@st.cache_data(ttl=3600)  # Cache data for 1 hour
def read_table(
    table_name: str = "workspace.default.gross_sales_monthly",
    http_path: str = "/sql/1.0/warehouses/e2e25fceda9c1031",
) -> pd.DataFrame:
    """Read Delta table from Unity Catalog using Arrow format."""
    try:
        st.info(f"📊 Reading {table_name} from Unity Catalog...")

        # Step 1: Initialize Config and establish connection
        try:
            from databricks.sdk.core import Config

            st.info("🔧 Step 1a: Initializing Databricks SDK Config...")
            cfg = Config()

            # DEBUG: Print ALL Config attributes
            st.write("**🔍 DEBUG: Config Object Details**")
            st.code(f"Config type: {type(cfg)}")
            st.code(f"Config host: {cfg.host}")
            st.code(f"Config repr: {repr(cfg)}")

            # DEBUG: Print authenticate method
            st.write("**🔍 DEBUG: Authenticate Method**")
            st.code(f"authenticate type: {type(cfg.authenticate)}")
            st.code(f"authenticate: {cfg.authenticate}")

            # DEBUG: Call authenticate and print result
            st.write("**🔍 DEBUG: Calling cfg.authenticate()**")
            auth_result = cfg.authenticate()
            st.code(f"authenticate() result type: {type(auth_result)}")
            st.code(f"authenticate() result: {auth_result}")

            # DEBUG: Test what lambda returns
            st.write("**🔍 DEBUG: Lambda Test**")
            test_lambda = lambda: cfg.authenticate
            test_result = test_lambda()
            st.code(f"lambda: cfg.authenticate returns type: {type(test_result)}")
            st.code(f"lambda: cfg.authenticate returns: {test_result}")

            st.success(f"✅ Config initialized - Host: {cfg.host}")

            # Step 1b: Connect to SQL Warehouse
            st.info("🔌 Step 1b: Connecting to SQL Warehouse...")
            st.code(f"server_hostname: {cfg.host}")
            st.code(f"http_path: {http_path}")
            st.code("credentials_provider: lambda: cfg.authenticate (NO parentheses)")

            conn = sql.connect(
                server_hostname=cfg.host,
                http_path=http_path,
                credentials_provider=lambda: cfg.authenticate,
                _socket_timeout=30,  # 30 second timeout for connection
            )
            st.success("✅ SQL Warehouse connection established!")

        except Exception as conn_error:
            st.error(f"❌ Connection failed: {type(conn_error).__name__}: {conn_error}")
            import traceback

            with st.expander("🔍 Full Connection Error"):
                st.code(traceback.format_exc())
            raise

        # Step 2: Create cursor
        try:
            st.info("📝 Step 3: Creating cursor...")
            cursor = conn.cursor()
            st.success("✅ Cursor created!")
        except Exception as cursor_error:
            st.error(
                f"❌ Failed to create cursor: {type(cursor_error).__name__}: {cursor_error}"
            )
            conn.close()
            raise

        # Step 3: Execute query
        try:
            st.info("🔍 Step 4: Executing query...")
            query = f"SELECT * FROM {table_name}"
            cursor.execute(query)
            st.success("✅ Query executed!")
        except Exception as query_error:
            st.error(
                f"❌ Failed to execute query: {type(query_error).__name__}: {query_error}"
            )
            cursor.close()
            conn.close()
            raise

        # Step 4: Fetch results using Arrow format
        try:
            st.info("📥 Step 5: Fetching results via Arrow format...")
            arrow_table = cursor.fetchall_arrow()
            st.success("✅ Fetched Arrow table!")
        except Exception as fetch_error:
            st.error(
                f"❌ Failed to fetch Arrow data: {type(fetch_error).__name__}: {fetch_error}"
            )
            cursor.close()
            conn.close()
            raise

        # Step 5: Convert to Pandas
        try:
            st.info("🐼 Step 6: Converting to Pandas DataFrame...")
            df = arrow_table.to_pandas()
            st.success(f"✅ Loaded {len(df):,} rows from Delta table")
        except Exception as pandas_error:
            st.error(
                f"❌ Failed to convert to Pandas: {type(pandas_error).__name__}: {pandas_error}"
            )
            cursor.close()
            conn.close()
            raise

        # Cleanup
        cursor.close()
        conn.close()

        return df

    except Exception as e:
        st.error(f"❌ Overall read_table failed: {type(e).__name__}: {e}")

        # Fallback to CSV
        st.info("📁 Falling back to CSV...")
        try:
            df = pd.read_csv("app/data/sap/gross_sales_monthly.csv")
            st.success(f"✅ Loaded {len(df):,} rows from CSV")
            return df
        except Exception as csv_error:
            st.error(f"❌ CSV fallback failed: {csv_error}")
            return pd.DataFrame()


@st.cache_resource(show_spinner=False)
def load_uc_model(model_name: str):
    # Initialize SDK Config for authentication (required before MLflow operations)
    cfg = Config()

    # Set MLflow URIs
    mlflow.set_tracking_uri("databricks")
    mlflow.set_registry_uri("databricks-uc")

    client = MlflowClient()

    # Get latest version
    versions = client.search_model_versions(f"name='{model_name}'")
    if not versions:
        raise RuntimeError(f"No registered versions found for '{model_name}'.")
    latest = max(versions, key=lambda mv: int(mv.version))

    model_uri = f"models:/{model_name}/{latest.version}"
    model = mlflow.pyfunc.load_model(model_uri=model_uri)
    return model, latest.version


ARIMA_ENDPOINT_URL = f"{WORKSPACE_URL}/serving-endpoints/{ARIMA_ENDPOINT}/invocations"
XGB_ENDPOINT_URL = f"{WORKSPACE_URL}/serving-endpoints/{XGB_ENDPOINT}/invocations"

st.sidebar.header("⚙️ Forecast Settings (ARIMA)")
forecast_months = st.sidebar.slider("Forecast Horizon (months)", 1, 24, 12)
show_confidence = st.sidebar.checkbox("Show Confidence Intervals", value=True)

with st.sidebar.expander("🔧 System Info"):
    st.code(f"Workspace: {WORKSPACE_URL}")
    st.code(f"ARIMA Endpoint: {ARIMA_ENDPOINT}")
    st.code(f"XGB Endpoint: {XGB_ENDPOINT}")
    auth_method = "PAT" if TOKEN else "OAuth (SDK)"
    st.code(f"Auth: {auth_method}")


def invoke_endpoint(url: str, records):
    if TOKEN:
        headers = {
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
        }
    else:
        # Use Databricks SDK Config for OAuth authentication
        cfg = Config()
        headers = cfg.authenticate()
        headers["Content-Type"] = "application/json"

    response = requests.post(
        url, headers=headers, json={"dataframe_records": records}, timeout=90
    )
    return response


def parse_xgb_schema():
    try:
        cat_map = json.loads(XGB_CATEGORICAL_MAP) or {}
    except json.JSONDecodeError:
        cat_map = {}
    feature_items = [f.strip() for f in XGB_FEATURE_SPEC.split(",") if f.strip()]
    default_numeric = [
        "avg_price",
        "promo_flag",
        "promo_spend",
        "macro_index",
        "seasonality",
        "channel_weight",
        "month",
        "quarter",
        "year",
        "units_sold_lag1",
        "units_sold_lag2",
        "units_sold_lag3",
        "units_sold_lag6",
        "units_sold_lag12",
        "rolling_mean_3",
        "rolling_mean_6",
        "rolling_std_6",
        "promo_rolling_sum_3",
        "avg_price_lag1",
        "avg_price_change_pct",
        "units_sold_diff",
        "units_sold_pct_change",
    ]
    # Define which numeric fields should be integers (long type)
    int_cols = ["promo_flag", "month", "quarter", "year", "promo_rolling_sum_3"]

    if not feature_items:
        feature_items = list(cat_map.keys()) + default_numeric
    cat_cols = list(cat_map.keys())
    num_cols = [f for f in feature_items if f not in cat_cols]
    return feature_items, cat_cols, num_cols, cat_map, int_cols


tabs = st.tabs(
    [
        "ARIMA Served",
        "XGBoost Served",
        "ARIMA MLflow",
        "XGBoost MLflow",
    ]
)

with tabs[0]:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("📊 Generate Forecast")
        st.write("Click to forecast Product X 7-count packages.")
    with col2:
        generate_btn = st.button(
            "🚀 Generate Forecast", type="primary", use_container_width=True
        )

    if generate_btn:
        result = None
        error = None
        status_placeholder = st.empty()
        try:
            status_placeholder.info("📡 Calling ARIMA endpoint...")
            start_time = time.time()
            resp = invoke_endpoint(ARIMA_ENDPOINT_URL, [{"n_periods": forecast_months}])
            elapsed = time.time() - start_time
            status_placeholder.success(f"✅ Response received in {elapsed:.1f}s")
            time.sleep(0.5)
            status_placeholder.empty()
            if resp.status_code != 200:
                try:
                    error = json.dumps(resp.json(), indent=2)
                except Exception:
                    error = resp.text[:500]
            else:
                result = resp.json()
        except requests.exceptions.Timeout:
            error = "Request timeout after 90 seconds."
        except Exception as exc:
            error = str(exc)

        if error:
            st.error("❌ Prediction failed!")
            with st.expander("Error Details"):
                st.code(error)
            st.info("Verify endpoint availability and permissions.")
            st.stop()

        predictions_data = None
        if isinstance(result, dict) and "predictions" in result:
            predictions_data = result["predictions"]
        elif isinstance(result, list):
            predictions_data = result
        else:
            st.error("❌ Unexpected response format")
            with st.expander("View raw response"):
                st.json(result)
            st.stop()

        if not predictions_data:
            st.error("❌ No predictions in response")
            with st.expander("View raw response"):
                st.json(result)
            st.stop()

        forecasts = []
        lower_bounds = []
        upper_bounds = []
        for item in predictions_data:
            forecasts.append(item.get("forecast", 0))
            lower_bounds.append(item.get("lower_bound", 0))
            upper_bounds.append(item.get("upper_bound", 0))

        st.success("✅ Forecast generated successfully!")

        st.subheader("📈 Key Metrics")
        k1, k2, k3, k4 = st.columns(4)
        if forecasts:
            k1.metric("Next Month", f"{int(forecasts[0]):,}")
        if len(forecasts) >= 3:
            k2.metric("3-Month Avg", f"{int(sum(forecasts[:3]) / 3):,}")
        if len(forecasts) >= 6:
            k3.metric("6-Month Avg", f"{int(sum(forecasts[:6]) / 6):,}")
        k4.metric(
            f"{forecast_months}-Month Total",
            f"{int(sum(forecasts[:forecast_months])):,}",
        )

        st.subheader("📊 Forecast Visualization")
        months = list(range(1, len(forecasts) + 1))
        fig = go.Figure()
        if show_confidence:
            fig.add_trace(
                go.Scatter(
                    x=months + months[::-1],
                    y=upper_bounds + lower_bounds[::-1],
                    fill="toself",
                    fillcolor="rgba(46, 204, 113, 0.2)",
                    line=dict(color="rgba(255,255,255,0)"),
                    name="95% Confidence Interval",
                    hoverinfo="skip",
                )
            )
        fig.add_trace(
            go.Scatter(
                x=months,
                y=forecasts,
                mode="lines+markers",
                name="Forecast",
                line=dict(color="#2ecc71", width=3),
                marker=dict(size=8, symbol="circle"),
                hovertemplate="<b>Month %{x}</b><br>Forecast: %{y:,.0f} units<extra></extra>",
            )
        )
        if show_confidence:
            fig.add_trace(
                go.Scatter(
                    x=months,
                    y=upper_bounds,
                    mode="lines",
                    name="Upper Bound",
                    line=dict(color="rgba(46, 204, 113, 0.5)", width=1, dash="dash"),
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=months,
                    y=lower_bounds,
                    mode="lines",
                    name="Lower Bound",
                    line=dict(color="rgba(46, 204, 113, 0.5)", width=1, dash="dash"),
                )
            )
        fig.update_layout(
            title="Product X 7-Count Package Forecast with Confidence Intervals",
            xaxis_title="Month",
            yaxis_title="Forecasted Units",
            height=500,
            hovermode="x unified",
            showlegend=True,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📋 Detailed Forecast Data")
        forecast_df = pd.DataFrame(
            {
                "Month": months,
                "Forecast": [int(x) for x in forecasts],
                "Lower Bound (95%)": [int(x) for x in lower_bounds],
                "Upper Bound (95%)": [int(x) for x in upper_bounds],
                "Cumulative": [
                    int(sum(forecasts[: i + 1])) for i in range(len(forecasts))
                ],
            }
        )
        st.dataframe(
            forecast_df.style.format(
                {
                    "Forecast": "{:,.0f}",
                    "Lower Bound (95%)": "{:,.0f}",
                    "Upper Bound (95%)": "{:,.0f}",
                    "Cumulative": "{:,.0f}",
                }
            ),
            use_container_width=True,
            height=400,
        )

        st.subheader("📊 Forecast Statistics")
        s1, s2, s3 = st.columns(3)
        s1.metric("Average Forecast", f"{int(sum(forecasts) / len(forecasts)):,}")
        s2.metric("Range", f"{int(min(forecasts)):,} - {int(max(forecasts)):,}")
        avg_ci = int(
            sum([upper_bounds[i] - lower_bounds[i] for i in range(len(forecasts))])
            / len(forecasts)
        )
        s3.metric("Avg Uncertainty", f"±{avg_ci:,}")

        st.subheader("💾 Export Data")
        d1, d2 = st.columns(2)
        csv = forecast_df.to_csv(index=False)
        d1.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"product_x_7count_forecast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
        json_export = {
            "generated_at": datetime.now().isoformat(),
            "package_size": 7,
            "forecast_months": forecast_months,
            "forecasts": [
                {
                    "month": i + 1,
                    "forecast": int(forecasts[i]),
                    "lower_bound": int(lower_bounds[i]),
                    "upper_bound": int(upper_bounds[i]),
                }
                for i in range(len(forecasts))
            ],
        }
        d2.download_button(
            label="📥 Download JSON",
            data=json.dumps(json_export, indent=2),
            file_name=f"product_x_7count_forecast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
        )

        with st.expander("🔍 View Raw API Response"):
            st.json(result)
    else:
        st.info("👆 Configure horizon in the sidebar and click 'Generate Forecast'.")
        info1, info2 = st.columns(2)
        with info1:
            st.markdown(
                """
                **Model Information:**
                - Product: Product X 7-count
                - Model: ARIMA
                - Endpoint: `jardiance_arima_pkg_7`
                - Confidence: 95% intervals
                """
            )
        with info2:
            st.markdown(
                """
                **Capabilities:**
                - Forecast up to 24 months
                - Visualize confidence intervals
                - Export CSV/JSON
                - Real-time serving via Databricks
                """
            )

with tabs[1]:
    st.subheader("🎯 XGBoost Point Prediction")
    feature_cols, cat_cols, num_cols, cat_map, int_cols = parse_xgb_schema()
    if not feature_cols:
        st.warning("Configure `XGB_FEATURE_SPEC` or `XGB_CATEGORICAL_MAP` env vars.")
        st.stop()

    with st.form("xgb_point_prediction_form"):
        st.markdown("Provide feature values for a single inference call.")
        user_inputs = {}
        for col in cat_cols:
            options = list(cat_map.get(col, {}).keys())
            if not options:
                st.error(f"No categorical mapping available for '{col}'.")
                st.stop()
            user_inputs[col] = st.selectbox(col, options, index=0)
        for col in num_cols:
            if col in int_cols:
                user_inputs[col] = st.number_input(col, value=0, step=1, format="%d")
            else:
                user_inputs[col] = st.number_input(col, value=0.0)
        submitted = st.form_submit_button("Predict Units Sold", type="primary")

    if submitted:
        encoded_payload = {}
        for col in feature_cols:
            val = user_inputs[col]
            if col in cat_cols:
                mapping = cat_map[col]
                if val not in mapping:
                    st.error(f"Value '{val}' is not valid for '{col}'.")
                    st.stop()
                encoded_payload[col] = int(mapping[val])
            elif col in int_cols:
                encoded_payload[col] = int(val)
            else:
                encoded_payload[col] = float(val)

        status = st.empty()
        status.info("📡 Calling XGBoost endpoint...")
        try:
            start = time.time()
            resp = invoke_endpoint(XGB_ENDPOINT_URL, [encoded_payload])
            elapsed = time.time() - start
            if resp.status_code != 200:
                status.error("❌ Prediction failed")
                with st.expander("Response details"):
                    st.code(resp.text[:500])
            else:
                status.success(f"✅ Prediction ready in {elapsed:.1f}s")
                body = resp.json()
                prediction = body.get("predictions", [None])[0]
                st.metric("Predicted Units Sold", f"{prediction:,.0f}")
                with st.expander("Inspect payloads"):
                    st.json({"request": encoded_payload, "response": body})
        except Exception as exc:
            status.error(f"❌ Request error: {exc}")


with tabs[2]:
    st.subheader("📊 ARIMA Forecast via MLflow")
    st.info("This tab loads the ARIMA model directly from MLflow for forecasting.")

    if st.button(
        "Load ARIMA Model from MLflow", type="primary", key="load_arima_mlflow"
    ):
        try:
            with st.spinner(f"Loading `{ARIMA_MODEL_NAME}` from Unity Catalog..."):
                arima_model, arima_version = load_uc_model(ARIMA_MODEL_NAME)
                st.session_state["arima_model"] = arima_model
                st.session_state["arima_version"] = arima_version
            st.success(
                f"✅ Loaded `{ARIMA_MODEL_NAME}` version {arima_version} from Unity Catalog."
            )
        except Exception as exc:
            st.error(f"❌ Failed to load ARIMA model: {exc}")
            import traceback

            with st.expander("Error details"):
                st.code(traceback.format_exc())

    if "arima_model" in st.session_state:
        st.success(
            f"ARIMA Model ready: version {st.session_state.get('arima_version', 'unknown')}"
        )

        forecast_months_mlflow = st.slider(
            "Forecast Horizon (months)", 1, 24, 12, key="arima_mlflow_months"
        )

        if st.button(
            "Generate Forecast via MLflow", type="primary", key="arima_mlflow_predict"
        ):
            try:
                input_df = pd.DataFrame([{"n_periods": forecast_months_mlflow}])
                result = st.session_state["arima_model"].predict(input_df)

                # Parse result based on format
                if isinstance(result, pd.DataFrame):
                    predictions_data = result.to_dict("records")
                elif isinstance(result, dict) and "predictions" in result:
                    predictions_data = result["predictions"]
                elif isinstance(result, list):
                    predictions_data = result
                else:
                    predictions_data = (
                        [
                            {
                                "forecast": val,
                                "lower_bound": val * 0.9,
                                "upper_bound": val * 1.1,
                            }
                            for val in result
                        ]
                        if hasattr(result, "__iter__")
                        else []
                    )

                forecasts = []
                lower_bounds = []
                upper_bounds = []
                for item in predictions_data:
                    if isinstance(item, dict):
                        forecasts.append(item.get("forecast", 0))
                        lower_bounds.append(item.get("lower_bound", 0))
                        upper_bounds.append(item.get("upper_bound", 0))
                    else:
                        forecasts.append(float(item))
                        lower_bounds.append(float(item) * 0.9)
                        upper_bounds.append(float(item) * 1.1)

                st.success("✅ Forecast generated via MLflow!")

                st.subheader("📈 Key Metrics")
                k1, k2, k3, k4 = st.columns(4)
                if forecasts:
                    k1.metric("Next Month", f"{int(forecasts[0]):,}")
                if len(forecasts) >= 3:
                    k2.metric("3-Month Avg", f"{int(sum(forecasts[:3]) / 3):,}")
                if len(forecasts) >= 6:
                    k3.metric("6-Month Avg", f"{int(sum(forecasts[:6]) / 6):,}")
                k4.metric(
                    f"{forecast_months_mlflow}-Month Total",
                    f"{int(sum(forecasts[:forecast_months_mlflow])):,}",
                )

                st.subheader("📊 Forecast Visualization")
                months = list(range(1, len(forecasts) + 1))
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=months + months[::-1],
                        y=upper_bounds + lower_bounds[::-1],
                        fill="toself",
                        fillcolor="rgba(46, 204, 113, 0.2)",
                        line=dict(color="rgba(255,255,255,0)"),
                        name="95% Confidence Interval",
                        hoverinfo="skip",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=months,
                        y=forecasts,
                        mode="lines+markers",
                        name="Forecast",
                        line=dict(color="#2ecc71", width=3),
                        marker=dict(size=8),
                        hovertemplate="<b>Month %{x}</b><br>Forecast: %{y:,.0f} units<extra></extra>",
                    )
                )
                fig.update_layout(
                    title="Product X 7-Count Forecast (MLflow Model)",
                    xaxis_title="Month",
                    yaxis_title="Forecasted Units",
                    height=500,
                    hovermode="x unified",
                )
                st.plotly_chart(fig, use_container_width=True)

                st.subheader("📋 Forecast Data")
                forecast_df = pd.DataFrame(
                    {
                        "Month": months,
                        "Forecast": [int(x) for x in forecasts],
                        "Lower Bound": [int(x) for x in lower_bounds],
                        "Upper Bound": [int(x) for x in upper_bounds],
                    }
                )
                st.dataframe(forecast_df, use_container_width=True)

            except Exception as exc:
                st.error(f"❌ Prediction failed: {exc}")
                import traceback

                with st.expander("Error details"):
                    st.code(traceback.format_exc())
    else:
        st.warning("👆 Click 'Load ARIMA Model from MLflow' to begin.")


with tabs[3]:
    st.subheader("🎯 XGBoost Prediction via MLflow")
    st.info("This tab loads the XGBoost model directly from MLflow for prediction.")

    if st.button(
        "Load XGBoost Model from MLflow", type="primary", key="load_xgb_mlflow"
    ):
        try:
            with st.spinner(f"Loading `{XGB_MODEL_NAME}` from Unity Catalog..."):
                xgb_model, xgb_version = load_uc_model(XGB_MODEL_NAME)
                st.session_state["xgb_mlflow_model"] = xgb_model
                st.session_state["xgb_mlflow_version"] = xgb_version
            st.success(
                f"✅ Loaded `{XGB_MODEL_NAME}` version {xgb_version} from Unity Catalog."
            )
        except Exception as exc:
            st.error(f"❌ Failed to load XGBoost model: {exc}")
            import traceback

            with st.expander("Error details"):
                st.code(traceback.format_exc())

    if "xgb_mlflow_model" in st.session_state:
        st.success(
            f"XGBoost Model ready: version {st.session_state.get('xgb_mlflow_version', 'unknown')}"
        )

        feature_cols, cat_cols, num_cols, cat_map, int_cols = parse_xgb_schema()

        with st.form("xgb_mlflow_form"):
            st.markdown("Provide feature values for prediction using MLflow model.")
            mlflow_inputs = {}
            for col in cat_cols:
                options = list(cat_map.get(col, {}).keys())
                if not options:
                    st.error(f"No categorical mapping available for '{col}'.")
                    st.stop()
                mlflow_inputs[col] = st.selectbox(
                    f"{col}", options, index=0, key=f"mlflow_{col}"
                )
            for col in num_cols:
                if col in int_cols:
                    mlflow_inputs[col] = st.number_input(
                        f"{col}", value=0, step=1, format="%d", key=f"mlflow_{col}"
                    )
                else:
                    mlflow_inputs[col] = st.number_input(
                        f"{col}", value=0.0, key=f"mlflow_{col}"
                    )
            submit_mlflow = st.form_submit_button("Predict via MLflow", type="primary")

        if submit_mlflow:
            encoded_payload = {}
            for col in feature_cols:
                val = mlflow_inputs[col]
                if col in cat_cols:
                    mapping = cat_map[col]
                    if val not in mapping:
                        st.error(f"Value '{val}' is not valid for '{col}'.")
                        st.stop()
                    encoded_payload[col] = int(mapping[val])
                elif col in int_cols:
                    encoded_payload[col] = int(val)
                else:
                    encoded_payload[col] = float(val)

            input_df = pd.DataFrame([encoded_payload])
            try:
                prediction = st.session_state["xgb_mlflow_model"].predict(input_df)[0]
                st.success("✅ Prediction completed!")
                st.metric("Predicted Units Sold", f"{prediction:,.0f}")

                with st.expander("📋 Input Details"):
                    st.json(
                        {
                            "categorical_inputs": {
                                k: mlflow_inputs[k] for k in cat_cols
                            },
                            "numeric_inputs": {k: mlflow_inputs[k] for k in num_cols},
                            "encoded_payload": encoded_payload,
                        }
                    )
            except Exception as exc:
                st.error(f"❌ Prediction failed: {exc}")
                import traceback

                with st.expander("Error details"):
                    st.code(traceback.format_exc())
    else:
        st.warning("👆 Click 'Load XGBoost Model from MLflow' to begin.")


st.markdown("---")
st.caption("Powered by Databricks Model Serving | Built with Streamlit")
