"""Step 4 - Spark Structured Streaming: Kafka -> (Kafka + MongoDB).

    spark-submit jobs/stream_invoices.py          (the `spark-stream` service runs this)

Two sinks, two lessons:
  1. Kafka -> transformed JSON -> Kafka topic `spark-output` (stream-to-stream, e.g. for other consumers)
  2. Kafka -> nested invoice documents -> MongoDB via foreachBatch + idempotent bulk upserts

Each sink has its own checkpoint: Kafka offsets are committed in the checkpoint only after the batch was
written, so a crash replays the last batch (at-least-once) and the idempotent Mongo upsert makes the
end result exactly-once.
The same code, cell by cell with explanations, is in notebooks/stream_invoices.ipynb.
"""

from __future__ import annotations

import os

from pymongo import MongoClient
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, IntegerType, StringType, StructField, StructType, TimestampType

from mongo_sink import build_updates

KAFKA = os.environ.get("KAFKA_BOOTSTRAP", "kafka:9092")
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://app:app@mongo:27017/invoices?authSource=invoices")
CHECKPOINTS = os.environ.get("CHECKPOINT_DIR", "/lab/checkpoints")

ITEM_SCHEMA = StructType(
    [
        StructField("InvoiceNo", StringType(), nullable=False),
        StructField("StockCode", StringType(), nullable=False),
        StructField("Description", StringType()),
        StructField("Quantity", IntegerType()),
        StructField("InvoiceDate", TimestampType()),
        StructField("UnitPrice", DoubleType()),
        StructField("CustomerID", StringType()),
        StructField("Country", StringType()),
    ]
)


def read_items(spark: SparkSession) -> DataFrame:
    raw = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", KAFKA)
        .option("subscribe", "ingestion-topic")
        .option("startingOffsets", "earliest")
        .option("maxOffsetsPerTrigger", 5000)  # backpressure: bounded micro-batches
        .load()
    )
    return (
        raw.select(F.from_json(F.col("value").cast("string"), ITEM_SCHEMA).alias("item"), "timestamp")
        .select("item.*", F.col("timestamp").alias("kafka_ts"))
        .where(F.col("InvoiceNo").isNotNull())
    )


def write_to_mongo(batch: DataFrame, batch_id: int) -> None:
    rows = [r.asDict() for r in batch.drop("kafka_ts").collect()]  # micro-batches are small (<= 5000 rows)
    if not rows:
        return
    updates = build_updates(rows)
    with MongoClient(MONGO_URI) as client:
        result = client.get_default_database()["invoices"].bulk_write(updates, ordered=False)
    print(
        f"batch {batch_id}: {len(rows)} items -> {len(updates)} invoices "
        f"(upserted {result.upserted_count}, modified {result.modified_count})",
        flush=True,
    )


def main() -> None:
    spark = (
        SparkSession.builder.appName("invoice-streaming")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    items = read_items(spark)

    # Sink 1: enriched JSON back to Kafka (line total added), key kept = InvoiceNo
    to_kafka = (
        items.withColumn("LineTotal", F.round(F.col("Quantity") * F.col("UnitPrice"), 2))
        .select(F.col("InvoiceNo").alias("key"), F.to_json(F.struct(*ITEM_SCHEMA.fieldNames(), "LineTotal")).alias("value"))
        .writeStream.format("kafka")
        .option("kafka.bootstrap.servers", KAFKA)
        .option("topic", "spark-output")
        .option("checkpointLocation", f"{CHECKPOINTS}/spark-output")
        .start()
    )

    # Sink 2: nested invoice documents in MongoDB
    to_mongo = (
        items.writeStream.foreachBatch(write_to_mongo)
        .option("checkpointLocation", f"{CHECKPOINTS}/mongo")
        .trigger(processingTime="5 seconds")
        .start()
    )
    print("streaming: ingestion-topic -> spark-output + mongodb.invoices", flush=True)
    spark.streams.awaitAnyTermination()
    to_kafka.stop()
    to_mongo.stop()


if __name__ == "__main__":
    main()
