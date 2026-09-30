# Partitioning Strategies — Hash, Range, and List Partitioning

**Type:** Theoretical
**Topic:** Partitioning, Query Performance, Spark, Data Warehouse

---

## The Question
> "Explain partitioning strategies in data engineering — hash, range, and list partitioning. How does partitioning affect query performance and how does it differ between a data warehouse and Spark?"

---

## Why Partition?

Without partitioning, every query scans the entire dataset. Partitioning physically organizes data so queries only read the slices they need — called **partition pruning**.

```
Without partitioning:
  SELECT * FROM orders WHERE country = 'IN' → Full scan: 500GB

With partitioning on country:
  → Reads only the 'IN' partition: 12GB
```

---

## The Three Strategies

### 1. Range Partitioning
Contiguous ranges of a column's values. Most common on dates.

```
s3://warehouse/orders/order_date=2026-09-28/
s3://warehouse/orders/order_date=2026-09-29/
s3://warehouse/orders/order_date=2026-09-30/
```

```python
df.write.partitionBy("order_date").parquet("s3://warehouse/orders")
```

**Best for:** Time-series, append-heavy tables, date-range queries
**Risk:** Skew — some partitions far larger than others (Black Friday)

### 2. Hash Partitioning
Hash function on a key column distributes rows evenly across N buckets.

```python
df.repartition(200, "customer_id")
# customer_id=1001 → hash(1001) % 200 = bucket 47 (always)
```

**Best for:** Even distribution, join optimization (pre-partition on join key avoids shuffle)
**Risk:** No range filtering — `WHERE customer_id > 5000` still scans all buckets

### 3. List Partitioning
Explicit mapping of values to partitions.

```sql
PARTITION BY LIST (country) (
    PARTITION p_asia   VALUES IN ('IN', 'CN', 'JP', 'SG'),
    PARTITION p_europe VALUES IN ('DE', 'FR', 'GB', 'NL'),
    PARTITION p_us     VALUES IN ('US', 'CA')
);
```

**Best for:** Low-cardinality categoricals with known values (country, status)
**Risk:** New values not in the list fail unless a catch-all partition exists

---

## Partition Pruning

Query engine reads partition metadata first, identifies matching partitions, skips all others.

```sql
-- Pruning WORKS:
WHERE order_date = '2026-09-30'
WHERE order_date >= '2026-01-01' AND order_date < '2027-01-01'

-- Pruning FAILS (function wraps the partition column):
WHERE YEAR(order_date) = 2026   -- engine evaluates per row, can't prune
```

---

## Multi-level Partitioning

```python
df.write.partitionBy("year", "month", "day").parquet("s3://warehouse/events")
# Layout: events/year=2026/month=09/day=30/
```

Finer pruning, but: 3yr × 12mo × 31d × 24hr = 26,784+ partitions → **small files problem**.

---

## The Small Files Problem

Over-partitioning creates millions of tiny files:
- S3/HDFS metadata overhead per file
- Spark: one task per file → thousands of near-empty tasks → scheduler bottleneck

```
Bad:  partitionBy("date", "user_id") → millions of partitions
Good: partitionBy("date") → ~1,000 partitions; use Z-ORDER for user_id
```

**Fix — Delta Lake compaction:**
```python
spark.sql("OPTIMIZE orders ZORDER BY (customer_id)")
```

Z-ordering co-locates data for high-cardinality columns within files without creating separate directories.

---

## DW vs Spark Partitioning

| | Snowflake / BigQuery / Redshift | Spark / Delta Lake |
|---|---|---|
| Defined at | Table DDL | Write time (`partitionBy`) |
| Stored as | Internal micro-partitions | Physical directories on S3/HDFS |
| Pruning | Automatic | Automatic when filter matches partition col |
| Small file risk | Managed internally | Your responsibility |
| High-cardinality | Clustering keys | Z-ordering |

Snowflake auto-divides tables into 50–500MB micro-partitions and tracks min/max per column — no manual partitioning needed. Define a **clustering key** to improve pruning for your most frequent access pattern.

---

## How to Say It in the Interview
> "Partitioning physically organizes data for partition pruning — queries read only the relevant slices. Range on date is the most common pattern for time-series data. Hash distributes evenly by key — useful for joins since co-partitioned tables avoid shuffle. List works for low-cardinality categoricals.
>
> The main risk is over-partitioning — too many small files hurt more than they help due to metadata overhead and task scheduling cost. Rule of thumb: partition on columns queries filter on, keep each partition at hundreds of MBs minimum, and use Z-ordering for high-cardinality columns you can't partition on."

---

## Follow-ups & Answers

**"How does Snowflake handle partitioning?"**
> Automatic micro-partitioning into 50–500MB compressed chunks with min/max metadata per column per partition. Queries prune automatically. You optionally define a clustering key to control physical ordering for your most common filters.

**"What is Z-ordering?"**
> Delta Lake feature — reorganizes data within files to co-locate rows with similar values for specified columns. Unlike partitioning (separate directories), Z-ordering improves pruning for high-cardinality columns like `customer_id` without the small files problem.

**"How do you choose what to partition on?"**
> Filter frequency (appears in WHERE most often), low cardinality (date/country, not user_id), and write pattern (append-by-date maps naturally to date partitioning).

---

## Common Mistakes
- Partitioning on high-cardinality columns (user_id) → millions of tiny files
- Wrapping partition column in a function → defeats pruning
- Confusing `repartition()` (in-memory Spark partitions) with `partitionBy()` (storage directories)
- Saying "more partitions = better" without knowing the small files problem

---

## Key Concepts Tested
- Range, hash, list — when to use each
- Partition pruning and what breaks it
- Small files problem and fixes
- Snowflake micro-partitioning vs Spark partitionBy
- Z-ordering for high-cardinality columns
