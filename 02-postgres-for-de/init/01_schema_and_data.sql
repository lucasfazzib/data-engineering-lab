-- Runs once, on the first start of an empty volume.
create extension if not exists pg_stat_statements;

create table customers (
    customer_id  bigint generated always as identity primary key,
    email        text not null,
    country_code char(2) not null,
    tier         text not null,
    created_at   timestamptz not null
);

create table orders (
    order_id     bigint generated always as identity primary key,
    customer_id  bigint not null references customers (customer_id),
    status       text not null,
    amount       numeric(12, 2) not null,
    created_at   timestamptz not null,
    attributes   jsonb not null default '{}'
);

-- 50k customers, 1M orders over the last ~365 days (deterministic)
select setseed(0.42);

insert into customers (email, country_code, tier, created_at)
select
    'user' || g || '@example.com',
    (array['BR', 'BR', 'BR', 'US', 'PT', 'AR', 'DE', 'MX'])[1 + floor(random() * 8)::int],
    (array['basic', 'basic', 'basic', 'plus', 'premium'])[1 + floor(random() * 5)::int],
    now() - interval '730 days' + (g * interval '20 minutes')
from generate_series(1, 50000) as g;

insert into orders (customer_id, status, amount, created_at, attributes)
select
    1 + floor(random() * 50000)::bigint,
    (array['delivered', 'delivered', 'delivered', 'delivered', 'shipped', 'placed', 'cancelled', 'returned'])[1 + floor(random() * 8)::int],
    round((5 + random() * 495)::numeric, 2),
    now() - interval '365 days' + (g * interval '31.5 seconds'),
    jsonb_build_object(
        'channel', (array['web', 'app', 'app', 'marketplace'])[1 + floor(random() * 4)::int],
        'coupon', case when random() < 0.05 then 'PROMO' || floor(random() * 10)::int end
    )
from generate_series(1, 1000000) as g;

analyze customers;
analyze orders;
