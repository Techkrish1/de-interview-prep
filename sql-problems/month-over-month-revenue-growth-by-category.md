# Calculate Month-over-Month Revenue Growth Percentage by Category

**Type:** SQL Problem
**Topic:** LAG Window Function, Date Functions, Percentage Calculation

---

## The Question
> "Write a SQL query to calculate the month-over-month revenue growth percentage for each product category."

```sql
-- orders(order_id, category, revenue, order_date)
```

---

## What's Needed
For each category and month:
- Current month revenue
- Previous month revenue (via `LAG`)
- Growth % = `(current - previous) / previous * 100`

---

## Full Solution

```sql
WITH monthly AS (
    SELECT
        category,
        DATE_TRUNC('month', order_date)  AS month,
        SUM(revenue)                      AS monthly_revenue
    FROM orders
    GROUP BY category, DATE_TRUNC('month', order_date)
),
with_lag AS (
    SELECT
        category,
        month,
        monthly_revenue,
        LAG(monthly_revenue) OVER (
            PARTITION BY category
            ORDER BY month ASC
        ) AS prev_month_revenue
    FROM monthly
)
SELECT
    category,
    month,
    monthly_revenue,
    prev_month_revenue,
    ROUND(
        (monthly_revenue - prev_month_revenue) * 100.0 / prev_month_revenue,
        2
    ) AS growth_pct
FROM with_lag
WHERE prev_month_revenue IS NOT NULL    -- exclude first month (no prior to compare)
ORDER BY category, month;
```

---

## Example Output

| category | month | monthly_revenue | prev_month_revenue | growth_pct |
|---|---|---|---|---|
| Clothing | 2024-02-01 | 25000 | 20000 | 25.00 |
| Clothing | 2024-03-01 | 22000 | 25000 | -12.00 |
| Electronics | 2024-02-01 | 60000 | 50000 | 20.00 |
| Electronics | 2024-03-01 | 45000 | 60000 | -25.00 |

---

## LAG vs LEAD

```sql
LAG(col, n, default)  OVER (...)   -- look n rows BACK   (default returned if NULL)
LEAD(col, n, default) OVER (...)   -- look n rows FORWARD

-- Year-over-year: look back 12 months
LAG(monthly_revenue, 12) OVER (PARTITION BY category ORDER BY month)
```

---

## DATE_TRUNC Across SQL Dialects

```sql
-- PostgreSQL, BigQuery, Snowflake
DATE_TRUNC('month', order_date)   →  2024-03-01

-- MySQL
DATE_FORMAT(order_date, '%Y-%m')  →  '2024-03'

-- SQL Server
DATETRUNC(month, order_date)      →  2024-03-01

-- Extracting parts (all dialects)
YEAR(order_date) → 2024  |  MONTH(order_date) → 3
```

---

## Edge Cases to Mention

**1. Division by zero (previous month revenue = 0):**
```sql
CASE
    WHEN prev_month_revenue = 0 THEN NULL
    ELSE ROUND((monthly_revenue - prev_month_revenue) * 100.0 / prev_month_revenue, 2)
END AS growth_pct
```

**2. Missing months (category skipped a month):**
> `LAG` skips to the last available row — doesn't know a calendar month was missing. Fix: generate a full date spine, `LEFT JOIN` categories onto it so missing months appear as 0 revenue before applying `LAG`.

---

## PySpark Equivalent

```python
from pyspark.sql import Window
import pyspark.sql.functions as F

monthly = (
    df.groupBy("category", F.date_trunc("month", "order_date").alias("month"))
      .agg(F.sum("revenue").alias("monthly_revenue"))
)

w = Window.partitionBy("category").orderBy("month")

result = (
    monthly
    .withColumn("prev_revenue", F.lag("monthly_revenue").over(w))
    .withColumn("growth_pct",
        F.round((F.col("monthly_revenue") - F.col("prev_revenue")) * 100.0 / F.col("prev_revenue"), 2))
    .filter(F.col("prev_revenue").isNotNull())
)
```

---

## How to Say It in the Interview
> "Two CTEs: first aggregate revenue by category and month using `DATE_TRUNC`. Second, apply `LAG` partitioned by category ordered by month — gives previous month revenue in the same row. Compute growth as current minus previous divided by previous times 100. I'm using `100.0` to force decimal division. Filter `prev_month_revenue IS NOT NULL` to drop the first month. Two edge cases: divide-by-zero if previous revenue is 0 — wrap in CASE. And if a category skips a month entirely, LAG won't return the calendar-prior month — I'd need a date spine for correctness."

---

## Follow-ups & Answers

**"Year-over-year instead of month-over-month?"**
> `LAG(monthly_revenue, 12)` — look back 12 rows instead of 1. Everything else stays.

**"Categories with growth > 10% for 3 consecutive months?"**
> Add a rolling `MIN(growth_pct)` over a 3-row window per category. Filter where the minimum > 10.

---

## Common Mistakes
- `LAG` without `PARTITION BY category` — compares across categories
- Integer division: `* 100` truncates — must use `* 100.0`
- Not filtering `NULL` for first month — causes confusing output
- Not raising the missing-month edge case
- `ORDER BY month DESC` in window — `LAG` then looks forward, not back

---

## Key Concepts Tested
- `LAG()` and `LEAD()` window functions
- `DATE_TRUNC` and cross-dialect date functions
- Decimal vs integer division
- CTE chaining
- NULL handling in window functions
- Edge cases: divide-by-zero, missing months
- PySpark equivalency
