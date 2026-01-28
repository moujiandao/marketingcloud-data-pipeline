{{
    config(
        materialized='view'
    )
}}

with source as (

    select * from {{ source('salesforce', 'contacts') }}

),

renamed as (

    select
        -- Primary key
        id as contact_id,

        -- Foreign keys
        account_id,
        owner_id as owner_user_id,

        -- Attributes
        first_name,
        last_name,
        first_name || ' ' || last_name as full_name,
        email,
        phone,
        title,
        department,
        lead_source,

        -- Timestamps
        created_date,

        -- Metadata
        loaded_at

    from source

)

select * from renamed
