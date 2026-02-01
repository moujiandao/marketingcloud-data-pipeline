-- Campaign ROI Analysis
-- Ranks campaigns by performance and calculates ROI metrics

with campaigns as (
    select * from {{ ref('dim_campaigns') }}
)

select
    campaign_name,
    campaign_type,
    campaign_status,
    start_date,
    end_date,
    campaign_duration_days,

    -- Member metrics
    total_members,
    responded_members,
    response_rate,

    -- Financial metrics
    budgeted_cost,
    actual_cost,
    expected_revenue,

    -- ROI calculations
    expected_revenue - actual_cost as expected_profit,
    round((expected_revenue - actual_cost) / nullif(actual_cost, 0) * 100, 2) as roi_percent,

    -- Efficiency metrics
    round(actual_cost / nullif(total_members, 0), 2) as cost_per_member,
    round(actual_cost / nullif(responded_members, 0), 2) as cost_per_response,

    -- Performance classification
    performance_category,

    -- Budget variance
    actual_cost - budgeted_cost as budget_variance,
    round((actual_cost - budgeted_cost) / nullif(budgeted_cost, 0) * 100, 2) as budget_variance_pct

from campaigns

where actual_cost > 0  -- Only include campaigns with spend

order by roi_percent desc nulls last
