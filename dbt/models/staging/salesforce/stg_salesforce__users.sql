{{
    config(
        materialized='view'
    )
}}

with source as (

    select * from {{ source('salesforce', 'users') }}

),

renamed as (

    select
        -- Primary key
        id as user_id,

        -- Attributes
        name as user_name,
        email,
        username,
        department,
        is_active,

        -- Foreign keys
        user_role_id,
        manager_id as manager_user_id,

        -- Timestamps
        created_date,

        -- Metadata
        loaded_at

    from source

)

select * from renamed
