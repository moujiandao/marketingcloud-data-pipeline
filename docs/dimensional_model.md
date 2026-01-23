# Dimensional Model Design

## Business Context

We're modeling a B2B SaaS company's sales data from Salesforce. The business questions we need to answer:

1. What's our pipeline by stage, rep, and region?
2. How does win rate vary by industry and deal size?
3. What activities correlate with closed-won deals?
4. How is pipeline trending week-over-week?

## Grain Definition

**Critical Concept**: The grain is the most atomic level of detail in a fact table. Get this wrong and everything breaks.

| Fact Table | Grain | One Row Represents |
|------------|-------|-------------------|
| fct_opportunity | One opportunity at current state | A single deal |
| fct_opportunity_history | One opportunity per day | Deal state on a given day |
| fct_activity | One activity | A single task/call/email |

## Dimension Tables

### dim_account

| Column | Type | Description | Source |
|--------|------|-------------|--------|
| account_key | INT (SK) | Surrogate key | Generated |
| account_id | VARCHAR | Salesforce ID | Account.Id |
| account_name | VARCHAR | Company name | Account.Name |
| industry | VARCHAR | Industry vertical | Account.Industry |
| employee_count | INT | Company size | Account.NumberOfEmployees |
| annual_revenue | DECIMAL | Company revenue | Account.AnnualRevenue |
| billing_country | VARCHAR | HQ country | Account.BillingCountry |
| billing_state | VARCHAR | HQ state | Account.BillingState |
| account_type | VARCHAR | Customer/Prospect | Account.Type |
| created_date | DATE | When created in SF | Account.CreatedDate |
| is_current | BOOLEAN | SCD2 current flag | Derived |
| valid_from | TIMESTAMP | SCD2 start | Derived |
| valid_to | TIMESTAMP | SCD2 end | Derived |

**Design Decision**: Using SCD Type 2 for accounts because analysts need to see what industry/segment an account was in *when a deal closed*, not what it is today.

### dim_user

| Column | Type | Description | Source |
|--------|------|-------------|--------|
| user_key | INT (SK) | Surrogate key | Generated |
| user_id | VARCHAR | Salesforce ID | User.Id |
| full_name | VARCHAR | Rep name | User.Name |
| email | VARCHAR | Email | User.Email |
| role_name | VARCHAR | Sales role | UserRole.Name |
| department | VARCHAR | Department | User.Department |
| manager_id | VARCHAR | Manager's SF ID | User.ManagerId |
| is_active | BOOLEAN | Still employed | User.IsActive |
| hire_date | DATE | Start date | User.CreatedDate |

### dim_product

| Column | Type | Description | Source |
|--------|------|-------------|--------|
| product_key | INT (SK) | Surrogate key | Generated |
| product_id | VARCHAR | Salesforce ID | Product2.Id |
| product_name | VARCHAR | Product name | Product2.Name |
| product_family | VARCHAR | Product category | Product2.Family |
| product_code | VARCHAR | SKU | Product2.ProductCode |
| is_active | BOOLEAN | Currently sold | Product2.IsActive |
| unit_price | DECIMAL | List price | PricebookEntry.UnitPrice |

### dim_date

| Column | Type | Description |
|--------|------|-------------|
| date_key | INT | YYYYMMDD format |
| date_actual | DATE | The date |
| day_of_week | INT | 1-7 |
| day_name | VARCHAR | Monday, Tuesday... |
| day_of_month | INT | 1-31 |
| day_of_year | INT | 1-366 |
| week_of_year | INT | 1-53 |
| month_actual | INT | 1-12 |
| month_name | VARCHAR | January, February... |
| quarter_actual | INT | 1-4 |
| quarter_name | VARCHAR | Q1, Q2... |
| year_actual | INT | 2024, 2025... |
| fiscal_quarter | INT | Based on Feb fiscal year |
| fiscal_year | INT | Fiscal year |
| is_weekend | BOOLEAN | Saturday/Sunday |
| is_holiday | BOOLEAN | US federal holidays |

**Why a date dimension?** Instead of extracting date parts in every query, pre-compute them once. Also enables fiscal calendar logic in one place.

## Fact Tables

### fct_opportunity

| Column | Type | Description | Source |
|--------|------|-------------|--------|
| opportunity_key | INT (SK) | Surrogate key | Generated |
| opportunity_id | VARCHAR | Salesforce ID | Opportunity.Id |
| account_key | INT (FK) | Link to account | dim_account |
| owner_user_key | INT (FK) | Link to rep | dim_user |
| created_date_key | INT (FK) | When created | dim_date |
| close_date_key | INT (FK) | Expected/actual close | dim_date |
| stage_name | VARCHAR | Current stage | Opportunity.StageName |
| opportunity_type | VARCHAR | New/Renewal/Upsell | Opportunity.Type |
| lead_source | VARCHAR | How they found us | Opportunity.LeadSource |
| amount | DECIMAL | Deal value | Opportunity.Amount |
| expected_revenue | DECIMAL | Amount * probability | Calculated |
| is_won | BOOLEAN | Closed Won | Opportunity.IsWon |
| is_closed | BOOLEAN | Won or Lost | Opportunity.IsClosed |
| days_in_stage | INT | Current stage duration | Calculated |
| days_to_close | INT | Created to close | Calculated |

### fct_activity

| Column | Type | Description | Source |
|--------|------|-------------|--------|
| activity_key | INT (SK) | Surrogate key | Generated |
| activity_id | VARCHAR | Salesforce ID | Task.Id |
| account_key | INT (FK) | Related account | dim_account |
| contact_key | INT (FK) | Related contact | dim_contact |
| owner_user_key | INT (FK) | Who did it | dim_user |
| activity_date_key | INT (FK) | When | dim_date |
| activity_type | VARCHAR | Call/Email/Meeting | Task.Type |
| subject | VARCHAR | Activity subject | Task.Subject |
| status | VARCHAR | Open/Completed | Task.Status |
| priority | VARCHAR | High/Normal/Low | Task.Priority |
| duration_minutes | INT | How long | Task.CallDurationInSeconds/60 |

## Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Dimension tables | `dim_<entity>` | dim_account |
| Fact tables | `fct_<event>` | fct_opportunity |
| Surrogate keys | `<entity>_key` | account_key |
| Natural keys | `<entity>_id` | account_id |
| Foreign keys | `<referenced>_key` | account_key in fct_opportunity |
| Booleans | `is_<condition>` | is_won, is_active |
| Dates | `<event>_date` | created_date, close_date |
| Timestamps | `<event>_at` | updated_at |
| Counts | `<thing>_count` | employee_count |
| Amounts | `<thing>_amount` or just name | amount, annual_revenue |

## Slowly Changing Dimensions (SCD)

**Type 1**: Overwrite. Use when history doesn't matter.
- Example: Fixing a typo in account name

**Type 2**: Track history with validity dates. Use when history matters for analysis.
- Example: Account industry changes from "Startup" to "Enterprise"
- We need to know deals closed when they were a "Startup"

**Type 3**: Previous value column. Rarely used.
- Example: `current_industry`, `previous_industry`

We'll use **SCD Type 2** for dim_account and dim_contact since these attributes affect how we segment deals.
