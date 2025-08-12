# Database Migrations

This directory contains SQL migration scripts for the MCMV Dashboard v5.

## Migration Files

- `001_business_logic_foundation.sql` - Initial business logic setup
- `002_create_refresh_function.sql` - Creates the `refresh_all_materialized_views()` function
- `003_create_quality_history.sql` - Creates quality history tracking and monitoring tables

## Running Migrations

To apply the migrations, run them in order:

```bash
# Connect to the database
psql -h pac-mcmv-mvp-db-1 -U postgres -d pac_mcmv

# Run each migration
\i /path/to/dashboard_v5/database/001_business_logic_foundation.sql
\i /path/to/dashboard_v5/database/002_create_refresh_function.sql
```

## Function: refresh_all_materialized_views()

This function refreshes all materialized views in the `mcmv_v2` schema:

- Attempts CONCURRENT refresh first (non-blocking)
- Falls back to regular refresh if concurrent is not possible
- Returns a table showing the status of each refresh
- Continues with other views even if one fails

Usage:
```sql
SELECT * FROM mcmv_v2.refresh_all_materialized_views();
```