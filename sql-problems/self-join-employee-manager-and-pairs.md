# Self-Join Patterns — Employee-Manager Pairs and Mutual Referrals

**Type:** SQL Problem
**Topic:** Self Join, Hierarchical Queries, Pair-Finding

---

## The Question
> "Write a query to show every employee alongside their manager's name. Then write a query to find all pairs of users who referred each other."

---

## Part 1 — Employee-Manager Self Join

```sql
CREATE TABLE employees (
    employee_id INT,
    name        VARCHAR(50),
    manager_id  INT    -- references employee_id
);
```

```sql
SELECT
    e.employee_id,
    e.name          AS employee_name,
    m.name          AS manager_name
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.employee_id;
```

```
employee_id | employee_name | manager_name
------------|---------------|-------------
1           | Alice         | NULL          ← CEO, no manager
2           | Bob           | Alice
3           | Carol         | Alice
4           | Dave          | Bob
```

**Why LEFT JOIN:** The top-level employee (CEO) has `manager_id = NULL` — INNER JOIN would exclude them.

---

## Part 2 — Find Mutual Referrals (Pairs Who Referred Each Other)

```sql
CREATE TABLE referrals (
    referrer_id INT,
    referred_id INT
);
-- (1,2) means user 1 referred user 2
-- (2,1) means user 2 referred user 1
```

```sql
SELECT DISTINCT
    LEAST(r1.referrer_id, r2.referrer_id)    AS user_a,
    GREATEST(r1.referrer_id, r2.referrer_id) AS user_b
FROM referrals r1
JOIN referrals r2
  ON r1.referrer_id = r2.referred_id
 AND r1.referred_id = r2.referrer_id
WHERE r1.referrer_id < r2.referrer_id;   -- avoid duplicate pairs (1,2) and (2,1)
```

The `< condition` / `LEAST+GREATEST` pattern is the standard way to deduplicate symmetric pairs in SQL.

---

## Part 3 — Find Employees Earning More Than Their Manager

```sql
SELECT
    e.name          AS employee,
    e.salary        AS employee_salary,
    m.name          AS manager,
    m.salary        AS manager_salary
FROM employees e
JOIN employees m ON e.manager_id = m.employee_id
WHERE e.salary > m.salary;
```

Classic interview question — same table joined to itself with different roles.

---

## How to Say It in the Interview
> "A self join joins a table to itself using aliases — the same table plays two different roles. The employee-manager pattern is the most common example: alias 'e' for the employee row and 'm' for the manager row, join on manager_id = employee_id. Use LEFT JOIN to retain rows with no match, like the CEO with no manager. For finding symmetric pairs — users who referred each other — join the table to itself on reversed keys and use a less-than condition or LEAST/GREATEST to deduplicate, since (1,2) and (2,1) are the same pair."

---

## Common Mistakes
- Using INNER JOIN and losing the root node (CEO/top-level record)
- Getting duplicate pairs for symmetric relationships — forgetting the deduplication condition
- Confusing self join with recursive CTE — self join handles one level; recursive CTE handles arbitrary depth

---

## Key Concepts Tested
- Self join mechanics and aliases
- LEFT vs INNER JOIN for hierarchical data
- Symmetric pair deduplication (`<` condition or LEAST/GREATEST)
- Classic variants: salary comparison, friend-of-friend
