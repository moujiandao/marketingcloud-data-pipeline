-- Test that all opportunity amounts are positive
-- This test will fail if any rows are returned

select
    opportunity_id,
    amount
from {{ ref('fct_opportunities') }}
where amount < 0
