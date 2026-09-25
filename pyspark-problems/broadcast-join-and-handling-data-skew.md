# Broadcast Join and Handling Data Skew in PySpark

**Type:** PySpark Problem
**Topic:** Join Strategies, Broadcast Join, Data Skew, Salting

---

## The Question
> "You have a PySpark job joining a large transactions table (10 billion rows) with a small countries lookup table (200 rows). The job is slow and some executors are running out of memory. How do you fix it? Also explain the different join strategies Spark uses internally."

---

## Root Cause
Default Spark join = **Sort-Merge Join** — shuffles both datasets across the network by join key. For 10B × 200 rows, all 10B rows shuffle unnecessarily. Fix: **Broadcast Join**.

---

## The Fix — Broadcast Join

Send the small table to every executor as a local copy. Large table never moves.

```python
from pyspark.sql.functions import broadcast

result = transactions.join(
    broadcast(countries),    # Spark sends countries to every executor
    on="country_code",
    how="left"
)
```

**Auto-broadcast threshold (default 10MB):**
```python
# Increase threshold
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "50MB")

# Disable auto-broadcast (explicit control)
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "-1")
```
> Always prefer explicit `broadcast()` hint over relying on the threshold.

---

## All Four Spark Join Strategies

| Join Type | When Used | Mechanism |
|---|---|---|
| **Broadcast Hash Join** | One table fits in memory | Small table sent to all executors, hash lookup |
| **Sort-Merge Join** | Both tables large | Both shuffled, sorted, merged — default for large joins |
| **Shuffle Hash Join** | One side medium-sized | Smaller side hashed, larger side probed |
| **Cartesian Join** | No join condition | Every row × every row — extremely expensive, avoid |

**Verify which join Spark chose:**
```python
result.explain()          # or result.explain("formatted")
# Look for: BroadcastHashJoin / SortMergeJoin in the physical plan
```

---

## Second Problem — Data Skew

**Symptom:** One Spark task takes 10x longer than others (visible in Spark UI → Stages → Task timeline as a "straggler").

**Cause:** Join key is uneven — e.g., 80% of rows have `country_code = 'USA'`, all go to one partition.

**Fix — Salting:**
```python
import pyspark.sql.functions as F
from pyspark.sql.functions import array, explode, lit

NUM_SALTS = 10

# Add random salt to large table
transactions_salted = transactions.withColumn(
    "salted_key",
    F.concat(F.col("country_code"), F.lit("_"), (F.rand() * NUM_SALTS).cast("int"))
)

# Explode small table to cover all salt values
countries_salted = countries.withColumn(
    "salt", explode(array([lit(i) for i in range(NUM_SALTS)]))
).withColumn(
    "salted_key",
    F.concat(F.col("country_code"), F.lit("_"), F.col("salt"))
)

# Join on salted key — USA splits into USA_0, USA_1, ... USA_9
result = transactions_salted.join(
    countries_salted, on="salted_key", how="left"
).drop("salted_key", "salt")
```

---

## repartition vs coalesce

```python
df.repartition(n)   # full shuffle — increases or decreases, evenly distributed
df.coalesce(n)      # no shuffle — only decreases, can be uneven

# Use repartition: before wide transformations (joins, groupBy)
# Use coalesce: before writing output to reduce file count
```

---

## How to Say It in the Interview
> "Root cause is sort-merge join shuffling all 10 billion rows. Since countries is 200 rows, I'd wrap it in `broadcast()` — Spark sends the entire table to every executor as a hash map, eliminating the shuffle. To verify, I'd run `explain()` and confirm `BroadcastHashJoin` in the plan.
>
> If I still see straggler tasks in the Spark UI after that, it's data skew — one country dominates the join key. Fix is salting: append a random 0–9 to the large table key and explode the small table to cover all salt values, distributing the hot key across 10 partitions."

---

## Follow-ups & Answers

**"When does broadcast join hurt performance?"**
> When the "small" table isn't actually small — broadcasting 1GB to 500 executors = 500GB network traffic + memory pressure on every executor.

**"How do you check which join Spark is using?"**
> `df.explain()` or `df.explain("formatted")` — look for `BroadcastHashJoin` or `SortMergeJoin` in the physical plan.

---

## Common Mistakes
- Saying "increase executor memory" instead of using broadcast join
- Using `broadcast()` on a large table — causes OOM
- Not checking Spark UI to confirm skew before optimizing
- Confusing `repartition` (shuffle) and `coalesce` (no shuffle)

---

## Key Concepts Tested
- Spark join strategies: Broadcast, Sort-Merge, Shuffle Hash, Cartesian
- `broadcast()` hint and threshold config
- Data skew detection via Spark UI
- Salting for skew mitigation
- `repartition` vs `coalesce`
- `explain()` for query plan inspection
