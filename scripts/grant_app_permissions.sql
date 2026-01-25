-- Grant Unity Catalog permissions to the app's service principal
-- This script should be run after the app is deployed
-- Replace <SERVICE_PRINCIPAL_ID> with the actual service principal ID from the app

-- Grant catalog access
GRANT USE CATALOG ON CATALOG workspace TO `<SERVICE_PRINCIPAL_ID>`;

-- Grant schema access
GRANT USE SCHEMA ON SCHEMA workspace.default TO `<SERVICE_PRINCIPAL_ID>`;

-- Grant SELECT on schema (allows reading tables in the schema)
GRANT SELECT ON SCHEMA workspace.default TO `<SERVICE_PRINCIPAL_ID>`;

-- Grant READ VOLUME if needed for volumes
GRANT READ VOLUME ON SCHEMA workspace.default TO `<SERVICE_PRINCIPAL_ID>`;

-- Optional: Grant access to specific MLflow models if needed
-- GRANT EXECUTE ON FUNCTION workspace.default.<model_name> TO `<SERVICE_PRINCIPAL_ID>`;
