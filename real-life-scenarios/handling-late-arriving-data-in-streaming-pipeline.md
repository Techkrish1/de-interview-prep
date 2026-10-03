# How Do You Handle Late-Arriving Data in a Streaming Pipeline?

**Type:** Real-life Scenario
**Topic:** Streaming, Watermarks, Late Data, Spark Structured Streaming / Kafka

---

## The Question
> "You have a real-time events pipeline — user clicks are processed as they arrive. Sometimes events arrive 10–30 minutes late due to mobile device connectivity issues. How do you handle this?"

---

## The Problem

```
Event time: when the event actually happened (device clock)
Processing time: when Kafka/Spark sees it

Mobile user clicks at 10:00 → device is offline
Device reconnects at 10:35 → event arrives at Kafka at 10:35
Your pipeline already computed the 10:00 window at 10:05
```

If you ignore this: late events are silently dropped or go into the wrong window.

---

## Solution Architecture

### Option 1 — Watermarks (Spark Structured Streaming)

A watermark tells Spark: "accept events up to X minutes late, then close the window."

```python
from pyspark.sql import functions as F

df = (
    spark.readStream.format("kafka")
    .option("subscribe", "user-clicks")
    .load()
)

events = df.select(
    F.col("value").cast("string").alias("payload"),
    F.col("timestamp").alias("kafka_time")
)

result = (
    events
    .withWatermark("kafka_time", "30 minutes")   # accept up to 30min late
    .groupBy(
        F.window("kafka_time", "10 minutes"),    # 10-min tumbling window
        "user_id"
    )
    .count()
)

result.writeStream.outputMode("append").format("delta").start("s3://output")
```

**What happens:**
- Spark tracks the max event time seen so far — call it `T`
- Watermark threshold = `T - 30 minutes`
- Events with `event_time < watermark` are discarded
- Windows are only finalized and emitted once the watermark passes their end time

### Option 2 — Reprocessing Layer (Lambda/Kappa Architecture)

Speed layer: process events as they arrive (accept some late data loss)
Batch layer: reprocess the last N hours every hour with all late events included — overwrites the speed layer results

```
Kafka → Spark Streaming → DynamoDB (speed layer, approximate)
Kafka → Kafka retention (7 days) → Hourly Spark batch → S3/Delta (corrected)
```

More complex but gives you eventually-consistent correct results.

### Option 3 — Delta Lake MERGE for Late Events

If your sink is Delta Lake, late events can be merged in after the fact:

```python
from delta.tables import DeltaTable

late_events = spark.read.parquet("s3://late-arrivals")

DeltaTable.forPath(spark, "s3://aggregated-clicks").alias("target").merge(
    late_events.alias("source"),
    "target.window_start = source.window_start AND target.user_id = source.user_id"
).whenMatchedUpdate(set={"count": "target.count + source.count"}) \
 .whenNotMatchedInsertAll() \
 .execute()
```

---

## Trade-offs

| Approach | Latency | Correctness | Complexity |
|---|---|---|---|
| Ignore late data | Lowest | Incorrect | Lowest |
| Watermark (drop after threshold) | Low | Good (within threshold) | Medium |
| Reprocessing batch | Higher | Correct | High |
| Delta MERGE on late events | Medium | Correct | Medium |

---

## How to Say It in the Interview
> "Late data is a fundamental challenge in streaming. The simplest approach is watermarks — you define a tolerance window, say 30 minutes, and Spark tracks the max event time seen. Any event arriving more than 30 minutes behind is discarded; within that threshold, events are included in the right window. For stricter correctness, I'd use a dual-layer approach: the streaming job produces near-real-time results with the watermark tolerance, and a batch job re-aggregates the last few hours every hour using Delta MERGE to correct any late arrivals. Which approach you choose depends on your SLA — how wrong is acceptable and for how long."

---

## Follow-ups & Answers

**"What's the difference between event time and processing time?"**
> Event time = when it happened (in the original system). Processing time = when the pipeline sees it. For late data handling, always use event time — otherwise your window boundaries are meaningless.

**"How does Kafka help with late data?"**
> Kafka retains messages for a configurable period (default 7 days). This means a batch job can always re-read the last N hours of events from Kafka to reprocess late arrivals — without needing a separate late-data store.

---

## Common Mistakes
- Using processing time instead of event time for windowing
- Setting watermark too tight — drops valid late events
- Setting watermark too loose — keeps state in memory too long, causing OOM
- Not testing with simulated late data before production

---

## Key Concepts Tested
- Event time vs processing time
- Watermarks and window finalization
- Spark Structured Streaming watermark API
- Lambda/Kappa architecture for correctness
- Delta Lake MERGE for late event correction
