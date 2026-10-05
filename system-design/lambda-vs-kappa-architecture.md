# Lambda vs Kappa Architecture

**Type:** System Design
**Topic:** Batch vs Streaming, Architecture Patterns, Lambda, Kappa

---

## The Question
> "What is the Lambda architecture? What problem does it solve and when would you use Kappa instead?"

---

## The Problem Both Solve

Two conflicting requirements:
- **Low latency**: dashboards need data within seconds
- **High accuracy**: batch jobs must reprocess history to correct late arrivals and bad data

Lambda solves this by running both in parallel.

---

## Lambda Architecture

```
         Data Source (Kafka / S3)
                    │
       ┌────────────┴────────────┐
       │                         │
  Speed Layer (Stream)      Batch Layer
  Kafka → Spark Streaming   Spark Batch job
  Low latency (~seconds)    High accuracy (~hours)
  Approximate results       Exact, full history
       │                         │
       └────────────┬────────────┘
                    │
             Serving Layer
        (merges batch + speed results)
```

**Serving layer logic:**
```
result = batch_result  (authoritative, covers history up to N hours ago)
       + speed_result  (fills gap from N hours ago to now)
```

### Example — real-time sales dashboard
- **Speed layer**: Kafka → Spark Streaming → Redis. Revenue for last 15 min, approximate, seconds of latency.
- **Batch layer**: Spark batch hourly → recomputes last 24h from full history → Delta Lake. Exact, handles late arrivals.
- **Serving**: dashboard shows batch result for older windows + speed result for the current window.

### Lambda Trade-offs

**Pros:** Real-time approximate results + accurate historical recomputation. Batch layer corrects speed layer errors over time.

**Cons:** **Two codebases** — same business logic implemented in streaming AND batch. They drift. A logic change must be made in both. High operational complexity.

---

## Kappa Architecture

Eliminate the batch layer. One streaming pipeline handles everything. Kafka's long retention enables reprocessing by replaying from offset 0.

```
Data Source (Kafka, long retention)
         │
  Single Stream Processor
  (Spark Structured Streaming / Flink)
         │
    Serving Layer
```

**Reprocessing flow:**
```
1. Deploy corrected streaming job (v2)
2. v2 replays Kafka from offset 0
3. v2 writes to new output table
4. Swap serving layer to v2 output
5. Decommission v1
```

**Pros:** Single codebase — logic defined once for both real-time and history. Simpler operations.

**Cons:** Reprocessing large history is slow. Kafka long retention is expensive. Multi-pass aggregations are harder in streaming.

---

## When to Choose Which

| Situation | Choose |
|---|---|
| Need sub-second latency AND exact historical accuracy | Lambda |
| Complex batch aggregations (multi-pass, ML training) | Lambda |
| Kafka retention sufficient, logic is streamable | Kappa |
| Want single codebase, simpler ops | Kappa |
| Strong streaming expertise in the team | Kappa |

---

## Modern Practical Approach

Most teams converge on a middle ground using Delta Lake:

```
Kafka → Spark Structured Streaming → Delta Lake
                                          │
                               Ad-hoc MERGE job for corrections
                               (runs when late data arrives)
```

Not pure Lambda (no permanent dual pipeline), not pure Kappa (uses MERGE for corrections). Delta's transaction log gives audit history; MERGE handles late data without full replay.

---

## How to Say It in the Interview
> "Lambda splits processing into a speed layer for low-latency approximate results and a batch layer for accurate historical computation, merging them at a serving layer. The cost is maintaining two codebases with the same logic — they drift over time. Kappa eliminates the batch layer and handles everything in one streaming pipeline, using Kafka replay for reprocessing. The trade-off is Kafka retention cost and slower reprocessing at scale. In practice, most modern teams use something in between — streaming writes to Delta Lake and a MERGE job handles corrections, rather than running permanent parallel pipelines."

---

## Follow-ups & Answers

**"What is the serving layer?"**
> The queryable store end users hit. In Lambda it merges batch + speed results. Implemented as Redis/Cassandra for low-latency lookups, or Delta/Athena for analytical queries. Must support efficient merging of two result sets.

**"Flink vs Spark Streaming for Kappa?"**
> Flink is streaming-first — better exactly-once semantics, lower latency, stronger stateful aggregation support. Spark Streaming is easier to adopt for teams already on Spark. Kappa with Flink is common in high-throughput, latency-sensitive pipelines.

**"How does Delta Lake change this?"**
> Delta's MERGE + time-travel blur the Lambda/Kappa line. A single streaming job writes to Delta; a correction job MERGEs late data into the same table. Databricks' Medallion Architecture builds on this pattern.

---

## Common Mistakes
- Describing Lambda as just "batch + stream" without the serving layer merge
- Not knowing the main Lambda pain: dual codebase maintenance
- Not knowing Kappa uses Kafka replay as its reprocessing mechanism
- Not having a view on when to choose which

---

## Key Concepts Tested
- Lambda: speed + batch + serving layer
- Main Lambda pain: dual codebase drift
- Kappa: single stream pipeline + Kafka replay
- Modern alternative: Delta Lake MERGE
- Decision criteria: latency requirements, reprocessing needs, team expertise
