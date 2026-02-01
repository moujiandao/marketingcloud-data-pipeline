"""
Salesforce Data Pipeline DAG

Orchestrates the complete data pipeline:
1. Generate mock Salesforce data
2. Load raw data to PostgreSQL
3. Run dbt transformations (staging → intermediate → marts)
4. Run dbt tests

Schedule: Daily at 2 AM UTC
"""

from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

# Project paths
PROJECT_ROOT = Path("/Users/brianmar/Documents/claudecode-data-pipeline")
SRC_DIR = PROJECT_ROOT / "src"
DBT_DIR = PROJECT_ROOT / "dbt"

# Default arguments
default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

# DAG definition
with DAG(
    dag_id="salesforce_pipeline",
    default_args=default_args,
    description="End-to-end Salesforce data pipeline with dbt transformations",
    schedule_interval="0 2 * * *",  # Daily at 2 AM UTC
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["salesforce", "dbt", "analytics"],
) as dag:

    # Task 1: Generate mock Salesforce data
    generate_data = BashOperator(
        task_id="generate_mock_salesforce_data",
        bash_command=f"cd {SRC_DIR} && python3 extract/generate_mock_data.py",
        env={
            "PYTHONPATH": str(SRC_DIR),
        },
    )

    # Task 2: Load data to PostgreSQL
    load_to_postgres = BashOperator(
        task_id="load_data_to_postgres",
        bash_command=f"cd {SRC_DIR} && python3 load/load_to_postgres.py",
        env={
            "PYTHONPATH": str(SRC_DIR),
        },
    )

    # Task 3: Run dbt staging models
    dbt_run_staging = BashOperator(
        task_id="dbt_run_staging",
        bash_command=f"cd {DBT_DIR} && dbt run --profiles-dir . --select staging",
    )

    # Task 4: Run dbt intermediate models
    dbt_run_intermediate = BashOperator(
        task_id="dbt_run_intermediate",
        bash_command=f"cd {DBT_DIR} && dbt run --profiles-dir . --select intermediate",
    )

    # Task 5: Run dbt mart models
    dbt_run_marts = BashOperator(
        task_id="dbt_run_marts",
        bash_command=f"cd {DBT_DIR} && dbt run --profiles-dir . --select marts",
    )

    # Task 6: Run dbt tests
    dbt_test = BashOperator(
        task_id="dbt_test_all",
        bash_command=f"cd {DBT_DIR} && dbt test --profiles-dir .",
    )

    # Task 7: Generate dbt documentation
    dbt_docs_generate = BashOperator(
        task_id="dbt_docs_generate",
        bash_command=f"cd {DBT_DIR} && dbt docs generate --profiles-dir .",
    )

    # Define task dependencies
    # Linear flow: extract → load → staging → intermediate → marts → test → docs
    (
        generate_data
        >> load_to_postgres
        >> dbt_run_staging
        >> dbt_run_intermediate
        >> dbt_run_marts
        >> dbt_test
        >> dbt_docs_generate
    )
