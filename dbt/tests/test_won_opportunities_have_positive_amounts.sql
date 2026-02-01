-- Test that won opportunities have positive amounts
-- Won deals should have revenue > 0

select
    opportunity_id,
    amount,
    is_won
from {{ ref('fct_opportunities') }}
where is_won = true
  and (amount is null or amount <= 0)
