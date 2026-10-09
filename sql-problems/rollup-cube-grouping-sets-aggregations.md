# Multi-level Aggregations Using ROLLUP, CUBE, and GROUPING SETS

**Type:** SQL Problem
**Topic:** Advanced Aggregation, ROLLUP, CUBE, GROUPING SETS

---

## The Question
> "Write a query that shows revenue by region and category, plus subtotals per region, plus a grand total — all in one result set."

---

## Sample Data

```sql
sales: region | category    | revenue
       East   | Electronics | 5000
       East   | Clothing    | 2000
       West   | Electronics | 3000
       West   | Clothing    | 1500
```

---

## ROLLUP — Hierarchical Subtotals

Generates subtotals rolling up from the rightmost column to the leftmost, plus a grand total.

```sql
SELECT
    region,
    category,
    SUM(revenue) AS total_revenue
FROM sales
GROUP BY ROLLUP(region, category);
```

```
region | category    | total_revenue
-------|-------------|---------------
East   | Clothing    | 2000
East   | Electronics | 5000
East   | NULL        | 7000          ← East subtotal
West   | Clothing    | 1500
West   | Electronics | 3000
West   | NULL        | 4500          ← West subtotal
NULL   | NULL        | 11500         ← Grand total
```

NULL in the output means "this level was rolled up / aggregated away."

---

## CUBE — All Combinations of Subtotals

Generates subtotals for every possible combination of the grouping columns.

```sql
SELECT region, category, SUM(revenue)
FROM sales
GROUP BY CUBE(region, category);
```

```
region | category    | total
-------|-------------|-------
East   | Electronics | 5000   ← both specified
East   | Clothing    | 2000
West   | Electronics | 3000
West   | Clothing    | 1500
East   | NULL        | 7000   ← East, all categories
West   | NULL        | 4500   ← West, all categories
NULL   | Electronics | 8000   ← all regions, Electronics
NULL   | Clothing    | 3500   ← all regions, Clothing
NULL   | NULL        | 11500  ← grand total
```

CUBE = ROLLUP + cross-dimension subtotals. 2 columns → 2² = 4 grouping combinations.

---

## GROUPING SETS — Custom Combinations

Specify exactly which combinations you want.

```sql
SELECT region, category, SUM(revenue)
FROM sales
GROUP BY GROUPING SETS (
    (region, category),   -- detail level
    (region),             -- region subtotal only
    ()                    -- grand total only
);
-- Equivalent to ROLLUP(region, category) in this case
```

**Use when you need specific combinations** — e.g., subtotals by region AND by category but not by their cross-product (avoids CUBE's extra rows).

---

## Distinguish NULL Subtotals from Real NULLs

Use `GROUPING()` to tell if a NULL is a rollup or an actual NULL value:

```sql
SELECT
    CASE WHEN GROUPING(region) = 1 THEN 'ALL REGIONS' ELSE region END AS region,
    CASE WHEN GROUPING(category) = 1 THEN 'ALL CATEGORIES' ELSE category END AS category,
    SUM(revenue)
FROM sales
GROUP BY ROLLUP(region, category);
```

`GROUPING(col) = 1` means that column was aggregated away (it's a subtotal row).

---

## When to Use Each

| Function | Use case |
|---|---|
| `ROLLUP` | Hierarchical reports: year → month → day, country → region → city |
| `CUBE` | Cross-dimensional analysis: all combinations of dimensions |
| `GROUPING SETS` | Custom mix — when you need specific aggregation levels, not all of them |

---

## How to Say It in the Interview
> "ROLLUP generates subtotals by progressively rolling up from the finest grain to the coarsest — perfect for hierarchical reports like country → region → city totals. CUBE generates all possible combinations of subtotals — useful for pivot-style analysis. GROUPING SETS lets you specify exactly which aggregation levels you need when you don't want the full CUBE. NULLs in rollup results represent aggregated dimensions — use GROUPING() to distinguish them from actual NULL values in the data."

---

## Common Mistakes
- Confusing output NULLs (from rollup) with data NULLs — always use GROUPING()
- Using CUBE when you only need one direction of subtotals — ROLLUP is simpler
- Not knowing these exist and writing multiple UNION ALL queries instead

---

## Key Concepts Tested
- ROLLUP: hierarchical subtotals
- CUBE: all-combinations subtotals
- GROUPING SETS: custom combinations
- GROUPING() function to handle NULL ambiguity
