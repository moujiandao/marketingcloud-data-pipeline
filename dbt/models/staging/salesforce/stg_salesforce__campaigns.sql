{{
    config(
        materialized='view'
    )
}}

with source as (

    select * from {{ source('salesforce', 'campaigns') }}

),

renamed as (

    select
        -- Primary key
        id as campaign_id,

        -- Foreign keys
        parent_id as parent_campaign_id,
        owner_id as owner_user_id,

        -- Attributes
        name as campaign_name,
        type as campaign_type,
        status as campaign_status,
        description,
        is_active,

        -- Metrics
        budgeted_cost,
        actual_cost,
        expected_revenue,
        number_sent,

        -- Dates
        start_date,
        end_date,
        created_date,
        last_modified_date,

        -- Flags
        is_deleted,

        -- Metadata
        loaded_at

    from source

)

select * from renamed
