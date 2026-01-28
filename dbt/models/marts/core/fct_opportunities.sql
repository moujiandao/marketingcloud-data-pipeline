{{
    config(
        materialized='table'
    )
}}

-- Fact table for opportunities
-- Grain: One row per opportunity
-- Contains foreign keys to dimensions and numeric measures

with opportunities_enhanced as (

    select * from {{ ref('int_opportunities_enhanced') }}

)

select
    -- Fact primary key
    opportunity_id,

    -- Foreign keys to dimensions
    account_id,
    owner_user_id,
    close_date as date_key,  -- FK to dim_date

    -- Degenerate dimensions (high-cardinality attributes stored in fact)
    opportunity_name,
    stage_name,
    stage_category,
    deal_status,
    lead_source,
    opportunity_type,

    -- Numeric measures (additive)
    amount,
    probability,
    expected_revenue,

    -- Numeric measures (semi-additive - make sense to sum within certain contexts)
    deal_age_days,
    sales_cycle_days,

    -- Flags
    is_closed,
    is_won,

    -- Audit
    opportunity_created_date,
    loaded_at

from opportunities_enhanced
