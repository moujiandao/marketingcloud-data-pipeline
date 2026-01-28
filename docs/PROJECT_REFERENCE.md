# Project Reference - Salesforce Data Pipeline

**Last Updated**: 2026-01-22 23:35
**Current Status**: Phase 6 Complete (dbt Staging Models)

This document serves as our shared context for the Salesforce data pipeline project. It captures all setup decisions, technical explanations, and project conventions established during development.

---

## 🎯 CURRENT STATUS (Session Context)

**Completed Phases:**
- ✅ Phase 1: Dimensional modeling & star schema
- ✅ Phase 2: Project structure and dependencies
- ✅ Phase 3: Mock data generation (20,576 records)
- ✅ Phase 4: Database loading scripts
- ✅ Phase 5: PostgreSQL setup and data loading
- ✅ Phase 6: dbt staging models (8 views created)

**Next Phase:** Phase 7 - Intermediate Models

**PostgreSQL Details:**
- Database: `salesforce_dw`
- User: `brianmar`
- Location: `/opt/homebrew/var/postgresql@14/`
- Schemas: `raw`, `public_staging`, `intermediate`, `marts`

**dbt Configuration:**
- Profile: `salesforce_pipeline`
- Profiles dir: `./dbt/profiles.yml`
- Run command: `cd dbt && dbt run --profiles-dir .`
- Current models: 8 staging views in `public_staging.*`

**Key Files:**
- Data generator: `src/extract/generate_mock_data.py`
- PostgreSQL loader: `src/load/load_to_postgres.py`
- Staging models: `dbt/models/staging/salesforce/stg_salesforce__*.sql`
- Sources config: `dbt/models/staging/salesforce/_sources.yml`

