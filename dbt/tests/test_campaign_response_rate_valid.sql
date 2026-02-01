-- Test that campaign response rates are between 0 and 100
-- Response rate is a percentage and should be in valid range

select
    campaign_id,
    campaign_name,
    response_rate
from {{ ref('dim_campaigns') }}
where response_rate < 0
   or response_rate > 100
