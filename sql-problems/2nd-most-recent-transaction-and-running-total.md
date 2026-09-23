# Find Each User's 2nd Most Recent Transaction and Running Total Spend

**Type:** SQL Problem
**Topic:** Window Functions

---

## The Question
> "You have a transactions table. Write SQL to find each user's 2nd most recent transaction and their running total spend up to that point."

```sql
-- transactions(user_id, txn_id, amount, txn_date)
```

---

## Break the Problem into Two Parts

| Part | What you need | SQL Tool |
|---|---|---|
| 2nd most recent transaction | Rank per user newest→oldest, pick rank 2 | `ROW_NUMBER()` |
| Running total up to that point | Cumulative sum per user oldest→newest | `SUM() OVER` with frame |

---

## Step-by-Step Build

**Step 1 — Rank transactions newest-first per user:**
```sql
ROW_NUMBER() OVER (
    PARTITION BY user_id
    ORDER BY txn_date DESC, txn_id DESC   -- txn_id breaks same-date ties
) AS rn
```

**Step 2 — Running total oldest-first per user:**
```sql
SUM(amount) OVER (
    PARTITION BY user_id
    ORDER BY txn_date ASC, txn_id ASC
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
) AS running_total
```

**Step 3 — Combine in a CTE, filter rn = 2:**
```sql
WITH ranked AS (
    SELECT
        user_id,
        txn_id,
        amount,
        txn_date,
        ROW_NUMBER() OVER (
            PARTITION BY user_id
            ORDER BY txn_date DESC, txn_id DESC
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

---

## Example Walkthrough

| user_id | txn_id | amount | txn_date |
|---|---|---|---|
| U1 | T1 | 100 | 2024-01-01 |
| U1 | T2 | 200 | 2024-01-05 |
| U1 | T3 | 150 | 2024-01-10 |

- 2nd most recent = **T2** (Jan 5)
- Running total up to T2 = 100 + 200 = **300**

**Output:**

| user_id | txn_id | amount | txn_date | running_total |
|---|---|---|---|---|
| U1 | T2 | 200 | 2024-01-05 | 300 |

---

## ROWS vs RANGE — The Detail That Separates Candidates

```sql
-- ROWS: counts physical rows — always predictable ✅
ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW

-- RANGE: groups rows with same ORDER BY value — risky for running totals ⚠️
RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
```

**Example — two transactions on the same date:**

| txn_id | amount | txn_date |
|---|---|---|
| T1 | 100 | 2024-01-05 |
| T2 | 200 | 2024-01-05 |

- `RANGE`: both rows show running_total = **300** (treated as a group)
- `ROWS`: T1 = 100, T2 = 300 (row by row, predictable)

**Rule: Always use `ROWS` for running totals.**

---

## ROW_NUMBER vs RANK vs DENSE_RANK

```sql
-- Scores: 100, 100, 90
ROW_NUMBER():  1, 2, 3   -- unique, arbitrary tiebreak — use for filtering
RANK():        1, 1, 3   -- ties share rank, skips numbers
DENSE_RANK():  1, 1, 2   -- ties share rank, no skips
```
> Use `ROW_NUMBER()` here — you need exactly one row per user at rank 2. `RANK()` could return two rows if two transactions share the same date.

---

## PySpark Equivalent
```python
from pyspark.sql import Window
import pyspark.sql.functions as F

w_rank = Window.partitionBy("user_id") \
               .orderBy(F.desc("txn_date"), F.desc("txn_id"))

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

## How to Say It in the Interview
> "I'll split this into two window functions inside a CTE. First, `ROW_NUMBER` partitioned by user, ordered newest-first — that ranks transactions so I can filter rank 2. Second, a running `SUM` partitioned by user, ordered oldest-first, with `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`. I use `ROWS` not `RANGE` to avoid unexpected results when two transactions share the same date."
>
> After writing: *"One edge case — users with only one transaction return no row. I'd ask if a NULL result is needed for those users."*

---

## Follow-ups & Answers

**"Top 3 instead of 2nd only?"**
> Change `WHERE rn = 2` to `WHERE rn <= 3`. No structural change.

**"How does this perform at scale?"**
> Window functions require a full scan. Mitigate with: table partitioning by `user_id`, bucketing in Spark, or materializing ranked snapshots incrementally rather than recomputing from scratch daily.

**"Can you do this without a CTE?"**
> Yes — use a subquery. CTEs are preferred for readability.

---

## Common Mistakes
- Using `RANK()` instead of `ROW_NUMBER()` for filtering — ties break the filter
- Forgetting `ROWS BETWEEN` — default RANGE gives wrong results on same-date ties
- Ordering running total `DESC` instead of `ASC`
- Trying to filter `WHERE rn = 2` at the same level as the window — must wrap in CTE first

---

## Key Concepts Tested
- Window functions: ROW_NUMBER, RANK, DENSE_RANK
- Frame specification: ROWS vs RANGE
- Running aggregates with SUM OVER
- CTE composition
- PySpark Window API
- Edge case awareness