**GitHub Repo:**
- URL: https://github.com/moujiandao/marketingcloud-data-pipeline
- Last commit: Initial commit with staging models

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture Decisions](#architecture-decisions)
3. [Setup Completed](#setup-completed)
4. [Key Technical Concepts](#key-technical-concepts)
5. [Project Structure](#project-structure)
6. [Data Model Design](#data-model-design)
7. [Commands Reference](#commands-reference)
8. [Next Steps](#next-steps)

---

## Project Overview

**Goal**: Build a production-grade data pipeline that extracts fictitious data from Salesforce, transforms it using industry-standard data engineering practices, and creates a star schema that MLEs, data analysts, and data scientists can query.

**Tech Stack**:
- **Source**: Mock Salesforce CRM data (JSON format)
- **Extraction**: Python scripts with Faker library
- **Storage**: PostgreSQL (local instance)
- **Transformation**: dbt (data build tool)
- **Orchestration**: Apache Airflow
- **Target**: Dimensional model (star schema)

**Learning Approach**: Production-grade guidance, teaching concepts as they arise, emphasizing best practices and scalable patterns.

---

## Architecture Decisions

### Decision 1: Local Development (No Docker)
**Chosen**: Run PostgreSQL, Python, and Airflow locally
**Alternative Considered**: Docker Compose with containerized services
**Rationale**:
- Easier debugging for learning
- Simpler setup
- More direct access to logs and processes
- Can always containerize later

**Trade-off**: Less reproducible than Docker, but better for understanding how components work.

---

### Decision 2: PostgreSQL as Data Warehouse
**Chosen**: PostgreSQL
**Alternative Considered**: DuckDB
**Rationale**:
- Industry standard syntax (closest to Snowflake/Redshift)
- Production-like experience
- Better for learning enterprise patterns
- Most dbt tutorials use Postgres

---

### Decision 3: Medallion Architecture with dbt Layers
**Chosen**: Three-layer approach in dbt
```
staging/        → Bronze/Raw (1:1 with source, minimal transformation)
intermediate/   → Silver (business logic, joins, cleaning)
marts/          → Gold (dimensional models for consumption)
```

**Rationale**: Industry standard, separates concerns, makes debugging easier, aligns with dbt best practices.

---

## Setup Completed

### 1. Project Structure Created
```bash
mkdir -p src/{extract,load} \
  dbt/models/{staging,intermediate,marts/{core,marketing,finance}} \
  dbt/{macros,seeds,tests,snapshots} \
  airflow/dags \
  scripts \
  docs \
  data/{raw,processed}
```

**Purpose of each directory**:
- `src/extract/` - Python scripts to extract data from Salesforce (currently mock data generator)
- `src/load/` - Scripts to load raw data into PostgreSQL
- `dbt/models/staging/` - Source-conformed models (1:1 with raw tables)
- `dbt/models/intermediate/` - Business logic, complex joins, data cleaning
- `dbt/models/marts/` - Final dimensional models organized by consumer domain
- `dbt/macros/` - Reusable SQL functions
- `dbt/seeds/` - Static reference data (CSV files)
- `dbt/snapshots/` - Slowly Changing Dimension (SCD) Type 2 tracking
- `airflow/dags/` - Orchestration workflows
- `data/raw/` - Extracted JSON data from Salesforce
- `data/processed/` - Intermediate files

---

### 2. Configuration Files Created

#### `dbt_project.yml`
- Sets materialization strategies:
  - **Staging**: Views (cheap, always fresh)
  - **Intermediate**: Views (stepping stones)
  - **Marts**: Tables (performance for end users)
- Defines schema separation (staging, intermediate, marts)
- Sets project-wide variables (fiscal year start, date ranges)

#### `profiles.yml`
- Database connection configuration
- Uses environment variables for credentials (never hardcode passwords)
- Targets: `dev` (local), `prod` (future)

#### `.env.example`
- Template for environment variables
- Never commit `.env` to version control (contains secrets)

#### `.gitignore`
- Excludes sensitive files (.env, credentials)
- Excludes generated files (dbt/target/, __pycache__)
- Excludes large data files (data/raw/*.csv)

---

### 3. Documentation Created

#### `docs/dimensional_model.md`
Complete dimensional model design including:
- Business context and questions we're answering
- Grain definitions for each fact table
- Full schema for all dimension and fact tables
- SCD Type 2 strategy for historical tracking
- Naming conventions for consistency

#### `README.md`
Project overview, architecture diagram, structure explanation

---

### 4. Mock Data Generator Created

**File**: `src/extract/generate_mock_data.py`

**Key Features**:
- Generates realistic Salesforce CRM data with proper referential integrity
- Uses Faker library for realistic names, companies, addresses
- Implements realistic distributions:
  - **Log-normal deal sizes** (many small, few large)
  - **Quarter-end bias** (30% of deals close in last week of quarter - "hockey stick")
  - **Activity clustering** (more activities near opportunity close dates)
  - **Company size correlation** (larger companies = larger deals)

**Volumes**:
- 25 Users (sales reps with manager hierarchy)
- 200 Accounts (companies)
- 500 Contacts (people at companies)
- 10 Products (software, services, support, training)
- 800 Opportunities (deals in pipeline)
- 2,000 Activities (tasks, calls, emails, meetings)

**Output Format**: JSON files simulating Salesforce API responses
```json
{
  "totalSize": 200,
  "done": true,
  "records": [...]
}
```

---

## Key Technical Concepts

### Star Schema Fundamentals

**Definition**: A dimensional modeling approach that separates data into facts (measurements) and dimensions (context).

```
┌─────────────┐
│ dim_account │────┐
└─────────────┘    │
                   ▼
┌─────────────┐  ┌──────────────┐  ┌─────────────┐
│  dim_user   │──│ fct_oppty    │──│  dim_date   │
└─────────────┘  └──────────────┘  └─────────────┘
                   │
                   │ Foreign Keys
                   ▼
                [Measures: amount, stage, etc.]
```

**Fact Tables**:
- Store measurements (things you count, sum, average)
- Many rows, narrow columns
- Examples: `fct_opportunity`, `fct_activity`
- Contain foreign keys to dimensions

**Dimension Tables**:
- Store context (things you filter/group by)
- Fewer rows, wider columns
- Examples: `dim_account`, `dim_user`, `dim_date`, `dim_product`
- Contain descriptive attributes

**Why Star Schema?**
- Optimized for analytics (fast aggregations)
- Simple for analysts to understand and query
- Separates frequently-changing facts from stable dimensions
- Standard pattern across all modern data warehouses

---

### Grain Definition

**Critical Concept**: The grain is the most atomic level of detail in a fact table.

| Fact Table | Grain | One Row Represents |
|------------|-------|-------------------|
| `fct_opportunity` | One opportunity at current state | A single deal |
| `fct_opportunity_history` | One opportunity per day | Deal state on specific day |
| `fct_activity` | One activity | A single task/call/email |

**Why It Matters**:
- Every fact table must have ONE clearly defined grain
- All metrics must be consistent with that grain
- Mixing grains causes double-counting and incorrect aggregations
- Document the grain in model documentation

---

### Slowly Changing Dimensions (SCD)

**Type 1**: Overwrite - No history kept
- Use when: History doesn't matter (fixing typos)
- Example: Correcting misspelled account name

**Type 2**: Historical tracking with validity dates
- Use when: History matters for analysis
- Example: Account changes industry from "Startup" to "Enterprise"
- We need to know deals closed when they were a "Startup"
- Implementation: Add `is_current`, `valid_from`, `valid_to` columns

**Type 3**: Previous value column (rarely used)
- Columns: `current_industry`, `previous_industry`

**Our Approach**: Type 2 for `dim_account` and `dim_contact` since their attributes affect how we segment deals.

---

### Idempotency

**Definition**: Running the same pipeline multiple times with the same input produces the same output.

**Why Critical**:
- Enables safe re-runs when failures occur
- Allows backfilling historical data
- Essential for data quality and debugging

**How to Achieve**:
- Use deterministic transformations
- Use `MERGE` or `INSERT ... ON CONFLICT` instead of `INSERT`
- Include logic to handle duplicates
- Use dbt's incremental materialization strategy

---

### Medallion Architecture (Bronze/Silver/Gold)

| Layer | dbt Location | Purpose | Characteristics |
|-------|--------------|---------|-----------------|
| **Bronze** | `staging/` | Source-conformed | 1:1 with source, rename columns, cast types |
| **Silver** | `intermediate/` | Business logic | Joins, cleaning, deduplication, complex transformations |
| **Gold** | `marts/` | Consumption-ready | Dimensional models, aggregations, metrics |

**Data Flow**:
```
Raw JSON → Bronze (staging) → Silver (intermediate) → Gold (marts) → Analysts
```

---

### Naming Conventions

**Why Standardize**: Consistency makes code easier to read, review, and maintain across teams and projects.

| Element | Convention | Example |
|---------|------------|---------|
| Dimension tables | `dim_<entity>` | `dim_account`, `dim_user` |
| Fact tables | `fct_<event>` | `fct_opportunity`, `fct_activity` |
| Staging models | `stg_<source>__<entity>` | `stg_salesforce__accounts` |
| Intermediate models | `int_<descriptive_name>` | `int_account_enriched` |
| Surrogate keys | `<entity>_key` | `account_key` |
| Natural keys | `<entity>_id` | `account_id` (Salesforce ID) |
| Foreign keys | `<referenced_entity>_key` | `account_key` in fact table |
| Booleans | `is_<condition>` | `is_won`, `is_active`, `is_closed` |
| Dates | `<event>_date` | `created_date`, `close_date` |
| Timestamps | `<event>_at` | `updated_at`, `loaded_at` |
| Counts | `<thing>_count` | `employee_count`, `activity_count` |
| Amounts | Descriptive name or just "amount" | `amount`, `annual_revenue` |

---

## Project Structure

```
marketingcloud-data-pipeline/
├── .env.example              # Environment variable template
├── .gitignore               # Git exclusions
├── README.md                # Project overview
├── requirements.txt         # Python dependencies
│
├── src/                     # Source code for extraction/loading
│   ├── extract/
│   │   └── generate_mock_data.py  # Salesforce mock data generator
│   └── load/                # (Future) Raw data loaders
│
├── dbt/                     # dbt transformation project
│   ├── dbt_project.yml      # dbt configuration
│   ├── profiles.yml         # Database connections
│   ├── models/
│   │   ├── staging/         # Bronze layer (source-conformed)
│   │   ├── intermediate/    # Silver layer (business logic)
│   │   └── marts/           # Gold layer (dimensional models)
│   │       ├── core/        # Core business entities
│   │       ├── marketing/   # Marketing-specific models
│   │       └── finance/     # Finance-specific models
│   ├── macros/              # Reusable SQL functions
│   ├── seeds/               # Static reference data (CSV)
│   ├── tests/               # Custom data tests
│   └── snapshots/           # SCD Type 2 tracking
│
├── airflow/                 # Orchestration
│   └── dags/                # Airflow DAG definitions
│
├── scripts/                 # Utility scripts
├── docs/                    # Project documentation
│   ├── dimensional_model.md # Star schema design
│   └── PROJECT_REFERENCE.md # This file
│
└── data/                    # Local data storage
    ├── raw/                 # Extracted Salesforce JSON
    └── processed/           # Intermediate files
```

---

## Data Model Design

### Target Dimensional Models

**Dimensions** (Context for analysis):
- `dim_account` - Companies (industry, size, location) - SCD Type 2
- `dim_contact` - People at companies (title, department) - SCD Type 2
- `dim_user` - Sales reps (role, manager hierarchy)
- `dim_product` - Products sold (family, pricing)
- `dim_date` - Calendar/fiscal date dimension

**Facts** (Measurable events):
- `fct_opportunity` - Sales deals (amount, stage, win/loss)
- `fct_activity` - Sales activities (calls, emails, meetings)
- `fct_pipeline_snapshot` - Daily pipeline state for trending

### Example: fct_opportunity Schema

| Column | Type | Description | Source/Logic |
|--------|------|-------------|--------------|
| `opportunity_key` | INT (SK) | Surrogate key | Generated in dbt |
| `opportunity_id` | VARCHAR | Salesforce ID (natural key) | `Opportunity.Id` |
| `account_key` | INT (FK) | Link to dim_account | Lookup from `dim_account` |
| `owner_user_key` | INT (FK) | Link to dim_user | Lookup from `dim_user` |
| `created_date_key` | INT (FK) | Creation date | Lookup from `dim_date` |
| `close_date_key` | INT (FK) | Close date | Lookup from `dim_date` |
| `stage_name` | VARCHAR | Current pipeline stage | `Opportunity.StageName` |
| `opportunity_type` | VARCHAR | New/Renewal/Upsell | `Opportunity.Type` |
| `amount` | DECIMAL | Deal value | `Opportunity.Amount` |
| `expected_revenue` | DECIMAL | amount × probability | Calculated |
| `is_won` | BOOLEAN | Closed Won | `Opportunity.IsWon` |
| `is_closed` | BOOLEAN | Won or Lost | `Opportunity.IsClosed` |
| `days_to_close` | INT | Created to close duration | Calculated |

---

## Commands Reference

### Project Setup
```bash
# Create project structure
mkdir -p src/{extract,load} \
  dbt/models/{staging,intermediate,marts/{core,marketing,finance}} \
  dbt/{macros,seeds,tests,snapshots} \
  airflow/dags scripts docs data/{raw,processed}

# Create gitkeep files for empty directories
touch data/raw/.gitkeep data/processed/.gitkeep
```

### Python Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Generate mock data
python src/extract/generate_mock_data.py
```

### PostgreSQL Setup
```bash
# Install PostgreSQL (macOS)
brew install postgresql@15
brew services start postgresql@15

# Install PostgreSQL (Ubuntu/Debian)
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# Verify installation
psql --version

# Connect to PostgreSQL
psql postgres

# Create database (in psql prompt)
CREATE DATABASE salesforce_dw;
\q
```

### Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit environment variables (use your editor)
# Set POSTGRES_USER, POSTGRES_PASSWORD, etc.
```

### dbt Commands (Currently Using)
```bash
# Navigate to dbt directory
cd dbt

# Test database connection
dbt debug --profiles-dir .

# Run all models
dbt run --profiles-dir .

# Run only staging models
dbt run --profiles-dir . --select staging

# Run specific model
dbt run --profiles-dir . --select stg_salesforce__accounts

# Test data quality
dbt test --profiles-dir .

# Generate documentation
dbt docs generate --profiles-dir .
dbt docs serve --profiles-dir .

# Compile SQL without running
dbt compile --profiles-dir .

# Show model lineage
dbt docs generate --profiles-dir . && dbt docs serve --profiles-dir .
```

### Query Staging Models
```bash
# List staging views
psql salesforce_dw -c "\dv public_staging.*"

# Query a staging view
psql salesforce_dw -c "SELECT * FROM public_staging.stg_salesforce__accounts LIMIT 5;"

# Check counts
psql salesforce_dw -c "SELECT COUNT(*) FROM public_staging.stg_salesforce__opportunities;"
```

---

## Next Steps

### Phase 3: Mock Data Generation ✓
- [x] Created `generate_mock_data.py`
- [x] Implemented realistic distributions
- [ ] **NEXT**: Run script to generate data

### Phase 4: Extraction & Loading
- [ ] Create database loading scripts
- [ ] Build raw layer tables in PostgreSQL
- [ ] Implement idempotent loading logic

### Phase 5: dbt Staging Models
- [ ] Create `sources.yml` to define raw tables
- [ ] Build staging models (1:1 with sources)
- [ ] Add column renaming, type casting
- [ ] Write schema tests

### Phase 6: dbt Intermediate Models
- [ ] Build business logic layer
- [ ] Implement joins and deduplication
- [ ] Add calculated fields
- [ ] Data quality checks

### Phase 7: dbt Mart Models (Star Schema)
- [ ] Build dimension tables
- [ ] Implement SCD Type 2 for dim_account
- [ ] Build fact tables with surrogate keys
- [ ] Create dim_date generator

### Phase 8: Testing & Documentation
- [ ] Add dbt tests (unique, not_null, relationships)
- [ ] Add custom tests (business rules)
- [ ] Write model documentation
- [ ] Generate dbt docs site

### Phase 9: Airflow Orchestration
- [ ] Install and configure Airflow
- [ ] Create DAGs for extract → load → transform
- [ ] Implement error handling and retries
- [ ] Add monitoring and alerting

### Phase 10: Data Quality & Observability
- [ ] Integrate Great Expectations
- [ ] Add data freshness checks
- [ ] Implement anomaly detection
- [ ] Build monitoring dashboard

---

## Design Principles (Production-Grade)

### 1. Idempotency First
Every pipeline must be rerunnable. If you run it twice with the same input, you get the same output. No duplicates, no partial updates.

### 2. Incremental Processing
Don't reprocess data that hasn't changed. Use timestamps, watermarks, and checksums to identify new/changed records.

### 3. Schema Evolution
Upstream schemas change. Your pipeline must handle new columns gracefully without breaking.

### 4. Separation of Concerns
- **Extraction**: Get data, don't transform
- **Loading**: Store raw data as-is
- **Transformation**: All business logic in dbt (SQL)
- **Orchestration**: Airflow handles scheduling, not data transformation

### 5. Testability
- Unit tests for data transformations
- Contract tests for schema expectations
- Data quality tests for business rules
- Integration tests for end-to-end flows

### 6. Observability
Know when things break before users do:
- Data freshness SLAs
- Row count monitoring
- Null rate tracking
- Distribution anomaly detection

### 7. Documentation as Code
Documentation lives with code and is version-controlled. dbt docs are generated from schema files, not separate wikis.

---

## Key Learnings

### Why PostgreSQL Over DuckDB?
PostgreSQL is the foundation for Redshift, Greenplum, and other enterprise warehouses. Learning Postgres means learning the SQL dialect used in production data platforms.

### Why dbt?
- **Version control for data transformations** - Track changes like application code
- **Testing built-in** - Data quality tests are first-class citizens
- **Documentation generation** - Auto-generated docs with lineage graphs
- **Incremental materializations** - Built-in patterns for efficient updates
- **Macros & packages** - DRY principle for SQL

### Why Dimensional Modeling?
- **Performance** - Star schema is optimized for analytical queries
- **Understandability** - Business users can navigate the model
- **Flexibility** - Easy to add new dimensions or facts
- **Historical accuracy** - SCD tracks changes over time
- **Industry standard** - Kimball methodology used everywhere

---

## Troubleshooting

### Common Issues

**Issue**: `dbt debug` fails with connection error
**Solution**: Check PostgreSQL is running, verify credentials in profiles.yml

**Issue**: Data generator fails with missing Faker
**Solution**: Activate virtual environment and run `pip install -r requirements.txt`

**Issue**: PostgreSQL won't start
**Solution**: Check if another instance is running on port 5432 with `lsof -i :5432`

**Issue**: dbt models not found
**Solution**: Ensure `DBT_PROFILES_DIR` environment variable is set to `./dbt`

---

## Reference Links

- [dbt Documentation](https://docs.getdbt.com/)
- [Kimball Dimensional Modeling](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [Great Expectations](https://docs.greatexpectations.io/)

---

**Document Maintenance**: This file should be updated whenever we make significant decisions or complete major phases. Treat it as our single source of truth for the project.
