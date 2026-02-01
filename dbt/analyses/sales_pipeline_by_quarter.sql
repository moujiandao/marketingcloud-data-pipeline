-- Sales Pipeline Analysis by Quarter
-- Shows total pipeline value, expected revenue, and deal counts by quarter

with opportunities as (
    select * from {{ ref('fct_opportunities') }}
),

dates as (
    select * from {{ ref('dim_date') }}
)

select
    d.year_quarter,
    count(o.opportunity_id) as total_opportunities,
    count(case when o.is_won then 1 end) as won_count,
    count(case when o.is_closed and not o.is_won then 1 end) as lost_count,
    count(case when not o.is_closed then 1 end) as open_count,

    sum(o.amount) as total_pipeline_value,
    sum(o.expected_revenue) as total_expected_revenue,
    avg(o.amount) as avg_deal_size,
    avg(o.sales_cycle_days) as avg_sales_cycle_days,

    round(100.0 * count(case when o.is_won then 1 end) / nullif(count(case when o.is_closed then 1 end), 0), 2) as win_rate_pct

from opportunities o
left join dates d on o.date_key = d.date_day

group by d.year_quarter
order by d.year_quarter
