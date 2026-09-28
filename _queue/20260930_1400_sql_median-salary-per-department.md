---
publish_at: "2026-09-30T08:30:00Z"
folder: sql-problems
filename: find-median-salary-per-department.md
title: Find the median salary for each department
---

# Find the Median Salary for Each Department

**Type:** SQL Problem
**Topic:** Median, PERCENTILE_CONT, Window Functions

---

## The Question
> "Write a SQL query to find the median salary for each department."

```sql
-- employees(emp_id, department, salary)
```

---

## Why Median Is Tricky

You can't use `AVG()` — that's the mean, not median. SQL doesn't have a universal `MEDIAN()` function. The approach differs by database.

---

## Solution 1 — PERCENTILE_CONT (Modern SQL, Recommended)

Works in: **PostgreSQL, Snowflake, BigQuery, Redshift, SQL Server**

```sql
SELECT
    department,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary) AS median_salary
FROM employees
GROUP BY department;
```

`PERCENTILE_CONT(0.5)` = the value at the 50th percentile = median.
- **CONT** = continuous — interpolates between two middle values for even-count groups
- **DISC** = discrete — returns an actual value from the dataset (no interpolation)

```sql
-- For even number of employees:
-- PERCENTILE_CONT(0.5): averages the two middle values → 47500.0
-- PERCENTILE_DISC(0.5): returns the lower middle value  → 45000
```

---

## Solution 2 — Window Function Approach (Works Everywhere)

For MySQL or systems without `PERCENTILE_CONT`:

```sql
WITH ranked AS (
    SELECT
        department,
        salary,
        ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary)       AS rn,
        COUNT(*)     OVER (PARTITION BY department)                        AS total
    FROM employees
)
SELECT
    department,
    AVG(salary) AS median_salary
FROM ranked
WHERE rn IN (
    FLOOR((total + 1) / 2.0),     -- lower middle
    CEIL((total + 1) / 2.0)       -- upper middle (same as lower for odd count)
)
GROUP BY department;
```

**How the formula works:**
- Odd count (5 rows): `rn IN (3, 3)` → picks row 3 → middle row
- Even count (6 rows): `rn IN (3, 4)` → picks rows 3 and 4 → AVG of two middle values

---

## Example Walkthrough

| department | salary | rn | total |
|---|---|---|---|
| Eng | 60000 | 1 | 5 |
| Eng | 70000 | 2 | 5 |
| Eng | 80000 | **3** | 5 |  ← median (FLOOR(6/2)=3, CEIL(6/2)=3)
| Eng | 90000 | 4 | 5 |
| Eng | 100000 | 5 | 5 |

Median for Eng = 80000.

---

## PySpark Equivalent

```python
from pyspark.sql.functions import percentile_approx, expr

# Exact median
df.groupBy("department").agg(
    percentile_approx("salary", 0.5).alias("median_salary")
)

# Or using expr with SQL syntax
df.groupBy("department").agg(
    expr("percentile_approx(salary, 0.5)").alias("median_salary")
)
```

> Note: `percentile_approx` uses an approximation algorithm — fast for large datasets but not exact. For exact median in PySpark, use `pyspark.sql.functions.percentile` (Spark 3.4+).

---

## How to Say It in the Interview
> "For modern SQL systems like Snowflake or BigQuery, I'd use `PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary)` — clean, one line per department. For MySQL or older systems without that function, I'd use `ROW_NUMBER` to rank salaries within each department, then pick the middle row(s) using `FLOOR` and `CEIL` of the count, and average them. The key distinction is `PERCENTILE_CONT` interpolates for even-count groups while `PERCENTILE_DISC` returns an actual value from the data."

---

## Follow-ups & Answers

**"What's the difference between PERCENTILE_CONT and PERCENTILE_DISC?"**
> `CONT` (continuous): if the median falls between two values (even count), it averages them → can return a non-existent value like 47500 when data has only 45000 and 50000. `DISC` (discrete): always returns an actual value from the dataset — takes the lower of the two middle values.

**"How would you find the 90th percentile salary per department?"**
> Change `0.5` to `0.9` in `PERCENTILE_CONT(0.9)`. Same query, just a different percentile.

---

## Common Mistakes
- Using `AVG()` — that's mean, not median
- Not handling even vs odd count correctly in the manual approach
- Forgetting `WITHIN GROUP (ORDER BY ...)` clause with `PERCENTILE_CONT` — it's required
- Not knowing `PERCENTILE_CONT` exists — solving it with complex window functions when one line would do

---

## Key Concepts Tested
- PERCENTILE_CONT and PERCENTILE_DISC
- Manual median using ROW_NUMBER + FLOOR/CEIL
- Handling odd vs even row counts
- PySpark percentile_approx
