{{
    config(
        materialized='view'
    )
}}

with source as (

    select * from {{ source('salesforce', 'campaign_members') }}

),

renamed as (

    select
        -- Primary key
        id as campaign_member_id,

        -- Foreign keys
        campaign_id,
        lead_id,
        contact_id,

        -- Attributes
        status as member_status,
        has_responded,

        -- Timestamps
        created_date,
        last_modified_date,

        -- Metadata
        loaded_at

    from source

)

select * from renamed
