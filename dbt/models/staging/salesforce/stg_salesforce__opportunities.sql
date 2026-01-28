{{
    config(
        materialized='view'
    )
}}

with source as (

    select * from {{ source('salesforce', 'opportunities') }}

),

renamed as (

    select
        -- Primary key
        id as opportunity_id,

        -- Foreign keys
        account_id,
        owner_id as owner_user_id,

        -- Attributes
        name as opportunity_name,
        stage_name,
        type as opportunity_type,
        lead_source,
        amount,
        probability,

        -- Flags
        is_closed,
        is_won,

        -- Dates
        close_date,
        created_date,
        last_modified_date,

        -- Metadata
        loaded_at

    from source

)

select * from renamed
