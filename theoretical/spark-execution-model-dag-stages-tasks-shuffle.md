# Spark Execution Model — DAG, Stages, Tasks, and Shuffle

**Type:** Theoretical
**Topic:** Apache Spark, Internals, Performance

---

## The Question
> "Walk me through how Spark executes a job — from the code you write to physical execution. What are a DAG, stages, tasks, and shuffles?"

---

## Execution Flow

```
Your code (transformations)
         ↓
     Logical Plan
    (DAG of operations)
         ↓
  Catalyst Optimizer
  (predicate pushdown, column pruning, constant folding)
         ↓
     Physical Plan
         ↓
  Split into Stages at shuffle boundaries
         ↓
  Tasks dispatched to executors (one per partition per stage)
```

---

## DAG — Lazy Evaluation

Transformations build a DAG. Nothing runs until an **action** fires.

```python
df  = spark.read.parquet("s3://orders")          # no execution
f   = df.filter(df.amount > 100)                 # no execution
g   = f.groupBy("category").sum("amount")        # no execution
g.write.parquet("s3://output")                   # ← ACTION — DAG runs now
```

**Transformations** (lazy): `filter`, `select`, `groupBy`, `join`, `map`
**Actions** (trigger execution): `count()`, `collect()`, `write()`, `show()`

---

## Stages — Split at Shuffle Boundaries

The DAG is cut into stages at **wide transformations** — operations that require data to move between partitions.

```
Stage 1:  read → filter → select
          (narrow — data stays in its partition)
          ─────────── SHUFFLE BOUNDARY ─────────
          groupBy needs all "electronics" rows together
          ──────────────────────────────────────
Stage 2:  groupBy → sum → write
```

**Narrow** (no shuffle): `filter`, `map`, `select`, `union`, `coalesce`
**Wide** (triggers shuffle): `groupBy`, `join`, `distinct`, `repartition`, `orderBy`

---

## Tasks — Unit of Parallelism

Each stage = one task per partition, dispatched to executor cores in parallel.

```
Stage 1, 200 partitions → 200 tasks
  Task 0   → Executor 1, Core 1  (Partition 0)
  Task 1   → Executor 1, Core 2  (Partition 1)
  ...
  Task 199 → Executor N, Core M  (Partition 199)
```

More partitions = more parallelism, but also more task scheduling overhead. Default post-shuffle: 200 (`spark.sql.shuffle.partitions`).

---

## Shuffle — The Expensive Part

Shuffle = disk write + network transfer + disk read.

```
Before shuffle (spread across partitions):
  P0: [electronics $200], [books $15]
  P1: [electronics $350], [electronics $80]

After shuffle (regrouped by category):
  P0: [electronics $200], [electronics $350], [electronics $80]
  P1: [books $15]
```

If one category dominates (data skew), one task handles it all while others finish instantly — the core of why skew kills Spark jobs. Fix: salting or AQE skew hints.

---

## Minimizing Shuffles

| Technique | Effect |
|---|---|
| Broadcast join | Sends small table to all executors — no join shuffle |
| Pre-partition on join key | `repartition("customer_id")` before multiple joins |
| `reduceByKey` vs `groupByKey` | Combines locally before shuffle — less data moved |
| `coalesce` vs `repartition` | Reduces partition count without full shuffle |
| AQE (`spark.sql.adaptive.enabled=true`) | Auto-coalesces small partitions, auto-broadcasts, handles skew |

---

## How to Say It in the Interview
> "Transformations build a DAG lazily — nothing runs until an action fires. Spark's Catalyst optimizer compiles that DAG into a physical plan, then splits it into stages at shuffle boundaries — where data must move between partitions. Each stage runs as tasks, one per partition, across executor cores in parallel. Shuffles are expensive: disk write, network transfer, disk read. So Spark performance tuning is fundamentally about minimizing shuffles — broadcast joins for small tables, pre-partitioning on join keys, and AQE in Spark 3 which handles a lot automatically."

---

## Follow-ups & Answers

**"What is Catalyst?"**
> Spark's query optimizer — applies predicate pushdown, column pruning, and constant folding automatically to produce an efficient physical plan.

**"What is AQE?"**
> Adaptive Query Execution (Spark 3+). Dynamically adjusts the plan mid-execution: coalesces small shuffle partitions, auto-broadcasts small joins, splits skewed partitions. Enable with `spark.sql.adaptive.enabled=true`.

**"repartition vs coalesce?"**
> `repartition(N)` — full shuffle, can increase or decrease, evenly distributes. `coalesce(N)` — no shuffle, can only decrease, merges local partitions. Use coalesce when shrinking after a filter.

**"Why not use thousands of partitions?"**
> Task scheduling overhead per task (launch, serialize, manage results) exceeds compute time for tiny partitions. AQE auto-coalesces small post-shuffle partitions to avoid this.

---

## Common Mistakes
- Saying a transformation "executes" — only actions do
- Not explaining *why* shuffle is slow (disk + network)
- Saying `filter` causes a shuffle — it doesn't (narrow transformation)
- Ignoring task scheduling overhead when advocating for more partitions

---

## Key Concepts Tested
- Lazy evaluation — DAG, actions vs transformations
- Stage boundaries at wide transformations
- Tasks = one per partition = parallelism unit
- Shuffle cost: disk write + network + disk read
- Minimizing shuffles: broadcast, pre-partition, coalesce, AQE
