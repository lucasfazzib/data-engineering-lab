-- Source database for CDC. Runs once on the first start.

create table customers (
    id         serial primary key,
    name       text not null,
    email      text not null,
    tier       text not null default 'basic',
    updated_at timestamptz not null default now()
);

create table orders (
    id          serial primary key,
    customer_id int not null references customers (id),
    status      text not null,
    amount      numeric(10, 2) not null,
    updated_at  timestamptz not null default now()
);

-- Transactional outbox (exercise 3): the service writes business rows AND an event row in the same transaction.
create table outbox (
    id            uuid primary key default gen_random_uuid(),
    aggregatetype text not null,          -- routes the event to a topic, e.g. "order" -> outbox.event.order
    aggregateid   text not null,          -- becomes the Kafka message key
    type          text not null,          -- event type, e.g. "OrderPlaced"
    payload       jsonb not null,
    created_at    timestamptz not null default now()
);

-- Full before-image on UPDATE/DELETE for orders (see example 02, lesson 03)
alter table orders replica identity full;

insert into customers (name, email, tier)
select 'Customer ' || g, 'customer' || g || '@example.com', (array['basic', 'plus', 'premium'])[1 + g % 3]
from generate_series(1, 20) g;

insert into orders (customer_id, status, amount)
select 1 + (g % 20), 'placed', round((10 + g * 3.7)::numeric, 2)
from generate_series(1, 50) g;

-- Least privilege: a dedicated CDC user with REPLICATION, read access, and a pre-created publication
-- (so the connector does not need to own the tables).
create role debezium with login replication password 'debezium'; -- local-only credentials
grant select on all tables in schema public to debezium;
create publication dbz_shop for table customers, orders, outbox;
