{{
    config(
        materialized='table'
    )
}}

-- Dimension table for contacts
-- Provides descriptive attributes about people at customer companies

with contacts_enriched as (

    select * from {{ ref('int_contacts_enriched') }}

)

select
    -- Primary key
    contact_id,

    -- Descriptive attributes
    first_name,
    last_name,
    email,
    phone,
    title,
    department,
    lead_source,

    -- Account reference (denormalized)
    account_id,
    account_name,
    industry,
    account_type,

    -- Engagement metrics (denormalized for convenience)
    total_tasks,
    completed_tasks,
    total_opportunities,
    won_opportunities,
    engagement_level,

    -- Audit fields
    contact_created_date,
    loaded_at

from contacts_enriched
