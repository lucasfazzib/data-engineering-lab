-- Calendar dimension covering the dataset period. date_key (YYYYMMDD) is the join key used by the facts.
with spine as (

    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2016-01-01' as date)",
        end_date="cast('2019-01-01' as date)"
    ) }}

)

select
    cast(strftime(date_day, '%Y%m%d') as integer)   as date_key,
    cast(date_day as date)                          as date_day,
    year(date_day)                                  as year,
    quarter(date_day)                               as quarter,
    month(date_day)                                 as month,
    strftime(date_day, '%B')                        as month_name,
    cast(date_trunc('month', date_day) as date)     as month_start,
    weekofyear(date_day)                            as iso_week,
    isodow(date_day)                                as iso_day_of_week,
    strftime(date_day, '%A')                        as day_name,
    isodow(date_day) in (6, 7)                      as is_weekend

from spine
