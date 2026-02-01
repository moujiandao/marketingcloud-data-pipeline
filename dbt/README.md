# dbt Project - Salesforce Pipeline

This directory contains the dbt (data build tool) project for transforming raw Salesforce data into analytics-ready dimensional models.

## Quick Start

```bash
# Navigate to dbt directory
cd dbt

# Test database connection
dbt debug --profiles-dir .

# Run all models
dbt run --profiles-dir .

# Run tests
dbt test --profiles-dir .

# Generate documentation
dbt docs generate --profiles-dir .
dbt docs serve --profiles-dir .
```

## Project Structure

```
dbt/
├── models/
│   ├── staging/          # 1:1 with raw tables
│   │   └── salesforce/
│   │       ├── _sources.yml
│   │       └── stg_salesforce__*.sql
│   ├── intermediate/     # Joined business logic
│   │   ├── schema.yml
│   │   ├── int_opportunities_enhanced.sql
│   │   ├── int_contacts_enriched.sql
│   │   └── int_campaign_performance.sql
│   └── marts/            # Star schema
│       ├── core/         # Core business entities
│       │   ├── schema.yml
│       │   ├── dim_*.sql
│       │   └── fct_*.sql
│       └── marketing/    # Marketing analytics
│           ├── schema.yml
│           ├── dim_campaigns.sql
│           └── fct_campaign_members.sql
├── tests/                # Custom data quality tests
│   └── test_*.sql
├── dbt_project.yml       # Project configuration
├── profiles.yml          # Database connection
└── README.md             # This file
```

## Layers

### Staging (`staging/`)
- **Purpose**: Clean and rename raw data
- **Grain**: 1:1 with source tables
- **Materialization**: Views (no storage cost, always fresh)
- **Naming**: `stg_salesforce__<object>`

### Intermediate (`intermediate/`)
- **Purpose**: Join tables, add business logic, aggregate metrics
- **Grain**: Varies by model
- **Materialization**: Views
- **Naming**: `int_<business_concept>`

### Marts (`marts/`)
- **Purpose**: Analytics-ready dimensional models
- **Grain**: Dimensions (one row per entity), Facts (one row per event/transaction)
- **Materialization**: Tables (optimized for query performance)
- **Schema**: Star schema with `dim_*` and `fct_*` tables

## Common Commands

### Development

```bash
# Run specific model
dbt run --profiles-dir . --select dim_accounts

# Run model and downstream dependencies
dbt run --profiles-dir . --select dim_accounts+

# Run model and upstream dependencies
dbt run --profiles-dir . --select +dim_accounts

# Run all staging models
dbt run --profiles-dir . --select staging

# Run all mart models
dbt run --profiles-dir . --select marts
```

### Testing

```bash
# Run all tests
dbt test --profiles-dir .

# Test specific model
dbt test --profiles-dir . --select dim_accounts

# Run only schema tests
dbt test --profiles-dir . --exclude test_type:generic

# Run only custom tests
dbt test --profiles-dir . --select test_type:singular
```

### Documentation

```bash
# Generate docs
dbt docs generate --profiles-dir .

# Serve docs locally (opens browser at localhost:8080)
dbt docs serve --profiles-dir .
```

## Schema Overview

### Dimensions
- `dim_accounts`: Customer companies (200 rows)
- `dim_contacts`: People at companies (500 rows)
- `dim_products`: Product catalog (20 rows)
- `dim_campaigns`: Marketing campaigns (50 rows)
- `dim_date`: Date dimension 2022-2026 (1,826 rows)

### Facts
- `fct_opportunities`: Sales deals (800 rows)
- `fct_campaign_members`: Campaign membership (varies)

## Data Quality

Tests are defined in:
- `models/**/schema.yml` - Schema tests (unique, not_null, relationships)
- `tests/` - Custom SQL tests

Run tests after every model change:
```bash
dbt run --profiles-dir .
dbt test --profiles-dir .
```

## Configuration

### Database Connection
Edit `profiles.yml` to configure PostgreSQL connection:
```yaml
salesforce_pipeline:
  target: dev
  outputs:
    dev:
      type: postgres
      host: localhost
      user: "{{ env_var('POSTGRES_USER', 'brianmar') }}"
      dbname: salesforce_dw
```

### Model Materialization
Configured in `dbt_project.yml`:
- Staging: `+materialized: view`
- Intermediate: `+materialized: view`
- Marts: `+materialized: table`

## Troubleshooting

### Connection Issues
```bash
# Test connection
dbt debug --profiles-dir .

# Check environment variables
echo $POSTGRES_USER
echo $POSTGRES_PASSWORD
```

### Model Errors
```bash
# Compile without running
dbt compile --profiles-dir .

# Check compiled SQL
cat target/compiled/salesforce_pipeline/models/marts/core/dim_accounts.sql
```

### Clean Build
```bash
# Remove compiled files
dbt clean

# Full rebuild
dbt run --profiles-dir . --full-refresh
```

## Next Steps

1. Build Airflow DAG to orchestrate dbt runs
2. Add incremental models for large fact tables
3. Implement snapshot models for slowly changing dimensions
4. Add more custom tests for business rules
5. Create BI tool connections (Tableau, Looker, etc.)
