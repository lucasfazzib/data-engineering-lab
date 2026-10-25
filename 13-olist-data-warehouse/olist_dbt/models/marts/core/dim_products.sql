with products as (

    select * from {{ ref('stg_olist__products') }}

),

translations as (

    select * from {{ ref('stg_olist__category_translation') }}

)

select
    {{ dbt_utils.generate_surrogate_key(['products.product_id']) }} as product_key,
    products.product_id,
    coalesce(products.category_name, 'unknown')                                 as category_name,
    -- 2 categories have no translation: fall back to the Portuguese name instead of NULL
    coalesce(translations.category_name_en, products.category_name, 'unknown')  as category_name_en,
    products.photos_qty,
    products.weight_g,
    products.length_cm,
    products.height_cm,
    products.width_cm,
    products.length_cm * products.height_cm * products.width_cm                 as volume_cm3

from products
left join translations on products.category_name = translations.category_name
