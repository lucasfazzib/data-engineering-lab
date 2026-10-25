-- EXERCISE 3 — set up Postgres the way Debezium needs it. Run with: make exercise N=03
-- This is exactly what you'll automate in example 05.
\pset pager off

-- TODO 1: create a PUBLICATION named cdc_pub for tables customers and orders.

-- TODO 2: create a logical replication slot named cdc_slot using the pgoutput plugin.

-- TODO 3: make UPDATE and DELETE events on orders carry the full old row. Which setting? What does it cost?

-- TODO 4: write the monitoring query you'd put on a dashboard/alert: for every slot,
--         show active, the WAL it retains (pretty-printed) and the consumer lag.

-- TODO 5: clean up (drop the slot and the publication). What happens if you forget the slot?
