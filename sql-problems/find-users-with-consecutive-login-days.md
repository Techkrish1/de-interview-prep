# Find Users Who Logged In on at Least 3 Consecutive Days

**Type:** SQL Problem
**Topic:** Gaps and Islands, Date Arithmetic

---

## The Question
> "Given a table of user login events, find all users who logged in on at least 3 consecutive days."

```sql
-- logins(user_id, login_date)  — one row per user per day (deduplicated)
```

---

## The Key Insight — Gaps and Islands

Subtract a row's sequential rank from its date → consecutive dates produce the **same difference** value → group them as one "island."

```
user_id | login_date | rn | date - rn
--------|------------|----|-----------
U1      | 2024-01-01 |  1 | 2023-12-31  ← island A
U1      | 2024-01-02 |  2 | 2023-12-31  ← island A (same!)
U1      | 2024-01-03 |  3 | 2023-12-31  ← island A (same!)
U1      | 2024-01-07 |  4 | 2024-01-03  ← island B (gap!)
```

Group by `(user_id, date - rn)` → count rows → filter ≥ 3.

---

## Full Solution

```sql
WITH ranked AS (
    SELECT
        user_id,
        login_date,
        ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY login_date) AS rn
    FROM logins
),
islands AS (
    SELECT
        user_id,
        login_date - INTERVAL (rn - 1) DAY  AS island_key,
        COUNT(*)                              AS consecutive_days
    FROM ranked
    GROUP BY user_id, login_date - INTERVAL (rn - 1) DAY
)
SELECT DISTINCT user_id
FROM islands
WHERE consecutive_days >= 3;
```

**PostgreSQL / Snowflake:** `login_date - rn` (integer subtraction on DATE type)
**MySQL:** `DATE_SUB(login_date, INTERVAL rn DAY)`

---

## Streak Start + End + Length

```sql
SELECT
    user_id,
    MIN(login_date)  AS streak_start,
    MAX(login_date)  AS streak_end,
    COUNT(*)         AS streak_length
FROM ranked
GROUP BY user_id, login_date - INTERVAL (rn - 1) DAY
HAVING COUNT(*) >= 3;
```

---

## PySpark Equivalent

```python
from pyspark.sql import Window
import pyspark.sql.functions as F

w = Window.partitionBy("user_id").orderBy("login_date")
df = df.withColumn("rn", F.row_number().over(w)) \
       .withColumn("island_key", F.date_sub("login_date", F.col("rn").cast("int")))

df.groupBy("user_id", "island_key").count() \
  .filter("count >= 3").select("user_id").distinct()
```

---

## How to Say It in the Interview
> "This is the gaps-and-islands problem. The trick: subtract each row's sequential rank (ordered by date) from the date itself — consecutive dates produce the same difference. I assign row numbers per user, group by `(user_id, date minus rank)`, count rows per group — each group is a consecutive streak. Filter where count ≥ 3."

---

## Follow-ups & Answers

**"Same user logged in twice in one day?"**
> Deduplicate first: `SELECT DISTINCT user_id, login_date FROM logins`.

**"Longest streak per user?"**
> Remove HAVING, then `MAX(consecutive_days)` per user from the islands CTE.

---

## Common Mistakes
- Using LAG and comparing date differences — works but harder to generalize to N days
- Forgetting to deduplicate same-day logins
- Not naming this the "gaps and islands" pattern — interviewers use this term

---

## Key Concepts Tested
- Gaps and islands pattern
- ROW_NUMBER + date arithmetic
- GROUP BY with derived key
- HAVING for aggregate filters
