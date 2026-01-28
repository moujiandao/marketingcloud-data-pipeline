{{
    config(
        materialized='view'
    )
}}

with opportunities as (

    select * from {{ ref('stg_salesforce__opportunities') }}

),

accounts as (

    select * from {{ ref('stg_salesforce__accounts') }}

),

users as (

    select * from {{ ref('stg_salesforce__users') }}

),

joined as (

    select
        -- Opportunity fields
        opp.opportunity_id,
        opp.opportunity_name,
        opp.stage_name,
        opp.amount,
        opp.probability,
        opp.close_date,
        opp.is_closed,
        opp.is_won,
        opp.lead_source,
        opp.opportunity_type,
        opp.created_date as opportunity_created_date,
        opp.loaded_at,

        -- Account fields
        acc.account_id,
        acc.account_name,
        acc.industry,
        acc.account_type,

        -- Owner/User fields
        usr.user_id as owner_user_id,
        usr.user_name as owner_name,
        usr.email as owner_email,
        usr.department as owner_department,

        -- Calculated fields
        current_date - opp.created_date as deal_age_days,
        opp.close_date - opp.created_date as sales_cycle_days,
        opp.amount * (opp.probability / 100.0) as expected_revenue,

        -- Stage categorization
        case
            when opp.stage_name in ('Prospecting', 'Qualification') then 'Early'
            when opp.stage_name in ('Needs Analysis', 'Value Proposition', 'Proposal/Price Quote') then 'Middle'
            when opp.stage_name in ('Negotiation/Review', 'Closed Won', 'Closed Lost') then 'Late'
            else 'Unknown'
        end as stage_category,

        -- Win/loss categorization
        case
            when opp.is_won then 'Won'
            when opp.is_closed and not opp.is_won then 'Lost'
            when not opp.is_closed then 'Open'
            else 'Unknown'
        end as deal_status

    from opportunities as opp
    left join accounts as acc on opp.account_id = acc.account_id
    left join users as usr on opp.owner_user_id = usr.user_id

)

select * from joined
