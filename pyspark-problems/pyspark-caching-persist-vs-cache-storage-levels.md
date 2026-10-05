# PySpark Caching — When to Use cache vs persist and Storage Levels

**Type:** PySpark Problem
**Topic:** Caching, Persistence, Performance Optimization

---

## The Question
> "Explain caching in PySpark. When would you cache a DataFrame and what is the difference between cache() and persist()?"

---

## Why Caching Matters

Without caching, every action re-executes the full DAG from scratch:

```python
df = spark.read.parquet("s3://huge-dataset")   # read from S3
filtered = df.filter(df.amount > 100)
joined   = filtered.join(dim_df, "customer_id")

joined.count()      # reads S3, filters, joins — full DAG
joined.show()       # reads S3, filters, joins — full DAG AGAIN
joined.write.parquet("s3://output")  # reads S3, filters, joins — AGAIN
```

S3 read + filter + join executed 3 times. Cache it once:

```python
joined.cache()          # marks for caching
joined.count()          # first action: computes + caches in memory
joined.show()           # reads from cache — no S3, no recompute
joined.write.parquet("s3://output")  # reads from cache
joined.unpersist()      # free memory when done
```

---

## cache() vs persist()

```python
df.cache()
# equivalent to:
df.persist(StorageLevel.MEMORY_AND_DISK)
```

`cache()` = shortcut with a fixed storage level.
`persist()` = lets you choose the storage level.

---

## Storage Levels

```python
from pyspark import StorageLevel

df.persist(StorageLevel.MEMORY_ONLY)         # RAM only — evicted if not enough memory
df.persist(StorageLevel.MEMORY_AND_DISK)     # RAM first, spill to disk if needed (default)
df.persist(StorageLevel.DISK_ONLY)           # Disk only — slowest but uses no RAM
df.persist(StorageLevel.MEMORY_AND_DISK_2)  # Replicated on 2 nodes for fault tolerance
df.persist(StorageLevel.OFF_HEAP)            # Tungsten off-heap memory (avoids GC pressure)
```

| Level | Speed | Memory Use | Fault Tolerant |
|---|---|---|---|
| MEMORY_ONLY | Fastest | Highest | No |
| MEMORY_AND_DISK | Fast (fallback to disk) | Medium | No |
| DISK_ONLY | Slow | Lowest | Yes (can reread) |
| _2 variants | Fast | 2× | Yes (replica) |

**Rule of thumb:** Use `MEMORY_AND_DISK` (the default). Use `MEMORY_ONLY` only if your DataFrame fits comfortably in RAM and you need maximum speed. Use `DISK_ONLY` for very large DataFrames accessed infrequently.

---

## When to Cache

**Good candidates:**
- DataFrame used in multiple actions or branches of computation
- Iterative algorithms (ML training loops) — re-use the same training data
- After an expensive join/aggregation that feeds multiple downstream queries

```python
# Good: feature_df used for train and test evaluation
feature_df = raw.join(lookup, "id").groupBy("user_id").agg(...)
feature_df.cache()

train = feature_df.filter(feature_df.split == "train")
test  = feature_df.filter(feature_df.split == "test")
model.fit(train)
model.transform(test).show()
feature_df.unpersist()
```

**Bad candidates:**
- DataFrame used only once — caching overhead with no benefit
- Very large DataFrame that exceeds executor memory — causes spills and OOM
- Streaming DataFrames — caching doesn't apply the same way

---

## Checkpoint vs Cache

```python
df.cache()       # stores in memory/disk on executors — recomputed on failure
df.checkpoint()  # writes to HDFS/S3 — breaks DAG lineage, safe on long chains
```

Checkpoint is for very deep DAGs (long ML pipelines) where re-computing from scratch on failure is too expensive. Cache is for reuse within a job.

---

## How to Say It in the Interview
> "cache() and persist() both store a DataFrame so it's not recomputed on every action. cache() is a shortcut for MEMORY_AND_DISK. persist() lets you pick a storage level — MEMORY_ONLY for max speed when data fits in RAM, DISK_ONLY when it doesn't, or the _2 variants for fault tolerance via replication. You should cache when a DataFrame is reused across multiple actions or in iterative algorithms. Always call unpersist() when you're done — Spark doesn't automatically free cached DataFrames until the application ends or memory pressure forces eviction."

---

## Follow-ups & Answers

**"What happens if cached data is evicted from memory?"**
> Spark recomputes it from the original DAG. For MEMORY_AND_DISK, it spills to disk instead of evicting — so recomputation only happens with MEMORY_ONLY when RAM is insufficient.

**"What's the difference between cache and checkpoint?"**
> Cache stores data on executors (in memory/disk) and keeps the DAG lineage — if an executor fails, Spark recomputes from source. Checkpoint writes to stable storage (HDFS/S3) and truncates the DAG — used for long iterative jobs where recomputing from scratch is too costly.

---

## Common Mistakes
- Caching a DataFrame used only once
- Forgetting to `unpersist()` — memory leak across jobs
- Caching before filtering — cache the smaller filtered dataset, not the raw one
- Assuming cache guarantees data is in memory — MEMORY_ONLY can evict under pressure

---

## Key Concepts Tested
- Lazy evaluation and why caching helps
- cache() vs persist() — storage levels
- When caching improves performance vs wastes memory
- unpersist() and memory management
- Cache vs checkpoint
