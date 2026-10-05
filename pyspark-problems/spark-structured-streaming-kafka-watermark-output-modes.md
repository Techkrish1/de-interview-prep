# Spark Structured Streaming — Kafka, Watermarks, and Output Modes

**Type:** PySpark Problem
**Topic:** Spark Structured Streaming, Kafka, Watermarks, Checkpoints

---

## The Question
> "Walk me through Spark Structured Streaming — how does it work, how do you read from Kafka, and what output modes are available?"

---

## Mental Model

Structured Streaming treats a live data stream as an **infinite table** that keeps growing. You write the same DataFrame API as batch — Spark executes it incrementally through micro-batches.

```
Kafka topic (rows keep arriving)
         ↓
   Treated as an infinite table
         ↓
   DataFrame transformations (same API as batch)
         ↓
   Results written to sink incrementally
```

---

## Reading from Kafka

```python
raw = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "broker:9092")
    .option("subscribe", "orders")
    .option("startingOffsets", "latest")   # "earliest" to replay all history
    .load()
)

# Kafka delivers: key, value (binary), topic, partition, offset, timestamp
# Parse the JSON payload:
schema = StructType() \
    .add("order_id",   LongType()) \
    .add("customer_id", LongType()) \
    .add("amount",     "double") \
    .add("event_time", "timestamp")

orders = raw.select(
    F.from_json(F.col("value").cast("string"), schema).alias("d")
).select("d.*")
```

---

## Windowed Aggregation with Watermark

```python
result = (
    orders
    .withWatermark("event_time", "10 minutes")     # accept up to 10min late
    .groupBy(
        F.window("event_time", "5 minutes"),        # 5-min tumbling window
        "customer_id"
    )
    .agg(F.sum("amount").alias("total_spend"))
)
```

Watermark = how long to wait for late data before finalizing a window and emitting it in append mode.

---

## Output Modes

| Mode | What gets written each trigger | When to use |
|---|---|---|
| **append** | Only NEW finalized rows | Aggregations with watermark; raw event forwarding |
| **complete** | Entire result table | Small aggregations you want fully refreshed |
| **update** | Only rows that changed | Aggregations without watermark |

Rule: aggregations without watermark → only `complete` or `update`. With watermark → `append` works.

---

## Writing with Checkpoint

```python
query = (
    result.writeStream
    .outputMode("append")
    .format("delta")
    .option("checkpointLocation", "s3://checkpoints/orders-stream")
    .option("path", "s3://output/customer-spend")
    .trigger(processingTime="1 minute")
    .start()
)
query.awaitTermination()
```

Checkpoint stores:
1. Committed Kafka offsets (prevents reprocessing)
2. Intermediate aggregation state (recovers in-progress windows after crash)

**Without checkpoint**: job restarts from `startingOffsets` on failure — potentially reprocesses everything.

---

## Trigger Modes

```python
.trigger(processingTime="30 seconds")   # fixed interval micro-batch
.trigger(once=True)                     # one micro-batch then stop
.trigger(availableNow=True)             # process backlog then stop (Spark 3.3+)
```

`availableNow=True` is useful for Airflow-scheduled streaming runs — process what's available, stop, reschedule.

---

## foreachBatch — Escape Hatch

When built-in sinks don't fit (multi-table writes, custom upserts):

```python
def process_batch(batch_df, batch_id):
    batch_df.write.format("delta").mode("append").save("s3://output")

query.writeStream.foreachBatch(process_batch).start()
```

Each micro-batch arrives as a static DataFrame — apply any batch logic.

---

## How to Say It in the Interview
> "Structured Streaming treats a live stream as an infinite table — you write the same DataFrame API as batch, and Spark handles incremental micro-batch execution. To read from Kafka you use readStream, then parse the binary value column with from_json. Watermarks define how long to wait for late data before finalizing a window. The three output modes control what gets written per trigger: append for finalized rows, complete for the full result, update for changed rows. Checkpointing is essential — it saves Kafka offsets and aggregation state so the job recovers from failures without reprocessing."

---

## Follow-ups & Answers

**"Micro-batch vs continuous processing?"**
> Micro-batch (default) runs at fixed intervals — 30s+ latency, stable, full operator support. Continuous processing (experimental) processes records as they arrive with ~1ms latency but limited operator support. Micro-batch is sufficient for most DE use cases.

**"foreachBatch use case?"**
> When you need upserts (Delta MERGE), write to multiple sinks, or apply deduplication logic that doesn't fit built-in operators. Each micro-batch becomes a static DataFrame you manipulate freely.

**"Structured Streaming vs Flink?"**
> Spark Structured Streaming: micro-batch, best for teams on Spark, tight Delta Lake integration. Flink: true streaming, millisecond latency, best-in-class stateful operators — preferred when latency is critical.

---

## Common Mistakes
- Forgetting checkpoint — job restarts from beginning on crash
- Using `complete` mode on large unbounded aggregations — rewrites entire table every trigger
- Not setting watermark and wondering why windows never emit in `append` mode
- Not casting Kafka `value` to String before `from_json` — it's binary by default

---

## Key Concepts Tested
- Infinite table mental model, micro-batch execution
- Kafka readStream and JSON parsing
- Watermark for late data
- Output modes: append / complete / update
- Checkpointing: offsets + state recovery
- Trigger modes including `availableNow`
- `foreachBatch` escape hatch
