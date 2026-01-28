{{
    config(
        materialized='table'
    )
}}

-- Dimension table for products
-- Provides descriptive attributes about products we sell

with products as (

    select * from {{ ref('stg_salesforce__products') }}

)

select
    -- Primary key
    product_id,

    -- Descriptive attributes
    product_name,
    product_code,
    product_family,
    product_description,
    is_active,

    -- Audit fields
    created_date,
    loaded_at

from products
