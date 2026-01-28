{{
    config(
        materialized='view'
    )
}}

with contacts as (

    select * from {{ ref('stg_salesforce__contacts') }}

),

accounts as (

    select * from {{ ref('stg_salesforce__accounts') }}

),

tasks as (

    select * from {{ ref('stg_salesforce__tasks') }}

),

opportunities as (

    select * from {{ ref('stg_salesforce__opportunities') }}

),

-- Aggregate task activity per contact
contact_tasks as (

    select
        contact_id,
        count(*) as total_tasks,
        count(case when task_status = 'Completed' then 1 end) as completed_tasks,
        count(case when task_type = 'Call' then 1 end) as call_tasks,
        count(case when task_type = 'Email' then 1 end) as email_tasks,
        max(activity_date) as last_activity_date,
        sum(call_duration_in_seconds) as total_call_duration_seconds

    from tasks
    where contact_id is not null
    group by contact_id

),

-- Aggregate opportunity data per contact
contact_opportunities as (

    select
        contact_id,
        count(*) as total_opportunities,
        count(case when is_won then 1 end) as won_opportunities,
        count(case when is_closed and not is_won then 1 end) as lost_opportunities,
        sum(amount) as total_opportunity_value,
        sum(case when is_won then amount else 0 end) as won_opportunity_value,
        max(close_date) as most_recent_close_date

    from opportunities
    where contact_id is not null
    group by contact_id

),

joined as (

    select
        -- Contact fields
        con.contact_id,
        con.first_name,
        con.last_name,
        con.email,
        con.phone,
        con.title,
        con.department,
        con.lead_source,
        con.created_date as contact_created_date,
        con.loaded_at,

        -- Account fields
        acc.account_id,
        acc.account_name,
        acc.industry,
        acc.account_type,

        -- Task metrics
        coalesce(t.total_tasks, 0) as total_tasks,
        coalesce(t.completed_tasks, 0) as completed_tasks,
        coalesce(t.call_tasks, 0) as call_tasks,
        coalesce(t.email_tasks, 0) as email_tasks,
        t.last_activity_date,
        coalesce(t.total_call_duration_seconds, 0) as total_call_duration_seconds,

        -- Opportunity metrics
        coalesce(opp.total_opportunities, 0) as total_opportunities,
        coalesce(opp.won_opportunities, 0) as won_opportunities,
        coalesce(opp.lost_opportunities, 0) as lost_opportunities,
        coalesce(opp.total_opportunity_value, 0) as total_opportunity_value,
        coalesce(opp.won_opportunity_value, 0) as won_opportunity_value,
        opp.most_recent_close_date,

        -- Calculated engagement metrics
        case
            when coalesce(t.total_tasks, 0) = 0 then 0
            else round(100.0 * coalesce(t.completed_tasks, 0) / t.total_tasks, 2)
        end as task_completion_rate,

        case
            when coalesce(opp.total_opportunities, 0) = 0 then 0
            else round(100.0 * coalesce(opp.won_opportunities, 0) / opp.total_opportunities, 2)
        end as win_rate,

        current_date - con.created_date as contact_age_days,
        current_date - t.last_activity_date as days_since_last_activity,

        -- Engagement scoring
        case
            when coalesce(t.total_tasks, 0) >= 10 and coalesce(opp.total_opportunities, 0) >= 3 then 'High'
            when coalesce(t.total_tasks, 0) >= 5 and coalesce(opp.total_opportunities, 0) >= 1 then 'Medium'
            else 'Low'
        end as engagement_level

    from contacts as con
    left join accounts as acc on con.account_id = acc.account_id
    left join contact_tasks as t on con.contact_id = t.contact_id
    left join contact_opportunities as opp on con.contact_id = opp.contact_id

)

select * from joined
