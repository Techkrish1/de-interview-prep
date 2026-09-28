---
publish_at: "2026-09-28T13:30:00Z"
folder: sql-problems
filename: deduplicate-keep-latest-record-per-user.md
title: Deduplicate a table and keep only the latest record per user
---

# Deduplicate a Table and Keep Only the Latest Record Per User

**Type:** SQL Problem
**Topic:** Deduplication, ROW_NUMBER, CTE

---

## The Question
> "You have a users table with duplicate records — the same user_id appears multiple times due to a pipeline bug. Write SQL to delete duplicates and keep only the most recent record per user."

```sql
-- users(id, user_id, name, email, updated_at)
-- id = auto-increment primary key (unique per row)
-- user_id = the business identifier (has duplicates)
```

---

## Step-by-Step Solution

### Step 1 — Identify which rows to keep (latest per user_id)

```sql
SELECT
    id,
    user_id,
    ROW_NUMBER() OVER (
        PARTITION BY user_id
        ORDER BY updated_at DESC, id DESC    -- tiebreaker on id
    ) AS rn
FROM users
```

`rn = 1` is the latest record per user. Everything else is a duplicate.

### Step 2 — Delete duplicates (keep rn = 1)

**Option A — DELETE with CTE (PostgreSQL, SQL Server, Snowflake):**
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

**Option B — CREATE TABLE AS SELECT (BigQuery, Hive, Spark SQL):**
```sql
-- BigQuery / Spark SQL don't support DELETE with CTEs easily
-- Create a clean table instead:
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

**Option C — Using NOT IN with subquery (works everywhere):**
```sql
DELETE FROM users
WHERE id NOT IN (
    SELECT MIN(id)    -- if you want the oldest (use MAX for newest by id)
    FROM (
        SELECT id,
            ROW_NUMBER() OVER (
                PARTITION BY user_id
                ORDER BY updated_at DESC, id DESC
            ) AS rn
        FROM users
    ) ranked
    WHERE rn = 1
);
```

---

## Example Walkthrough

| id | user_id | name | updated_at |
|---|---|---|---|
| 1 | U1 | Alice | 2024-01-01 |
| 3 | U1 | Alice | 2024-01-10 ← keep |
| 5 | U1 | Alice | 2024-01-05 |
| 2 | U2 | Bob | 2024-02-01 ← keep (only one) |

After dedup, only `id=3` (U1, latest) and `id=2` (U2) remain.

---

## How to Say It in the Interview
> "I'd use `ROW_NUMBER` partitioned by `user_id`, ordered by `updated_at` descending. `rn = 1` is the latest record per user — everything with `rn > 1` is a duplicate. For deletion, I'd wrap this in a CTE and delete rows where `id IN (SELECT id FROM ranked WHERE rn > 1)`. For systems like BigQuery that don't support DELETE with CTEs well, I'd use `CREATE TABLE AS SELECT` with the window function filter instead."

---

## Follow-ups & Answers

**"What if two records have the same updated_at?"**
> Add `id DESC` as a tiebreaker in the `ORDER BY` — keep the row with the highest `id` (most recently inserted).

**"How would you do this in PySpark?"**
```python
from pyspark.sql import Window
import pyspark.sql.functions as F

w = Window.partitionBy("user_id").orderBy(F.desc("updated_at"), F.desc("id"))
df.withColumn("rn", F.row_number().over(w)).filter("rn = 1").drop("rn")
```

**"What's the risk of deleting vs creating a new table?"**
> DELETE modifies in place — risk of data loss if logic is wrong. Safer: CREATE TABLE AS SELECT the clean version, validate row counts, then swap tables. Always take a backup or test in a transaction with ROLLBACK before committing a mass DELETE.

---

## Common Mistakes
- Using `MIN(id)` without ordering by `updated_at` — keeps oldest, not latest
- Not having a tiebreaker for same timestamp rows
- Running DELETE without first SELECTing to verify which rows will be removed
- Not checking row counts before and after

---

## Key Concepts Tested
- ROW_NUMBER for deduplication
- DELETE with CTE
- Handling ties in ordering
- Platform-specific SQL (BigQuery vs PostgreSQL)
- PySpark equivalency
- Safe deletion practices
