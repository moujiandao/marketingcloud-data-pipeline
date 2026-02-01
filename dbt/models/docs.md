{% docs __overview__ %}

# Salesforce Data Pipeline

This dbt project transforms raw Salesforce data into analytics-ready dimensional models following the star schema pattern.

## Project Structure

### Layers

**Staging Layer** (`models/staging/`)
- 1:1 with source tables
- Light transformations (renaming, type casting)
- Standardized naming: `stg_salesforce__<object>`
- Materialized as views

**Intermediate Layer** (`models/intermediate/`)
- Joins and business logic
- Calculated metrics and aggregations
- Preparation for marts
- Materialized as views

**Marts Layer** (`models/marts/`)
- Star schema dimensions and facts
- Optimized for analytical queries
- Materialized as tables for performance

### Marts

#### Core
- `dim_accounts`: Customer companies
- `dim_contacts`: People at customer companies
- `dim_products`: Product catalog
- `dim_date`: Date dimension with fiscal calendar
- `fct_opportunities`: Sales opportunities fact table

#### Marketing
- `dim_campaigns`: Marketing campaigns
- `fct_campaign_members`: Campaign membership fact table

## Data Architecture

### Medallion Pattern
- **Bronze (Raw)**: Raw Salesforce data loaded from JSON
- **Silver (Staging/Intermediate)**: Cleaned and joined data
- **Gold (Marts)**: Business-ready dimensional models

### Star Schema
Fact tables contain numeric measures and foreign keys to dimensions.
Dimensions provide descriptive attributes for slicing and filtering.

## Key Metrics

### Sales Metrics
- Pipeline value: `sum(amount)`
- Expected revenue: `sum(expected_revenue)`
- Win rate: `count(is_won) / count(*)`
- Average deal size: `avg(amount)`
- Sales cycle days: `avg(sales_cycle_days)`

### Marketing Metrics
- Response rate: `count(responded) / count(members)`
- Cost per response: `actual_cost / responded_members`
- Campaign ROI: `(expected_revenue - actual_cost) / actual_cost`

### Engagement Metrics
- Task completion rate: `completed_tasks / total_tasks`
- Contact engagement score (High/Medium/Low)

## Data Freshness

- Raw data loaded via `src/load/load_to_postgres.py`
- dbt models rebuild on demand or scheduled via Airflow
- Staging/Intermediate: Always current (views)
- Marts: Refreshed during dbt run (tables)

## Testing Strategy

### Schema Tests
- Primary key uniqueness and not-null
- Foreign key relationships
- Accepted value ranges

### Custom Tests
- Business rule validation
- Data quality checks
- Referential integrity across layers

## Documentation

Generate and view documentation:
```bash
cd dbt
dbt docs generate --profiles-dir .
dbt docs serve --profiles-dir .
```

{% enddocs %}
