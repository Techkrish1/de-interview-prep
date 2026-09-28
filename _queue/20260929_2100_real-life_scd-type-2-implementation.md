---
publish_at: "2026-09-29T15:30:00Z"
folder: real-life-scenarios
filename: scd-type-2-implementation.md
title: Implement SCD Type 2 to track historical changes in a customer dimension
---

# Implement SCD Type 2 to Track Historical Changes in a Customer Dimension

**Type:** Real-life Scenario
**Topic:** Slowly Changing Dimensions, SCD Type 2, Delta Lake MERGE

---

## The Question
> "A customer's city or email changes over time. Your analytics team needs to know what city a customer was in at the time of each order — not just their current city. How do you implement this?"

---

## The Problem with SCD Type 1

SCD Type 1 = just overwrite. Simple, but loses history.

```
Customer U1 moves from Mumbai → Bangalore.
After overwrite: ALL past orders show Bangalore — even orders placed when they were in Mumbai.
→ Wrong! Revenue by city report is now inaccurate for history.
```

---

## SCD Type 2 — Keep Full History

Add `valid_from`, `valid_to`, and `is_current` columns. Each change creates a **new row** instead of overwriting.

```sql
-- DIM_CUSTOMER after SCD Type 2
| customer_key | customer_id | city      | valid_from | valid_to   | is_current |
|--------------|-------------|-----------|------------|------------|------------|
| 1            | C1          | Mumbai    | 2023-01-01 | 2024-06-14 | false      |
| 2            | C1          | Bangalore | 2024-06-15 | 9999-12-31 | true       |
```

`valid_to = 9999-12-31` is the sentinel value for the active record.

---

## Implementation with Delta Lake MERGE

```python
from delta.tables import DeltaTable
import pyspark.sql.functions as F
from datetime import date

today = str(date.today())   # "2024-06-15"

# incoming = new/changed customer records from source
incoming = spark.createDataFrame([
    ("C1", "Bangalore"),
    ("C2", "Chennai"),   # new customer
], ["customer_id", "city"])

dim = DeltaTable.forName(spark, "dim_customer")

# Step 1: Expire changed records (set valid_to = today, is_current = false)
dim.alias("target").merge(
    incoming.alias("source"),
    "target.customer_id = source.customer_id "
    "AND target.is_current = true "
    "AND target.city != source.city"     # only if something changed
).whenMatchedUpdate(set={
    "valid_to":    F.lit(today),
    "is_current":  F.lit(False)
}).execute()

# Step 2: Insert new/changed records as current rows
new_rows = (
    incoming.join(
        spark.read.table("dim_customer").filter("is_current = true"),
        "customer_id", "left_anti"     # customers not already current with same city
    )
    .withColumn("valid_from",   F.lit(today))
    .withColumn("valid_to",     F.lit("9999-12-31"))
    .withColumn("is_current",   F.lit(True))
)

new_rows.write.format("delta").mode("append").saveAsTable("dim_customer")
```

---

## Querying Point-in-Time Correctly

```sql
-- What city was each customer in at time of their order?
SELECT
    o.order_id,
    o.order_date,
    c.city           AS city_at_time_of_order,
    o.revenue
FROM fact_orders o
JOIN dim_customer c
    ON o.customer_id = c.customer_id
    AND o.order_date BETWEEN c.valid_from AND c.valid_to
```

This is the correct join — it picks the dimension row that was active on the order date.

---

## SCD Types — Quick Reference

| Type | Behavior | Use when |
|---|---|---|
| Type 0 | Never update — keep original | Immutable attributes (birthdate) |
| Type 1 | Overwrite — no history | Current value only matters (phone number) |
| Type 2 | New row per change — full history | Attribute affects historical analysis (city, tier) |
| Type 3 | Add column for previous value | Only last change matters (current + prior) |

---

## How to Say It in the Interview
> "SCD Type 2 keeps full history by adding `valid_from`, `valid_to`, and `is_current` columns. When an attribute changes, instead of overwriting the row, we expire the old row (set `valid_to` to today, `is_current` to false) and insert a new row as the current record. To join fact tables with this dimension correctly, I join on `order_date BETWEEN valid_from AND valid_to` — this picks the exact version of the dimension that was active on the transaction date. In Delta Lake, I implement this with a two-step MERGE: first expire changed rows, then insert new current rows."

---

## Follow-ups & Answers

**"What is a surrogate key and why do you need it for SCD Type 2?"**
> The source system's natural key (customer_id) is no longer unique — customer C1 now has two rows. So we introduce a surrogate key (auto-increment integer, e.g., `customer_key`) as the primary key of the dimension. The fact table joins on `customer_key`, not `customer_id`, ensuring it points to the exact historical version.

**"How do you handle new customers with no history?"**
> They have only one row: `valid_from = today`, `valid_to = 9999-12-31`, `is_current = true`. Same structure, just no expired predecessor row.

**"What is the disadvantage of SCD Type 2?"**
> Table grows over time — every attribute change adds a row. For customers who change frequently, the dimension can become very large. Also, queries must always include the date-range join condition, which is easy to forget.

---

## Common Mistakes
- Forgetting `valid_to = 9999-12-31` sentinel — some use NULL, which breaks BETWEEN joins
- Not including `is_current = true` condition in the expire step — could expire already-expired rows
- Joining fact to dimension on just `customer_id` — gets multiple rows (one per version)
- Not adding a surrogate key — the fact table has no way to point to a specific version

---

## Key Concepts Tested
- SCD Types 0, 1, 2, 3 — trade-offs
- valid_from / valid_to / is_current pattern
- Surrogate key necessity
- Point-in-time join pattern
- Delta Lake MERGE for SCD Type 2
