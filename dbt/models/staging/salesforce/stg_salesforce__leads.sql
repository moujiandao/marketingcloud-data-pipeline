{{
    config(
        materialized='view'
    )
}}

with source as (

    select * from {{ source('salesforce', 'leads') }}

),

renamed as (

    select
        -- Primary key
        id as lead_id,

        -- Foreign keys
        owner_id as owner_user_id,

        -- Attributes
        first_name,
        last_name,
        first_name || ' ' || last_name as full_name,
        company,
        title,
        email,
        phone,
        status as lead_status,
        rating as lead_rating,
        lead_source,
        industry,
        annual_revenue,
        number_of_employees,

        -- Address
        street,
        city,
        state,
        postal_code,
        country,

        -- Conversion tracking
        is_converted,
        converted_account_id,
        converted_contact_id,
        converted_opportunity_id,
        converted_date,

        -- Timestamps
        created_date,
        last_modified_date,

        -- Flags
        is_deleted,

        -- Metadata
        loaded_at

    from source

)

select * from renamed
