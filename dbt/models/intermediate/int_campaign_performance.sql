{{
    config(
        materialized='view'
    )
}}

with campaigns as (

    select * from {{ ref('stg_salesforce__campaigns') }}

),

campaign_members as (

    select * from {{ ref('stg_salesforce__campaign_members') }}

),

-- Aggregate member metrics per campaign
campaign_metrics as (

    select
        campaign_id,
        count(*) as total_members,
        count(case when has_responded then 1 end) as responded_members,
        count(case when contact_id is not null then 1 end) as contact_members,
        count(case when lead_id is not null then 1 end) as lead_members,
        count(distinct member_status) as unique_statuses,
        max(created_date) as most_recent_member_date

    from campaign_members
    group by campaign_id

),

joined as (

    select
        -- Campaign fields
        c.campaign_id,
        c.campaign_name,
        c.campaign_type,
        c.campaign_status,
        c.start_date,
        c.end_date,
        c.expected_revenue,
        c.budgeted_cost,
        c.actual_cost,
        c.number_sent,
        c.is_active,
        c.created_date as campaign_created_date,
        c.loaded_at,

        -- Member metrics
        coalesce(m.total_members, 0) as total_members,
        coalesce(m.responded_members, 0) as responded_members,
        coalesce(m.contact_members, 0) as contact_members,
        coalesce(m.lead_members, 0) as lead_members,
        m.most_recent_member_date,

        -- Calculated metrics
        case
            when coalesce(m.total_members, 0) = 0 then 0
            else round(100.0 * coalesce(m.responded_members, 0) / m.total_members, 2)
        end as response_rate,

        case
            when c.number_sent = 0 then 0
            else round(100.0 * coalesce(m.total_members, 0) / c.number_sent, 2)
        end as member_to_sent_ratio,

        case
            when coalesce(m.total_members, 0) = 0 then 0
            else round(c.actual_cost / m.total_members, 2)
        end as cost_per_member,

        case
            when coalesce(m.responded_members, 0) = 0 then 0
            else round(c.actual_cost / m.responded_members, 2)
        end as cost_per_response,

        case
            when c.actual_cost = 0 then 0
            else round(100.0 * (c.expected_revenue - c.actual_cost) / c.actual_cost, 2)
        end as expected_roi_percent,

        -- Campaign duration
        c.end_date - c.start_date as campaign_duration_days,
        current_date - c.start_date as days_since_start,

        -- Campaign effectiveness categorization
        case
            when coalesce(m.responded_members, 0) = 0 then 'No Response'
            when round(100.0 * coalesce(m.responded_members, 0) / nullif(m.total_members, 0), 2) >= 20 then 'High Performance'
            when round(100.0 * coalesce(m.responded_members, 0) / nullif(m.total_members, 0), 2) >= 10 then 'Medium Performance'
            else 'Low Performance'
        end as performance_category

    from campaigns as c
    left join campaign_metrics as m on c.campaign_id = m.campaign_id

)

select * from joined
