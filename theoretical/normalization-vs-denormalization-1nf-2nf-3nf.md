# Normalization vs Denormalization — 1NF, 2NF, 3NF and When to Denormalize

**Type:** Theoretical
**Topic:** Data Modeling, Normalization, OLTP vs OLAP

---

## The Question
> "Explain database normalization — 1NF, 2NF, and 3NF. When would you deliberately denormalize?"

---

## Why Normalize?

Normalization eliminates redundancy and update anomalies.

**Unnormalized problem:**
```
orders: order_id | customer_name | customer_email | product | category | price
1        Alice     alice@x.com    Laptop           Electronics  999
2        Alice     alice@x.com    Mouse            Electronics   29
```
Alice's email stored twice. If it changes, must update every row — miss one → inconsistency.

---

## 1NF — First Normal Form

Rule: Every column holds atomic (indivisible) values. No repeating groups.

```
VIOLATES 1NF:
order_id | products
1        | "Laptop, Mouse, Keyboard"   ← not atomic

SATISFIES 1NF:
order_id | product
1        | Laptop
1        | Mouse
1        | Keyboard
```

---

## 2NF — Second Normal Form

Rule: 1NF + every non-key column depends on the ENTIRE primary key (no partial dependency).
Applies only when the primary key is composite.

```
VIOLATES 2NF (PK = order_id + product_id):
order_id | product_id | quantity | product_name | category
1        | 101        | 2        | Laptop       | Electronics

product_name depends only on product_id (partial dependency) → move to products table

SATISFIES 2NF:
order_items: order_id | product_id | quantity
products:    product_id | product_name | category
```

---

## 3NF — Third Normal Form

Rule: 2NF + no transitive dependencies (non-key column depends on another non-key column).

```
VIOLATES 3NF:
employees: employee_id | dept_id | dept_name | dept_location
dept_name depends on dept_id (not on employee_id) → transitive dependency

SATISFIES 3NF:
employees:   employee_id | dept_id
departments: dept_id | dept_name | dept_location
```

---

## OLTP vs OLAP — Why Normalization Rules Differ

| | OLTP (transactional) | OLAP (analytics) |
|---|---|---|
| Goal | Fast writes, data integrity | Fast reads, aggregations |
| Schema | Normalized (3NF) | Denormalized (star schema) |
| Joins | Many joins OK (small result sets) | Joins are expensive at scale |
| Example | MySQL order system | Snowflake fact/dimension tables |

---

## When to Denormalize

Denormalize deliberately in analytical systems when:
- Query performance matters more than write efficiency
- Data is read far more than written
- Joins become the bottleneck at scale

```sql
-- Normalized (3NF): requires 3-table join for every query
SELECT c.name, p.category, SUM(oi.quantity * oi.price)
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
GROUP BY 1, 2;

-- Denormalized (wide table in data warehouse):
SELECT customer_name, product_category, SUM(revenue)
FROM fct_orders
GROUP BY 1, 2;   -- no joins needed
```

**Star schema** is the standard denormalization for analytics: one fact table with FK references to dimension tables. Reduces join complexity vs fully normalized while avoiding the worst data duplication of a single wide table.

---

## How to Say It in the Interview
> "1NF requires atomic values — no comma-separated lists in a column. 2NF removes partial dependencies — every non-key column depends on the whole primary key, not just part of it. 3NF removes transitive dependencies — no non-key column depends on another non-key column. These rules eliminate redundancy and update anomalies, which is critical for OLTP systems.
>
> For analytics, we deliberately denormalize. Normalized schemas require many joins which are expensive at scale when you're scanning billions of rows. Star schema is the standard compromise — a fact table with FK references to dimensions. Enough denormalization for fast analytical queries, without full wide-table redundancy."

---

## Common Mistakes
- Mixing up 2NF (partial dependency) and 3NF (transitive dependency)
- Not knowing that normalization is for OLTP, not OLAP
- Saying "denormalization is bad" without the OLAP context
- Forgetting that 2NF only matters when there's a composite primary key

---

## Key Concepts Tested
- 1NF: atomic values
- 2NF: no partial dependencies on composite PK
- 3NF: no transitive dependencies
- OLTP → normalize; OLAP → denormalize for read performance
- Star schema as the standard analytical denormalization
