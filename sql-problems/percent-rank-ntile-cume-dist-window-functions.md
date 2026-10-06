# Rank Customers into Percentiles Using PERCENT_RANK, NTILE, and CUME_DIST

**Type:** SQL Problem
**Topic:** Window Functions, Percentiles, Ranking

---

## The Question
> "Given a customers table with total_spend, write queries to: (1) find each customer's percentile rank by spend, (2) bucket customers into 4 equal spend tiers, (3) find all customers in the top 25% by spend."

---

## Sample Data

```sql
CREATE TABLE customers (
    customer_id INT,
    name        VARCHAR(50),
    total_spend DECIMAL(10,2)
);
-- Values: 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000
```

---

## PERCENT_RANK — Where Does This Row Rank Relatively?

Formula: `(rank - 1) / (total_rows - 1)`
Range: 0.0 to 1.0

```sql
SELECT
    customer_id,
    name,
    total_spend,
    PERCENT_RANK() OVER (ORDER BY total_spend) AS pct_rank
FROM customers;
```

```
customer_id | total_spend | pct_rank
------------|-------------|----------
1           | 100         | 0.00      ← bottom
2           | 200         | 0.11
3           | 300         | 0.22
...
10          | 1000        | 1.00      ← top
```

**Use case:** "What percentile is this customer in?" — `pct_rank = 0.75` means 75th percentile (better than 75% of customers).

---

## NTILE — Bucket Rows into N Equal Groups

```sql
SELECT
    customer_id,
    name,
    total_spend,
    NTILE(4) OVER (ORDER BY total_spend) AS spend_quartile
FROM customers;
```

```
customer_id | total_spend | spend_quartile
------------|-------------|---------------
1           | 100         | 1   ← bottom 25%
2           | 200         | 1
3           | 300         | 2
4           | 400         | 2
5           | 500         | 3
6           | 600         | 3
7           | 700         | 4
8           | 800         | 4
9           | 900         | 4
10          | 1000        | 4
```

**Use case:** Customer segmentation — bronze/silver/gold/platinum tiers.

---

## CUME_DIST — What Fraction of Rows Are ≤ This Value?

Formula: `rows with value <= current row / total rows`
Range: just above 0.0 to 1.0

```sql
SELECT
    customer_id,
    total_spend,
    CUME_DIST() OVER (ORDER BY total_spend) AS cum_dist
FROM customers;
```

```
customer_id | total_spend | cum_dist
------------|-------------|----------
1           | 100         | 0.10
5           | 500         | 0.50
10          | 1000        | 1.00
```

`cume_dist = 0.50` means 50% of customers spend ≤ this amount.

**Difference from PERCENT_RANK:** CUME_DIST includes the current row in the count; PERCENT_RANK excludes it. CUME_DIST is never 0.

---

## Find Top 25% by Spend

```sql
-- Using PERCENT_RANK
SELECT customer_id, name, total_spend
FROM (
    SELECT *,
        PERCENT_RANK() OVER (ORDER BY total_spend DESC) AS pct_rank
    FROM customers
) ranked
WHERE pct_rank <= 0.25;

-- Using NTILE
SELECT customer_id, name, total_spend
FROM (
    SELECT *, NTILE(4) OVER (ORDER BY total_spend) AS quartile
    FROM customers
) t
WHERE quartile = 4;
```

---

## PERCENT_RANK vs NTILE vs CUME_DIST

| Function | Returns | Use Case |
|---|---|---|
| `PERCENT_RANK` | Relative rank 0–1 | "What percentile is this customer?" |
| `NTILE(N)` | Bucket number 1–N | "Put customers into N equal groups" |
| `CUME_DIST` | Fraction of rows ≤ value | "What % of customers spend ≤ this?" |

---

## How to Say It in the Interview
> "PERCENT_RANK gives a 0-to-1 score showing relative rank — 0.75 means better than 75% of rows. NTILE divides rows into N equal buckets and assigns a bucket number — useful for customer tier segmentation. CUME_DIST gives the cumulative fraction of rows at or below the current value. For 'top 25% by spend', I'd use NTILE(4) and filter for quartile = 4, or PERCENT_RANK with a threshold filter."

---

## Common Mistakes
- Confusing PERCENT_RANK (relative rank excluding self) with CUME_DIST (fraction including self)
- Forgetting PERCENT_RANK returns 0 for the lowest row (not 1)
- Using NTILE when group sizes need to be exactly equal — NTILE distributes remainder rows to earlier buckets, so groups may differ by 1

---

## Key Concepts Tested
- PERCENT_RANK: relative rank formula and range
- NTILE: equal bucketing
- CUME_DIST: cumulative distribution
- Practical: filtering top/bottom N percentile
