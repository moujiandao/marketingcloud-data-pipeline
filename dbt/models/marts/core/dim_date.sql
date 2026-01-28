{{
    config(
        materialized='table'
    )
}}

-- Dimension table for dates
-- Provides date attributes for time-based analysis
-- Generated for 2022-01-01 through 2026-12-31

with date_spine as (

    -- Generate a series of dates using PostgreSQL generate_series
    select
        generate_series(
            '2022-01-01'::date,
            '2026-12-31'::date,
            '1 day'::interval
        )::date as date_day

),

date_dimension as (

    select
        -- Primary key
        date_day,

        -- Date parts
        extract(year from date_day) as year,
        extract(quarter from date_day) as quarter,
        extract(month from date_day) as month,
        extract(week from date_day) as week_of_year,
        extract(day from date_day) as day_of_month,
        extract(dow from date_day) as day_of_week,  -- 0 = Sunday, 6 = Saturday
        extract(doy from date_day) as day_of_year,

        -- Formatted strings
        to_char(date_day, 'YYYY-MM') as year_month,
        to_char(date_day, 'YYYY-Q') as year_quarter,
        to_char(date_day, 'Month') as month_name,
        to_char(date_day, 'Day') as day_name,

        -- Business logic
        case
            when extract(dow from date_day) in (0, 6) then false
            else true
        end as is_weekday,

        case
            when extract(dow from date_day) in (0, 6) then true
            else false
        end as is_weekend,

        -- Fiscal year (starts in February based on var)
        case
            when extract(month from date_day) >= {{ var('fiscal_year_start_month', 2) }}
            then extract(year from date_day)
            else extract(year from date_day) - 1
        end as fiscal_year,

        -- Quarter end flag (useful for identifying quarter-end patterns)
        case
            when date_day = (date_trunc('quarter', date_day) + interval '3 months - 1 day')::date
            then true
            else false
        end as is_quarter_end,

        -- Month end flag
        case
            when date_day = (date_trunc('month', date_day) + interval '1 month - 1 day')::date
            then true
            else false
        end as is_month_end

    from date_spine

)

select * from date_dimension
