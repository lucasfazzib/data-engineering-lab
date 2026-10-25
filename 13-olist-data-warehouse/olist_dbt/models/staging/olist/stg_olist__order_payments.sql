with source as (

    select * from {{ source('olist', 'order_payments') }}

),

renamed as (

    select
        order_id,
        cast(payment_sequential as integer)     as payment_sequential,
        payment_type,
        cast(payment_installments as integer)   as installments,
        cast(payment_value as decimal(12, 2))   as payment_value

    from source

)

select * from renamed
