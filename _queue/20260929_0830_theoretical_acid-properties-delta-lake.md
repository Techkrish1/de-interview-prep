---
publish_at: "2026-09-29T03:00:00Z"
folder: theoretical
filename: acid-properties-and-delta-lake.md
title: What are ACID properties and how does Delta Lake implement them?
---

# What are ACID Properties and How Does Delta Lake Implement Them?

**Type:** Theoretical
**Topic:** ACID, Delta Lake, Data Reliability

---

## The Question
> "What are ACID properties? Does a data lake have them? How does Delta Lake solve this?"

---

## ACID — What Each Property Means

| Property | Meaning | Example |
|---|---|---|
| **A**tomicity | All operations in a transaction succeed or all fail — no partial writes | Insert 1000 rows: either all 1000 land or none do |
| **C**onsistency | Data moves from one valid state to another — schema and constraints respected | Writing a string to an integer column fails, table stays unchanged |
| **I**solation | Concurrent transactions don't interfere with each other | Two writers don't corrupt the same partition |
| **D**urability | Committed data survives crashes and failures | Committed row persists even if server restarts immediately after |

---

## Why Plain Data Lakes (S3 + Parquet) Don't Have ACID

```
Writer 1: uploading 10 parquet files to s3://orders/date=2024-01-01/
Writer 2: simultaneously writing a different batch to same partition

Reader: reads at the wrong moment — sees 7 files from Writer 1 + 3 from Writer 2
→ Inconsistent, partially-written state
```

Problems with plain S3 + Parquet:
- **No atomicity** — file uploads are not transactional; a crash leaves partial data
- **No isolation** — two writers corrupt the same partition
- **No upserts** — Parquet files are immutable; you can't update a row
- **No schema enforcement** — any schema can be written at any time

---

## How Delta Lake Solves This — The Transaction Log

Delta Lake adds a `_delta_log/` folder to every table. Every change is recorded as a JSON entry in this log before data files are written.

```
s3://orders/
├── _delta_log/
│   ├── 00000000000000000001.json   ← "added files: part-001.parquet, part-002.parquet"
│   ├── 00000000000000000002.json   ← "removed files: part-001.parquet (overwritten)"
│   └── 00000000000000000003.json   ← "schema changed: added column 'discount'"
├── part-001.parquet
├── part-002.parquet
└── part-003.parquet
```

**How each ACID property is achieved:**

| Property | Delta Lake mechanism |
|---|---|
| Atomicity | All file additions/removals written to `_delta_log` in one atomic JSON entry |
| Consistency | Schema enforcement — Delta rejects writes that don't match the table schema |
| Isolation | Optimistic concurrency control — detects conflicting writes, retries or rejects |
| Durability | S3/ADLS/GCS durability + `_delta_log` is the source of truth |

---

## Key Delta Lake Features Built on ACID

```python
from delta.tables import DeltaTable

# UPSERT — not possible with plain Parquet
DeltaTable.forName(spark, "orders").alias("t").merge(
    new_data.alias("s"), "t.order_id = s.order_id"
).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()

# TIME TRAVEL — query historical versions
spark.read.format("delta").option("versionAsOf", 5).load("s3://orders/")
spark.read.format("delta").option("timestampAsOf", "2024-01-15").load("s3://orders/")

# SCHEMA ENFORCEMENT — rejects bad writes automatically
# SCHEMA EVOLUTION — opt-in with mergeSchema option
spark.write.format("delta").option("mergeSchema", "true").save("s3://orders/")
```

---

## Delta Lake vs Apache Iceberg vs Apache Hudi

| | Delta Lake | Apache Iceberg | Apache Hudi |
|---|---|---|---|
| Originated at | Databricks | Netflix | Uber |
| ACID | Yes | Yes | Yes |
| Time travel | Yes | Yes | Yes |
| Best for | Spark/Databricks ecosystem | Multi-engine (Spark, Flink, Trino) | Streaming upserts (CDC) |
| Format | Parquet + `_delta_log/` JSON | Parquet/ORC + metadata files | Parquet + HFile index |

---

## How to Say It in the Interview
> "ACID stands for Atomicity, Consistency, Isolation, Durability — the four properties that make database transactions reliable. Plain data lakes on S3 with Parquet don't have ACID: two concurrent writers can corrupt the same partition, crashes leave partial data, and there's no way to update a row. Delta Lake adds a transaction log — a `_delta_log/` folder where every change is recorded atomically before data files are touched. This enables upserts via MERGE, time travel to query past versions, schema enforcement, and safe concurrent writes. It essentially brings database reliability to the data lake."

---

## Follow-ups & Answers

**"What is time travel and why is it useful?"**
> Query any historical version of a Delta table — useful for auditing, recovering from accidental deletes, and A/B testing against historical data. Each write increments the version; you can query by version number or timestamp.

**"How does Delta Lake handle concurrent writes?"**
> Optimistic concurrency control: each writer reads the current version, makes changes, then tries to commit. If another writer committed in the meantime, Delta detects the conflict and either retries (if changes don't overlap) or raises an error (if they conflict on the same rows/partitions).

**"What is VACUUM in Delta Lake?"**
> Removes old data files no longer referenced by the transaction log (older than the retention period, default 7 days). Reclaims S3 storage. Warning: after VACUUM, time travel older than the retention period is no longer possible.

---

## Common Mistakes
- Confusing Delta Lake (open-source table format) with Databricks (the company)
- Saying data lakes are ACID — they are not without a table format layer
- Not knowing the `_delta_log/` is the key mechanism
- Not mentioning Iceberg/Hudi as alternatives — shows broader awareness

---

## Key Concepts Tested
- ACID properties definition and examples
- Why plain S3 + Parquet lacks ACID
- Delta Lake transaction log mechanism
- MERGE, time travel, schema enforcement
- Delta Lake vs Iceberg vs Hudi
