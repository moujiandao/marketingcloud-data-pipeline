{{
    config(
        materialized='view'
    )
}}

with source as (

    select * from {{ source('salesforce', 'tasks') }}

),

renamed as (

    select
        -- Primary key
        id as task_id,

        -- Foreign keys
        who_id as contact_id,
        what_id as related_to_id,
        owner_id as owner_user_id,

        -- Attributes
        subject,
        type as task_type,
        status as task_status,
        priority as task_priority,
        description,
        call_duration_in_seconds,

        -- Dates
        activity_date,
        created_date,

        -- Metadata
        loaded_at

    from source

)

select * from renamed
