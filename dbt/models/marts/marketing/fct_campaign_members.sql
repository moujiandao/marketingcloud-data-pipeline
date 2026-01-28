{{
    config(
        materialized='table'
    )
}}

-- Fact table for campaign members
-- Grain: One row per campaign member (person in a campaign)
-- Contains foreign keys to dimensions and measures

with campaign_members as (

    select * from {{ ref('stg_salesforce__campaign_members') }}

)

select
    -- Fact primary key
    campaign_member_id,

    -- Foreign keys to dimensions
    campaign_id,
    contact_id,
    lead_id,
    created_date as date_key,  -- FK to dim_date

    -- Degenerate dimensions
    member_status,

    -- Numeric measures (for aggregation)
    case when has_responded then 1 else 0 end as responded_count,
    1 as member_count,  -- Always 1, used for counting members

    -- Flags
    has_responded,

    -- Audit
    created_date,
    last_modified_date,
    loaded_at

from campaign_members
