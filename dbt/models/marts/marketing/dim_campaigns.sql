{{
    config(
        materialized='table'
    )
}}

-- Dimension table for campaigns
-- Provides descriptive attributes about marketing campaigns

with campaign_performance as (

    select * from {{ ref('int_campaign_performance') }}

)

select
    -- Primary key
    campaign_id,

    -- Descriptive attributes
    campaign_name,
    campaign_type,
    campaign_status,
    is_active,

    -- Financial attributes
    budgeted_cost,
    actual_cost,
    expected_revenue,

    -- Performance metrics (denormalized)
    total_members,
    responded_members,
    response_rate,
    performance_category,

    -- Date attributes
    start_date,
    end_date,
    campaign_duration_days,

    -- Audit fields
    campaign_created_date,
    loaded_at

from campaign_performance
