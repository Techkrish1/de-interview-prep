# Day 01 — Data Engineering Interview Prep
**Date:** 2026-09-23
**Topics:** ETL vs ELT · SQL Window Functions · Real-time Streaming Architecture

---

## Q1 — Theoretical: ETL vs ELT

### Key Decision Framework

| | ETL | ELT |
|---|---|---|
| Flow | Extract → Transform → Load | Extract → Load → Transform |
| Transform location | Pipeline server / middleware | Inside the data warehouse |
| Best for | PII masking, compliance, RDBMS targets | Cloud DWH (Snowflake, BigQuery, Redshift) |
| Latency | Higher | Lower (raw data lands fast) |
| Reprocessability | Limited | Full — raw layer always available |
| Modern default | Legacy / compliance-heavy | ✅ Cloud-native architectures |

### When to Use Which
- **ETL** → data must be cleaned/masked *before* entering the warehouse (HIPAA, PCI-DSS, GDPR)
- **ELT** → cloud DWH with elastic compute; need to replay/reprocess historical data; dbt-driven transforms

### Where dbt Fits
> dbt is the **T in ELT** — runs SQL transforms *inside* the warehouse. Adds version control, testing (schema + data tests), lineage, and documentation. Does not move data.

### Interview One-Liner
> *"ETL protects the warehouse from dirty/sensitive data; ELT trusts the warehouse to handle transformation at scale."*

---

## Q2 — Coding: SQL Window Functions

### Problem
> Find each user's **2nd most recent transaction** and the **running total of spend** up to that point.

### Solution

```sql
WITH ranked AS (
    SELECT
        user_id,
        txn_id,
        amount,
        txn_date,
        ROW_NUMBER() OVER (
            PARTITION BY user_id
            ORDER BY txn_date DESC, txn_id DESC   -- tiebreaker on txn_id
        ) AS rn,
        SUM(amount) OVER (
            PARTITION BY user_id
            ORDER BY txn_date ASC, txn_id ASC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS running_total
    FROM transactions
)
SELECT user_id, txn_id, amount, txn_date, running_total
FROM ranked
WHERE rn = 2;
```

### Window Function Cheat Sheet

| Function | Use Case | Tie Behavior |
|---|---|---|
| `ROW_NUMBER()` | Unique rank — use for filtering | No ties (always unique) |
| `RANK()` | Rank with gaps on ties | Skips numbers |
| `DENSE_RANK()` | Rank without gaps | No skips |
| `SUM/AVG OVER` | Running aggregates | Depends on frame |

### ROWS vs RANGE
```sql
-- ROWS: physical row count (SAFE for running totals)
ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW

-- RANGE: logical — rows with same ORDER BY value treated as a group (RISKY for running totals with ties)
RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
```
> **Rule:** Always use `ROWS` for running totals. Use `RANGE` only when you intentionally want tied rows to share the same aggregate value.

### PySpark Equivalent
```python
from pyspark.sql import Window
import pyspark.sql.functions as F

w_rank = Window.partitionBy("user_id").orderBy(F.desc("txn_date"), F.desc("txn_id"))
w_sum  = Window.partitionBy("user_id") \
               .orderBy("txn_date", "txn_id") \
               .rowsBetween(Window.unboundedPreceding, Window.currentRow)

result = (
    df.withColumn("rn", F.row_number().over(w_rank))
      .withColumn("running_total", F.sum("amount").over(w_sum))
      .filter(F.col("rn") == 2)
)
```

---

## Q3 — Real-time Scenario: Clickstream Pipeline (50K events/sec)

### Requirements
- **Speed layer:** Live dashboard with < 5s latency
- **Batch layer:** Daily reports, historical accuracy

### Architecture (Lambda Pattern)

```
Browser / Mobile App
        │
        ▼
  ┌─────────────┐
  │    Kafka     │  ← 30+ partitions, Schema Registry (Avro)
  │ partitioned  │
  │  by user_id  │
  └──────┬───────┘
         │
    ┌────┴─────┐
    │          │
    ▼          ▼
┌────────┐  ┌──────────────────────┐
│ Flink  │  │  S3 / GCS Raw Layer  │
│Streaming│  │  Parquet, partitioned│
│(exactly │  │  by date/hour        │
│  once)  │  └──────────┬───────────┘
└────┬───┘             │
     │                 ▼
     ▼          ┌─────────────┐
┌──────────┐    │ Spark Batch │
│  Redis / │    │  + dbt      │
│ClickHouse│    └──────┬──────┘
└────┬─────┘           │
     │                 ▼
     ▼          ┌──────────────┐
┌──────────┐    │  Snowflake / │
│   Live   │    │  BigQuery    │
│Dashboard │    │  (Reports)   │
└──────────┘    └──────────────┘
```

### Component Decisions

| Layer | Tech | Why |
|---|---|---|
| Ingestion | Kafka | 50K/s throughput, durable log, consumer groups |
| Stream processing | Apache Flink | Sub-second latency, exactly-once, stateful ops |
| Live serving | Redis / ClickHouse | < 5s queries; columnar OLAP for ClickHouse |
| Raw storage | S3 Parquet (date/hour partitioned) | Cheap, replayable, batch-ready |
| Batch | Spark + dbt | Complex business logic, historical aggregations |
| DWH | Snowflake / BigQuery | Analyst-facing, governed reports |

### Must-Mention Points in Interview

1. **Exactly-once semantics** — Flink checkpoints + idempotent sink writes (conditional Redis SET / upsert)
2. **Schema evolution** — Kafka Schema Registry (Avro/Protobuf); producers/consumers decouple
3. **Late data handling** — Flink watermarks + allowed lateness window (e.g., 2 min); side output for very late events
4. **Batch = source of truth** — streaming gives approximate real-time; EOD reconciliation job overwrites with authoritative batch numbers
5. **Kafka durability** — if Kafka is down, consumers resume from last committed offset; no data loss
6. **Monitoring** — consumer lag is the key metric; alert when lag exceeds threshold

### Flink Late Data Pattern
```
Event time window: 10:00–10:01
Watermark: event_time - 2 minutes
Allowed lateness: 2 minutes after watermark passes window end

→ Events up to 2 min late: update the window result
→ Events > 2 min late: route to side output → batch correction
```

---

## Quick Revision

| Concept | One-Line Rule |
|---|---|
| ETL vs ELT | Compliance/RDBMS → ETL; Cloud DWH + reprocessability → ELT |
| dbt role | T in ELT — SQL transforms inside DWH, with testing and lineage |
| ROW_NUMBER vs RANK | ROW_NUMBER for filters (no ties); RANK/DENSE_RANK for leaderboards |
| ROWS vs RANGE frames | Always ROWS for running totals |
| Kafka guarantee | Durable log → consumers always catch up from last offset |
| Exactly-once | Flink checkpoints + idempotent sink writes |
| Late data | Watermarks → allowed lateness → side output |
| Batch vs Stream truth | Stream = approximate real-time; Batch = source of truth |
| Lambda architecture | Speed layer (Kafka+Flink) + Batch layer (Spark) + Serving layer |

---

## Common Interview Pitfalls — Day 01

- Saying ELT is always better (wrong for HIPAA/PCI data)
- Using `RANK()` when filtering for Nth row (use `ROW_NUMBER()`)
- Forgetting `ROWS BETWEEN` frame — default `RANGE` can give wrong running totals on ties
- Building streaming-only pipeline and forgetting historical/batch requirement
- Not mentioning schema evolution (Schema Registry) in any streaming design
- Not mentioning monitoring (consumer lag) in any Kafka-based design
