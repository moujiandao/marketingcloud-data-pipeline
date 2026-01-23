# Salesforce Data Pipeline

A production-grade data pipeline demonstrating modern data engineering practices.

## Architecture

```
Salesforce (Mock) → Extract (Python) → PostgreSQL (Raw) → dbt (Transform) → Star Schema
                                                                              ↓
                                                         Analysts / Data Scientists / MLEs
```

## Project Structure

```
├── src/
│   ├── extract/          # Python extraction scripts
│   └── load/             # Raw data loaders
├── dbt/
│   ├── models/
│   │   ├── staging/      # 1:1 with source tables, light cleaning
│   │   ├── intermediate/ # Business logic, joins, complex transforms
│   │   └── marts/        # Final dimensional models (star schema)
│   │       ├── core/     # Core business entities (accounts, opps)
│   │       ├── marketing/# Marketing-specific models
│   │       └── finance/  # Finance-specific models
│   ├── macros/           # Reusable SQL functions
│   ├── seeds/            # Static reference data (CSV)
│   ├── tests/            # Custom data tests
│   └── snapshots/        # SCD Type 2 tracking
├── airflow/
│   └── dags/             # Orchestration DAGs
├── scripts/              # Utility scripts
├── docs/                 # Documentation
└── data/
    ├── raw/              # Extracted raw data
    └── processed/        # Intermediate files
```

## Key Concepts

### Data Layers (Medallion Architecture)

| Layer | dbt Location | Purpose |
|-------|--------------|---------|
| Bronze/Raw | `staging/` | Source-conformed, minimal transformation |
| Silver | `intermediate/` | Business logic, cleaned, joined |
| Gold | `marts/` | Consumption-ready dimensional models |

### Star Schema

- **Fact Tables**: Measurable events (opportunities, activities)
- **Dimension Tables**: Context for facts (accounts, users, dates)

## Setup

See individual README files in each directory for setup instructions.
