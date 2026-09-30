# Implement SCD Type 2 to Track Historical Changes in a Customer Dimension

**Type:** Real-life Scenario
**Topic:** Slowly Changing Dimensions, Delta Lake MERGE

---

## The Question
> "A customer's city changes over time. Analytics needs to know what city a customer was in at the time of each order — not their current city. How do you implement this?"

---

## Why SCD Type 1 Fails

SCD Type 1 = overwrite. Loses history.

```
Customer moves Mumbai → Bangalore.
After overwrite: ALL past orders show Bangalore — even orders from Mumbai period.
→ Revenue-by-city report is wrong for history.
```

---

## SCD Type 2 — New Row Per Change

```sql
| customer_key | customer_id | city      | valid_from | valid_to   | is_current |
|--------------|-------------|-----------|------------|------------|------------|
| 1            | C1          | Mumbai    | 2023-01-01 | 2024-06-14 | false      |
| 2            | C1          | Bangalore | 2024-06-15 | 9999-12-31 | true       |
```

`valid_to = 9999-12-31` = sentinel for active record.

---

## Implementation with Delta Lake MERGE

```python
from delta.tables import DeltaTable
import pyspark.sql.functions as F
from datetime import date

today = str(date.today())

# Step 1: Expire changed records
DeltaTable.forName(spark, "dim_customer").alias("t").merge(
    incoming.alias("s"),
    "t.customer_id = s.customer_id AND t.is_current = true AND t.city != s.city"
).whenMatchedUpdate(set={
    "valid_to":   F.lit(today),
    "is_current": F.lit(False)
}).execute()

# Step 2: Insert new current rows
new_rows = (
    incoming
    .join(spark.read.table("dim_customer").filter("is_current = true"),
          "customer_id", "left_anti")
    .withColumn("valid_from",   F.lit(today))
    .withColumn("valid_to",     F.lit("9999-12-31"))
    .withColumn("is_current",   F.lit(True))
)
new_rows.write.format("delta").mode("append").saveAsTable("dim_customer")
```

---

## Point-in-Time Join Pattern

```sql
SELECT o.order_id, o.order_date, c.city AS city_at_time_of_order, o.revenue
FROM fact_orders o
JOIN dim_customer c
    ON o.customer_id = c.customer_id
    AND o.order_date BETWEEN c.valid_from AND c.valid_to
```

---

## SCD Types Quick Reference

| Type | Behavior | Use when |
|---|---|---|
| 0 | Never update | Immutable (birthdate) |
| 1 | Overwrite | Current value only (phone) |
| 2 | New row per change | Affects historical analysis (city, tier) |
| 3 | Add previous-value column | Only last change matters |

---

## How to Say It in the Interview
> "SCD Type 2 keeps history by adding `valid_from`, `valid_to`, `is_current`. When an attribute changes: expire the old row (set `valid_to` = today, `is_current` = false), insert a new row as the current record. To join fact tables correctly, join on `order_date BETWEEN valid_from AND valid_to` — picks the exact dimension version active on the transaction date. In Delta Lake I use a two-step MERGE: first expire, then append new current rows."

---

## Follow-ups & Answers

**"Why do you need a surrogate key?"**
> `customer_id` is no longer unique — C1 now has two rows. Surrogate key (`customer_key`) is the primary key; the fact table joins on this, pointing to the exact historical version.

**"Disadvantage of SCD Type 2?"**
> Table grows over time. Queries must always include the date-range join — easy to forget and causes row multiplication.

---

## Common Mistakes
- Using NULL for `valid_to` instead of `9999-12-31` — breaks BETWEEN joins
- Joining fact to dimension on just `customer_id` — gets multiple rows (one per version)
- Forgetting surrogate key

---

## Key Concepts Tested
- SCD Types 1, 2, 3
- valid_from / valid_to / is_current pattern
- Surrogate key
- Point-in-time join
- Delta Lake MERGE
