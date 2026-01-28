{{
    config(
        materialized='table'
    )
}}

-- Dimension table for accounts
-- Provides descriptive attributes about customer companies

with accounts as (

    select * from {{ ref('stg_salesforce__accounts') }}

)

select
    -- Primary key
    account_id,

    -- Descriptive attributes
    account_name,
    industry,
    account_type,

    -- Owner reference (denormalized for convenience)
    owner_user_id,

    -- Audit fields
    created_date,
    loaded_at

from accounts
