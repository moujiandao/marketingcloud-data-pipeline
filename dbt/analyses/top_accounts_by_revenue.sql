-- Top Accounts by Revenue
-- Shows highest value accounts with opportunity metrics

with opportunities as (
    select * from {{ ref('fct_opportunities') }}
),

accounts as (
    select * from {{ ref('dim_accounts') }}
)

select
    a.account_name,
    a.industry,
    a.account_type,

    count(o.opportunity_id) as total_opportunities,
    count(case when o.is_won then 1 end) as won_opportunities,
    count(case when o.is_closed and not o.is_won then 1 end) as lost_opportunities,
    count(case when not o.is_closed then 1 end) as open_opportunities,

    sum(o.amount) as total_pipeline_value,
    sum(case when o.is_won then o.amount else 0 end) as total_revenue,
    avg(o.amount) as avg_deal_size,

    round(100.0 * count(case when o.is_won then 1 end) / nullif(count(case when o.is_closed then 1 end), 0), 2) as win_rate_pct

from accounts a
left join opportunities o on a.account_id = o.account_id

group by
    a.account_id,
    a.account_name,
    a.industry,
    a.account_type

having count(o.opportunity_id) > 0  -- Only accounts with opportunities

order by total_revenue desc

limit 20
