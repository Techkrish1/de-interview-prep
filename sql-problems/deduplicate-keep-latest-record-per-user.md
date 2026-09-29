# Deduplicate a Table and Keep Only the Latest Record Per User

**Type:** SQL Problem
**Topic:** Deduplication, ROW_NUMBER, CTE

---

## The Question
> "You have a users table with duplicate records. Write SQL to delete duplicates and keep only the most recent record per user."

```sql
-- users(id, user_id, name, email, updated_at)
```

---

## Full Solution

```sql
WITH ranked AS (
    SELECT
        id,
        ROW_NUMBER() OVER (
            PARTITION BY user_id
            ORDER BY updated_at DESC, id DESC
        ) AS rn
    FROM users
)
DELETE FROM users
WHERE id IN (
    SELECT id FROM ranked WHERE rn > 1
);
```

`rn = 1` = latest record per user. Everything with `rn > 1` is a duplicate.

---

## BigQuery / Spark SQL — No DELETE with CTE

```sql
CREATE TABLE users_clean AS
SELECT * EXCEPT(rn)
FROM (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY user_id
            ORDER BY updated_at DESC, id DESC
        ) AS rn
    FROM users
)
WHERE rn = 1;
```

---

## PySpark

```python
from pyspark.sql import Window
import pyspark.sql.functions as F

w = Window.partitionBy("user_id").orderBy(F.desc("updated_at"), F.desc("id"))
df.withColumn("rn", F.row_number().over(w)).filter("rn = 1").drop("rn")
```

---

## How to Say It in the Interview
> "I use `ROW_NUMBER` partitioned by `user_id`, ordered by `updated_at` descending with `id` as tiebreaker. `rn = 1` is the latest record — delete everything where `rn > 1`. For BigQuery or Spark SQL that don't support DELETE with CTEs, I use `CREATE TABLE AS SELECT` with the window filter instead. Before any mass delete I always verify the row count with a SELECT first."

---

## Follow-ups & Answers

**"What if two records have the same updated_at?"**
> Add `id DESC` as tiebreaker — keeps the row with the highest id (most recently inserted).

**"Safe deletion practice?"**
> Always SELECT first to verify which rows will be removed. Run DELETE inside a transaction with ROLLBACK option. Check row counts before and after.

---

## Common Mistakes
- Using `MIN(id)` without ordering by `updated_at` — keeps oldest, not latest
- No tiebreaker for same timestamp rows
- Running DELETE without verifying the SELECT first

---

## Key Concepts Tested
- ROW_NUMBER for deduplication
- DELETE with CTE
- Platform-specific SQL (BigQuery vs PostgreSQL)
- Safe deletion practices
