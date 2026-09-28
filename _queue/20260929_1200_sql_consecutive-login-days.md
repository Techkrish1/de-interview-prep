---
publish_at: "2026-09-29T06:30:00Z"
folder: sql-problems
filename: find-users-with-consecutive-login-days.md
title: Find users who logged in on at least 3 consecutive days
---

# Find Users Who Logged In on at Least 3 Consecutive Days

**Type:** SQL Problem
**Topic:** Gaps and Islands, Date Arithmetic, Window Functions

---

## The Question
> "Given a table of user login events, find all users who logged in on at least 3 consecutive days."

```sql
-- logins(user_id, login_date)
-- One row per user per day (deduplicated — no duplicate dates per user)
```

---

## The Key Insight — Gaps and Islands Pattern

If you subtract a row's sequential rank from its date, rows that are on consecutive days produce the **same difference** value. This groups consecutive dates into "islands."

```
user_id | login_date | row_number | date - row_number (as days)
--------|------------|------------|-----------------------------
U1      | 2024-01-01 |     1      | 2024-01-01 - 1 = 2023-12-31   ← island A
U1      | 2024-01-02 |     2      | 2024-01-02 - 2 = 2023-12-31   ← island A (same!)
U1      | 2024-01-03 |     3      | 2024-01-03 - 3 = 2023-12-31   ← island A (same!)
U1      | 2024-01-07 |     4      | 2024-01-07 - 4 = 2024-01-03   ← island B (different)
U1      | 2024-01-08 |     5      | 2024-01-08 - 5 = 2024-01-03   ← island B (same)
```

Group by `(user_id, date - row_number)` → count rows per group → filter ≥ 3.

---

## Full Solution

```sql
WITH ranked AS (
    SELECT
        user_id,
        login_date,
        ROW_NUMBER() OVER (
            PARTITION BY user_id
            ORDER BY login_date
        ) AS rn
    FROM logins
),
islands AS (
    SELECT
        user_id,
        login_date - INTERVAL (rn - 1) DAY   AS island_start,
        -- Alternatively: DATE_SUB(login_date, INTERVAL rn DAY) in MySQL
        COUNT(*)                               AS consecutive_days
    FROM ranked
    GROUP BY user_id, login_date - INTERVAL (rn - 1) DAY
)
SELECT DISTINCT user_id
FROM islands
WHERE consecutive_days >= 3;
```

**PostgreSQL / Snowflake / BigQuery syntax:**
```sql
-- Use integer subtraction on DATE types
login_date - rn   AS island_key
-- or
login_date - CAST(rn AS INT)
```

**MySQL syntax:**
```sql
DATE_SUB(login_date, INTERVAL rn DAY) AS island_key
```

---

## Example Walkthrough

| user_id | login_date | rn | island_key |
|---|---|---|---|
| U1 | 2024-01-01 | 1 | 2023-12-31 |
| U1 | 2024-01-02 | 2 | 2023-12-31 |
| U1 | 2024-01-03 | 3 | 2023-12-31 |
| U1 | 2024-01-07 | 4 | 2024-01-03 |

Group (U1, 2023-12-31) → 3 rows ✓ → U1 qualifies.

---

## Variant — Find the Actual Consecutive Streaks (Start + End + Length)

```sql
SELECT
    user_id,
    MIN(login_date)       AS streak_start,
    MAX(login_date)       AS streak_end,
    COUNT(*)              AS streak_length
FROM ranked
GROUP BY user_id, login_date - INTERVAL (rn - 1) DAY
HAVING COUNT(*) >= 3
ORDER BY user_id, streak_start;
```

---

## How to Say It in the Interview
> "This is the classic gaps-and-islands problem. The trick is: if you subtract a row's sequential rank (ordered by date) from the date itself, consecutive dates produce the same difference value — they're in the same 'island.' I assign row numbers per user ordered by date, then group by `(user_id, date minus rank)`. Each group is a consecutive streak. Filter where `COUNT(*) >= 3` to find users with at least 3 consecutive days."

---

## Follow-ups & Answers

**"What if the same user logged in multiple times in one day?"**
> Deduplicate first: `SELECT DISTINCT user_id, login_date FROM logins` before applying the window function.

**"How would you find the longest streak per user?"**
> Remove the `HAVING` clause, keep all islands, then `MAX(consecutive_days)` per user:
```sql
SELECT user_id, MAX(consecutive_days) AS longest_streak
FROM islands
GROUP BY user_id;
```

**"What if login data is in PySpark?"**
```python
from pyspark.sql import Window
import pyspark.sql.functions as F

w = Window.partitionBy("user_id").orderBy("login_date")
df = df.withColumn("rn", F.row_number().over(w)) \
       .withColumn("island_key", F.date_sub("login_date", F.col("rn").cast("int")))

streaks = df.groupBy("user_id", "island_key").count()
streaks.filter("count >= 3").select("user_id").distinct()
```

---

## Common Mistakes
- Trying to use `LAG(login_date)` and comparing differences — works but much harder to generalize to streaks of N
- Forgetting to deduplicate same-day logins before ranking
- Using wrong date subtraction syntax for the SQL dialect
- Not knowing this is the "gaps and islands" pattern by name — interviewers often use that phrase

---

## Key Concepts Tested
- Gaps and islands pattern
- ROW_NUMBER + date arithmetic
- GROUP BY with derived key
- HAVING for aggregate filters
- Deduplication before window functions
- PySpark equivalency
