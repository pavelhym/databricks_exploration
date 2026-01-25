"""
Simple Streamlit App - Load Data from Unity Catalog Delta Table
"""

import os

import pandas as pd
import streamlit as st
from databricks.sdk.core import Config

from databricks import sql

st.set_page_config(page_title="Data Loader", layout="wide")

st.title("📊 Unity Catalog Data Loader")
st.markdown("*Simple app to load data from Delta tables*")


@st.cache_resource(ttl=3600)  # Cache connection for 1 hour
def get_connection(http_path: str):
    """
    Get cached SQL Warehouse connection using Databricks SDK pattern.
    """
    from databricks.sdk.core import Config

    try:
        st.info("🔧 Step 1: Initializing Databricks SDK Config...")
        cfg = Config()
        st.success(f"✅ Config initialized - Host: {cfg.host}")
    except Exception as e:
        st.error(f"❌ Failed to initialize Config: {type(e).__name__}: {e}")
        raise

    try:
        st.info("🔌 Step 2: Connecting to SQL Warehouse...")
        conn = sql.connect(
            server_hostname=cfg.host,
            http_path=http_path,
            credentials_provider=lambda: cfg.authenticate,
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
def read_table(table_name: str, http_path: str) -> pd.DataFrame:
    """Read Delta table from Unity Catalog using Arrow format."""
    try:
        st.info(f"📊 Reading {table_name} from Unity Catalog...")

        # Step 1: Get connection
        try:
            conn = get_connection(http_path)
        except Exception as conn_error:
            st.error(f"❌ Connection failed at get_connection(): {conn_error}")
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
            st.info(f"🔍 Step 4: Executing query...")
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
            st.success(f"✅ Fetched Arrow table!")
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


# Main UI
st.sidebar.header("⚙️ Configuration")

http_path = st.sidebar.text_input(
    "SQL Warehouse HTTP Path",
    value=os.getenv("DATABRICKS_SQL_HTTP_PATH", "/sql/1.0/warehouses/e2e25fceda9c1031"),
    help="Format: /sql/1.0/warehouses/xxxxx",
)

table_name = st.sidebar.text_input(
    "Table Name",
    value="workspace.default.gross_sales_monthly",
    help="Enter Unity Catalog table name (catalog.schema.table)",
)

if st.sidebar.button("🚀 Load Data", type="primary"):
    if not http_path:
        st.error("❌ Please provide SQL Warehouse HTTP Path")
    elif not table_name:
        st.error("❌ Please provide table name")
    else:
        data = read_table(table_name, http_path)

        if not data.empty:
            st.subheader("📋 Data Preview")

            # Display metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Rows", f"{len(data):,}")
            col2.metric("Total Columns", len(data.columns))
            col3.metric(
                "Memory Usage", f"{data.memory_usage(deep=True).sum() / 1024**2:.2f} MB"
            )

            # Display first 50 rows
            st.dataframe(data.head(50), use_container_width=True, height=400)

            # Column info
            st.subheader("📊 Column Information")
            col_info = pd.DataFrame(
                {
                    "Column": data.columns,
                    "Type": data.dtypes.astype(str),
                    "Non-Null Count": data.count().values,
                    "Null Count": data.isnull().sum().values,
                }
            )
            st.dataframe(col_info, use_container_width=True)

            # Download option
            st.subheader("💾 Export Data")
            csv = data.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"{table_name.split('.')[-1]}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.warning("No data loaded.")
else:
    st.info("👈 Configure table name and click 'Load Data' to begin.")

    with st.expander("📖 Environment Variables"):
        st.code(
            f"""
DATABRICKS_HOST: {os.getenv("DATABRICKS_HOST", "Not set")}
DATABRICKS_SQL_HTTP_PATH: {os.getenv("DATABRICKS_SQL_HTTP_PATH", "Not set")}
DATABRICKS_TOKEN: {"Set" if os.getenv("DATABRICKS_TOKEN") else "Not set (using OAuth)"}
        """
        )

st.markdown("---")
st.caption("Powered by Databricks Unity Catalog")
