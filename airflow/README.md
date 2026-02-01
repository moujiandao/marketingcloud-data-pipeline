# Airflow Orchestration

This directory contains Apache Airflow DAGs for orchestrating the Salesforce data pipeline.

## Overview

The `salesforce_pipeline` DAG orchestrates the entire data pipeline:

1. **Extract**: Generate mock Salesforce data
2. **Load**: Load raw data to PostgreSQL
3. **Transform (dbt)**:
   - Staging models
   - Intermediate models
   - Mart models
4. **Test**: Run dbt data quality tests
5. **Document**: Generate dbt documentation

## Quick Start

### Option 1: Local Airflow with Docker (Recommended)

```bash
# Navigate to airflow directory
cd airflow

# Create required directories
mkdir -p ./dags ./logs ./plugins

# Set Airflow UID (Linux/Mac)
echo -e "AIRFLOW_UID=$(id -u)" > .env

# Start Airflow
docker-compose up -d

# Access Airflow UI
# URL: http://localhost:8080
# Username: airflow
# Password: airflow
```

### Option 2: Local Airflow Installation

```bash
# Install Airflow
pip install apache-airflow==2.8.0

# Set Airflow home
export AIRFLOW_HOME=~/airflow

# Initialize database
airflow db init

# Create admin user
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com

# Start webserver
airflow webserver --port 8080

# Start scheduler (in another terminal)
airflow scheduler
```

## DAG Configuration

### salesforce_pipeline DAG

**Schedule**: Daily at 2 AM UTC (`0 2 * * *`)

**Tasks**:
1. `generate_mock_salesforce_data` - Python script to generate mock data
2. `load_data_to_postgres` - Load JSON data to PostgreSQL
3. `dbt_run_staging` - Build staging models
4. `dbt_run_intermediate` - Build intermediate models
5. `dbt_run_marts` - Build mart models
6. `dbt_run_marts` - Build mart models (star schema)
7. `dbt_test_all` - Run all dbt tests
8. `dbt_docs_generate` - Generate dbt documentation

**Dependencies**:
```
generate_data → load_to_postgres → dbt_staging → dbt_intermediate → dbt_marts → dbt_test → dbt_docs
```

## Managing DAGs

### Trigger DAG Manually

```bash
# From command line
airflow dags trigger salesforce_pipeline

# Or use the Airflow UI
# 1. Navigate to http://localhost:8080
# 2. Click on "salesforce_pipeline" DAG
# 3. Click the "Play" button to trigger
```

### View DAG Runs

```bash
# List DAG runs
airflow dags list-runs -d salesforce_pipeline

# View task logs
airflow tasks logs salesforce_pipeline dbt_run_marts <execution_date>
```

### Pause/Unpause DAG

```bash
# Pause DAG
airflow dags pause salesforce_pipeline

# Unpause DAG
airflow dags unpause salesforce_pipeline
```

## Project Structure

```
airflow/
├── dags/
│   └── salesforce_pipeline_dag.py    # Main pipeline DAG
├── logs/                              # Airflow task logs
├── plugins/                           # Custom Airflow plugins
├── docker-compose.yml                 # Docker setup for Airflow
└── README.md                          # This file
```

## Configuration

### Environment Variables

Set these in `.env` file or docker-compose.yml:

```bash
# PostgreSQL connection for data pipeline
POSTGRES_USER=brianmar
POSTGRES_PASSWORD=
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=salesforce_dw

# Airflow configuration
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__CORE__LOAD_EXAMPLES=false
```

### Airflow Connections

No additional connections needed - the DAG uses environment variables for database access.

## Monitoring

### Airflow UI

Access the web interface at http://localhost:8080

**Key Views**:
- **DAGs**: List of all DAGs and their status
- **Grid**: Visual representation of DAG runs
- **Graph**: Task dependencies visualization
- **Calendar**: Historical run success/failure
- **Task Duration**: Performance metrics

### Task Logs

Logs are stored in `./logs/` directory:
```bash
# View recent logs
tail -f logs/dag_id=salesforce_pipeline/run_id=*/task_id=dbt_run_marts/*.log
```

## Troubleshooting

### DAG Not Appearing

```bash
# Check for syntax errors
python dags/salesforce_pipeline_dag.py

# Refresh DAG list
airflow dags list

# Check scheduler logs
docker-compose logs airflow-scheduler
```

### Task Failures

1. Check task logs in Airflow UI
2. Verify database connection
3. Ensure all dependencies are installed
4. Check file paths in DAG

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -h localhost -U brianmar -d salesforce_dw

# Check environment variables
echo $POSTGRES_USER
```

## Production Deployment

For production deployment, consider:

1. **Use a production-grade executor**: CeleryExecutor or KubernetesExecutor
2. **External metadata database**: Use managed PostgreSQL/MySQL
3. **Monitoring & Alerting**: Integrate with Datadog, PagerDuty, or Slack
4. **Secret management**: Use Airflow Connections or AWS Secrets Manager
5. **Resource limits**: Set appropriate CPU/memory limits
6. **Backup & Recovery**: Regular backups of Airflow metadata database

### Deployment Options

- **AWS**: Amazon MWAA (Managed Workflows for Apache Airflow)
- **GCP**: Cloud Composer
- **Azure**: Data Factory with Airflow
- **Self-hosted**: EC2, GKE, or on-premises

## Best Practices

1. **Idempotency**: Ensure tasks can be re-run safely
2. **Monitoring**: Set up alerts for task failures
3. **Testing**: Test DAGs locally before deploying
4. **Documentation**: Keep DAG docstrings up to date
5. **Version Control**: Track DAG changes in git
6. **Incremental Loading**: Use incremental dbt models for large tables
7. **Retries**: Configure appropriate retry logic for transient failures

## Next Steps

1. Set up email notifications for DAG failures
2. Add data quality checks with Great Expectations
3. Implement incremental loads for large fact tables
4. Create separate DAGs for different business domains
5. Add SLA monitoring and alerts
6. Integrate with BI tools for automated report refreshes
