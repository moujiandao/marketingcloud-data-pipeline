{{
    config(
        materialized='view'
    )
}}

with source as (

    select * from {{ source('salesforce', 'products') }}

),

renamed as (

    select
        -- Primary key
        id as product_id,

        -- Attributes
        name as product_name,
        product_code,
        family as product_family,
        description as product_description,
        is_active,

        -- Timestamps
        created_date,

        -- Metadata
        loaded_at

    from source

)

select * from renamed
