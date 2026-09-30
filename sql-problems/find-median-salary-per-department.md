# Find the Median Salary for Each Department

**Type:** SQL Problem
**Topic:** PERCENTILE_CONT, Median, Window Functions

---

## The Question
> "Write a SQL query to find the median salary for each department."

```sql
-- employees(emp_id, department, salary)
```

---

## Solution 1 — PERCENTILE_CONT (Modern SQL, Recommended)

**PostgreSQL, Snowflake, BigQuery, Redshift, SQL Server:**

```sql
SELECT
    department,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary) AS median_salary
FROM employees
GROUP BY department;
```

- `PERCENTILE_CONT(0.5)` = 50th percentile = median
- **CONT** (continuous): interpolates between two middle values for even-count groups
- **DISC** (discrete): returns an actual value from the dataset

---

## Solution 2 — ROW_NUMBER Approach (MySQL / Everywhere)

```sql
WITH ranked AS (
    SELECT
        department,
        salary,
        ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary) AS rn,
        COUNT(*)     OVER (PARTITION BY department)                  AS total
    FROM employees
)
SELECT department, AVG(salary) AS median_salary
FROM ranked
WHERE rn IN (FLOOR((total + 1) / 2.0), CEIL((total + 1) / 2.0))
GROUP BY department;
```

- Odd count (5): `rn IN (3, 3)` → middle row
- Even count (6): `rn IN (3, 4)` → average of two middle values

---

## PySpark

```python
from pyspark.sql.functions import percentile_approx

df.groupBy("department").agg(
    percentile_approx("salary", 0.5).alias("median_salary")
)
```

> `percentile_approx` uses an approximation — fast for large datasets but not exact.

---

## How to Say It in the Interview
> "For Snowflake or BigQuery I'd use `PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary)` — clean one liner. For MySQL, I'd use `ROW_NUMBER` to rank salaries within each department, then pick the middle row(s) using `FLOOR` and `CEIL` of the count, and average them. Key difference: CONT interpolates for even-count groups, DISC returns an actual value."

---

## Follow-ups & Answers

**"PERCENTILE_CONT vs PERCENTILE_DISC?"**
> CONT: averages two middle values for even count → can return a non-existent value (e.g., 47500 when data only has 45000 and 50000). DISC: always returns an actual value — takes the lower of the two middle values.

**"90th percentile salary per department?"**
> Change `0.5` to `0.9` in `PERCENTILE_CONT(0.9)`. Same query.

---

## Common Mistakes
- Using `AVG()` — that's mean, not median
- Forgetting `WITHIN GROUP (ORDER BY ...)` — required with PERCENTILE_CONT
- Not knowing PERCENTILE_CONT exists — solving it with complex windows when one line would do

---

## Key Concepts Tested
- PERCENTILE_CONT and PERCENTILE_DISC
- Manual median with ROW_NUMBER + FLOOR/CEIL
- Odd vs even row count handling
- PySpark percentile_approx
