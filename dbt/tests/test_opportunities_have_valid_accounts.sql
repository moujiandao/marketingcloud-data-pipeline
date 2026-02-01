-- Test referential integrity: all opportunities reference valid accounts
-- This ensures no orphaned fact records

select
    f.opportunity_id,
    f.account_id
from {{ ref('fct_opportunities') }} f
left join {{ ref('dim_accounts') }} d
  on f.account_id = d.account_id
where d.account_id is null
