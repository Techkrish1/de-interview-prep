# What are ACID Properties and How Does Delta Lake Implement Them?

**Type:** Theoretical
**Topic:** ACID, Delta Lake, Data Reliability

---

## The Question
> "What are ACID properties? Does a data lake have them? How does Delta Lake solve this?"

---

## ACID Defined

| Property | Meaning | Example |
|---|---|---|
| **A**tomicity | All or nothing — no partial writes | Insert 1000 rows: all land or none do |
| **C**onsistency | Schema and constraints respected | Writing string to integer column fails |
| **I**solation | Concurrent writes don't corrupt each other | Two writers don't corrupt the same partition |
| **D**urability | Committed data survives crashes | Row persists even if server restarts after commit |

---

## Why Plain Data Lakes (S3 + Parquet) Don't Have ACID

```
Writer 1: uploading 10 parquet files to s3://orders/date=2024-01-01/
Writer 2: simultaneously writing to same partition

Reader: sees 7 files from Writer 1 + 3 from Writer 2 → inconsistent state
```

Problems:
- No atomicity — crash leaves partial data
- No isolation — two writers corrupt the same partition
- No upserts — Parquet files are immutable
- No schema enforcement — any schema can be written at any time

---

## How Delta Lake Solves This — Transaction Log

Delta Lake adds `_delta_log/` to every table. Every change is recorded as a JSON entry atomically before data files are written.

```
s3://orders/
├── _delta_log/
│   ├── 00000000000000000001.json  ← "added: part-001.parquet"
│   ├── 00000000000000000002.json  ← "removed: part-001.parquet (updated)"
│   └── 00000000000000000003.json  ← "schema changed: added column 'discount'"
├── part-001.parquet
└── part-002.parquet
```

| ACID Property | Delta Lake Mechanism |
|---|---|
| Atomicity | All file changes written to `_delta_log` in one atomic entry |
| Consistency | Schema enforcement rejects writes that don't match |
| Isolation | Optimistic concurrency — detects conflicting writes |
| Durability | S3 durability + `_delta_log` is source of truth |

---

## Key Delta Lake Features

```python
from delta.tables import DeltaTable

# UPSERT — impossible with plain Parquet
DeltaTable.forName(spark, "orders").alias("t").merge(
    new_data.alias("s"), "t.order_id = s.order_id"
).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()

# TIME TRAVEL
spark.read.format("delta").option("versionAsOf", 5).load("s3://orders/")
spark.read.format("delta").option("timestampAsOf", "2024-01-15").load("s3://orders/")
```

---

## Delta Lake vs Iceberg vs Hudi

| | Delta Lake | Apache Iceberg | Apache Hudi |
|---|---|---|---|
| Origin | Databricks | Netflix | Uber |
| Best for | Spark/Databricks | Multi-engine (Flink, Trino) | Streaming upserts (CDC) |

---

## How to Say It in the Interview
> "ACID stands for Atomicity, Consistency, Isolation, Durability. Plain S3 with Parquet has none of these — two concurrent writers can corrupt partitions and there's no way to update a row. Delta Lake adds a transaction log: a `_delta_log/` folder where every change is recorded atomically before data files are touched. This enables MERGE for upserts, time travel to query past versions, and schema enforcement. It brings database reliability to the data lake."

---

## Follow-ups & Answers

**"What is time travel in Delta Lake?"**
> Query any historical version — useful for auditing, recovering from accidental deletes. Each write increments the version; query by version number or timestamp.

**"What is VACUUM?"**
> Removes old data files no longer referenced by the log (older than retention period, default 7 days). After VACUUM, time travel older than retention is no longer possible.

---

## Common Mistakes
- Confusing Delta Lake (table format) with Databricks (company)
- Saying data lakes are ACID — they are not without a table format layer
- Not knowing the `_delta_log/` is the key mechanism

---

## Key Concepts Tested
- ACID properties definition
- Why S3 + Parquet lacks ACID
- Delta Lake transaction log
- MERGE, time travel, schema enforcement
- Delta Lake vs Iceberg vs Hudi
