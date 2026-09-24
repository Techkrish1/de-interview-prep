# Find Top 3 Products by Revenue for Each Category Using PySpark

**Type:** PySpark Problem
**Topic:** Window Functions, GroupBy, Aggregations

---

## The Question
> "You have a large e-commerce dataset with product sales. Find the top 3 products by total revenue for each category using PySpark."

```
sales(order_id, product_id, category, product_name, quantity, unit_price)
```

---

## Break the Problem into Steps

| Step | What to do | PySpark Tool |
|---|---|---|
| 1 | Calculate total revenue per product per category | `groupBy` + `agg` |
| 2 | Rank products within each category by revenue | `Window` + `dense_rank` |
| 3 | Keep only top 3 | `filter(rank <= 3)` |

---

## Full Solution

```python
from pyspark.sql import SparkSession, Window
import pyspark.sql.functions as F

spark = SparkSession.builder.appName("TopProducts").getOrCreate()

# Step 1: Revenue per product per category
revenue_df = (
    df.groupBy("category", "product_id", "product_name")
      .agg(
          F.sum(F.col("quantity") * F.col("unit_price")).alias("total_revenue")
      )
)

# Step 2: Rank within each category (highest revenue = rank 1)
window = Window.partitionBy("category").orderBy(F.desc("total_revenue"))
ranked_df = revenue_df.withColumn("rank", F.dense_rank().over(window))

# Step 3: Filter top 3
top3_df = ranked_df.filter(F.col("rank") <= 3)

top3_df.orderBy("category", "rank").show()
```

---

## Why dense_rank() — Not row_number()

| Function | Tied products at rank 3 | Result |
|---|---|---|
| `dense_rank()` | Both get rank 3 — both appear | Correct for business top-N |
| `row_number()` | One gets rank 3, one gets rank 4 — one is dropped arbitrarily | Wrong |
| `rank()` | Both get rank 3, next rank skips to 5 | Returns more than 3 rows |

> **Rule:** Use `dense_rank()` for top-N business questions. Use `row_number()` only when you need exactly N rows with no ties.

---

## Spark SQL Alternative

```python
df.createOrReplaceTempView("sales")

spark.sql("""
    WITH revenue AS (
        SELECT
            category,
            product_id,
            product_name,
            SUM(quantity * unit_price) AS total_revenue
        FROM sales
        GROUP BY category, product_id, product_name
    ),
    ranked AS (
        SELECT *,
            DENSE_RANK() OVER (PARTITION BY category ORDER BY total_revenue DESC) AS rank
        FROM revenue
    )
    SELECT * FROM ranked WHERE rank <= 3
""").show()
```

---

## Performance at Scale — What to Mention

Window functions shuffle data: `PARTITION BY category` moves all rows of the same category to one executor. If one category dominates (skew), that executor bottlenecks.

**Mitigations:**
```python
# Push filters early — reduce data before aggregation
df.filter(F.col("order_date") >= "2024-01-01")

# Repartition by category before window to control shuffle
revenue_df.repartition("category")

# Cache if revenue_df is reused downstream
revenue_df.cache()
```

---

## How to Say It in the Interview
> "I'll break this into three steps: aggregate total revenue per product per category, then rank using a window function partitioned by category ordered by revenue descending, then filter rank ≤ 3. I'll use `dense_rank` so tied products both show up rather than arbitrarily dropping one. For production at scale, the concern is skew — if one category is much larger, I'd repartition by category before the window and push filters early to reduce shuffle volume."

---

## Follow-ups & Answers

**"What if new data arrives every hour?"**
> Store daily pre-aggregated revenue in a Delta/Iceberg table. Each hour, append new sales and recalculate only affected categories using `MERGE INTO` — avoids full dataset reprocessing.

**"Can you do this without a window function?"**
> Yes — `groupBy` category, collect product-revenue pairs into an array, sort and slice top 3. But this puts all data for a category in one row, worse for memory. Window + filter is the standard approach.

---

## Common Mistakes
- Using `row_number()` — drops tied products arbitrarily
- Applying window on raw rows instead of aggregated revenue first
- Forgetting `F.desc()` — returns bottom 3 instead of top 3
- Not mentioning skew or performance

---

## Key Concepts Tested
- PySpark DataFrame API: `groupBy`, `agg`, `withColumn`, `filter`
- Window functions: `partitionBy`, `orderBy`, `dense_rank`
- `dense_rank` vs `rank` vs `row_number`
- Spark SQL equivalency
- Performance: shuffle, skew, early filtering, caching
