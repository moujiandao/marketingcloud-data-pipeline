{{
    config(
        materialized='view'
    )
}}

with source as (

    select * from {{ source('salesforce', 'accounts') }}

),

renamed as (

    select
        -- Primary key
        id as account_id,

        -- Attributes
        name as account_name,
        industry,
        type as account_type,
        number_of_employees,
        annual_revenue,

        -- Address
        billing_street,
        billing_city,
        billing_state,
        billing_postal_code,
        billing_country,

        -- Foreign keys
        owner_id as owner_user_id,

        -- Timestamps
        created_date,
        last_modified_date,

        -- Metadata
        loaded_at

    from source

)

select * from renamed
