# Use a Recursive CTE to Find All Employees in a Manager's Hierarchy

**Type:** SQL Problem
**Topic:** Recursive CTE, Hierarchical Queries

---

## The Question
> "You have an `employees` table with `employee_id`, `name`, and `manager_id`. Write a query to find all employees that report (directly or indirectly) to manager_id = 5."

---

## Sample Data

```sql
CREATE TABLE employees (
    employee_id INT,
    name        VARCHAR(50),
    manager_id  INT     -- NULL for the CEO
);

-- Hierarchy:
-- 5 (Alice)
--   ├── 8 (Bob)      → reports to Alice
--   │     └── 12 (Carol)  → reports to Bob
--   └── 9 (Dave)     → reports to Alice
--         └── 15 (Eve)    → reports to Dave
```

---

## Solution

```sql
WITH RECURSIVE hierarchy AS (
    -- Anchor: start with the manager themselves
    SELECT
        employee_id,
        name,
        manager_id,
        0 AS depth
    FROM employees
    WHERE employee_id = 5

    UNION ALL

    -- Recursive: join direct reports of everyone in current result
    SELECT
        e.employee_id,
        e.name,
        e.manager_id,
        h.depth + 1
    FROM employees e
    INNER JOIN hierarchy h ON e.manager_id = h.employee_id
)
SELECT employee_id, name, manager_id, depth
FROM hierarchy
WHERE employee_id != 5   -- exclude the manager if you only want reports
ORDER BY depth, name;
```

**Result:**
```
employee_id | name  | manager_id | depth
------------|-------|------------|------
8           | Bob   | 5          | 1
9           | Dave  | 5          | 1
12          | Carol | 8          | 2
15          | Eve   | 9          | 2
```

---

## How It Works

```
Iteration 0 (anchor):   {Alice (5, depth=0)}
Iteration 1 (recurse):  join employees where manager_id IN {5}  → {Bob(8), Dave(9), depth=1}
Iteration 2 (recurse):  join employees where manager_id IN {8,9} → {Carol(12), Eve(15), depth=2}
Iteration 3 (recurse):  no employees with manager_id IN {12,15} → stops
```

The recursion terminates when the recursive SELECT returns zero rows.

---

## Variation: Full Path

```sql
WITH RECURSIVE hierarchy AS (
    SELECT
        employee_id,
        name,
        CAST(name AS VARCHAR(500)) AS path
    FROM employees
    WHERE employee_id = 5

    UNION ALL

    SELECT
        e.employee_id,
        e.name,
        CONCAT(h.path, ' → ', e.name)
    FROM employees e
    JOIN hierarchy h ON e.manager_id = h.employee_id
)
SELECT employee_id, name, path FROM hierarchy;
-- path: Alice → Bob → Carol
```

---

## Variation: Find Root (CEO) of Any Employee

```sql
WITH RECURSIVE upward AS (
    SELECT employee_id, name, manager_id FROM employees WHERE employee_id = 12
    UNION ALL
    SELECT e.employee_id, e.name, e.manager_id
    FROM employees e JOIN upward u ON e.employee_id = u.manager_id
)
SELECT * FROM upward WHERE manager_id IS NULL;  -- NULL = CEO
```

---

## How to Say It in the Interview
> "Recursive CTEs work in two parts: the anchor query which seeds the recursion with the starting rows, and the recursive member which repeatedly joins back to the CTE until no new rows are added. For a manager hierarchy, the anchor selects the root manager, and each recursive step finds direct reports of everyone already in the result. You can track depth by incrementing a counter each iteration — useful for indentation or cycle detection."

---

## Watch Out For
- **Cycles**: if manager A reports to B and B reports to A, the recursion loops forever. Guard with a `depth < 100` or path deduplication check.
- Not all databases use `WITH RECURSIVE` syntax — Oracle uses `CONNECT BY PRIOR`, but the concept is the same.
- PostgreSQL, MySQL 8+, SQL Server, BigQuery, Snowflake all support standard `WITH RECURSIVE`.

---

## Key Concepts Tested
- Recursive CTE structure (anchor + recursive member)
- Hierarchical data traversal (org charts, bill of materials, folder trees)
- Depth tracking
- Cycle guard
