# What is dbt and How Does It Fit in the Modern Data Stack?

**Type:** Theoretical
**Topic:** dbt, Data Transformation, Modern Data Stack

---

## The Question
> "What is dbt? How does it fit into a modern data stack, and what problems does it solve?"

---

## What dbt Is

dbt (data build tool) is a **transformation framework** that runs SQL inside your data warehouse. It handles the T in ELT.

```
Raw data in warehouse → dbt models (SQL SELECT) → Transformed tables/views
```

You write `SELECT` statements. dbt handles:
- Materializing them as tables or views
- Ordering execution via dependency graph
- Running tests
- Generating documentation

---

## The Modern Data Stack

```
Source Systems
      ↓
Fivetran / Airbyte (Extract + Load)
      ↓
Data Warehouse: Snowflake / BigQuery / Redshift / Databricks
      ↓
dbt (Transform — SQL SELECT statements)
      ↓
BI Tool: Tableau / Looker / Metabase
```

dbt operates entirely inside the warehouse — no separate compute cluster to manage.

---

## Core Concepts

### Models
A model = a `.sql` file with a single `SELECT` statement.

```sql
-- models/marts/fct_orders.sql
SELECT
    o.order_id,
    o.customer_id,
    o.order_date,
    SUM(oi.quantity * oi.unit_price) AS total_amount
FROM {{ ref('stg_orders') }} o
JOIN {{ ref('stg_order_items') }} oi USING (order_id)
GROUP BY 1, 2, 3
```

`{{ ref('stg_orders') }}` tells dbt about the dependency — it builds the DAG automatically.

### Materializations

| Type | What it creates | When to use |
|---|---|---|
| `view` | A SQL view | Lightweight, always fresh |
| `table` | A full table (truncate + reload) | Expensive but fast to query |
| `incremental` | Append/merge only new rows | Large tables — only process new data |
| `ephemeral` | Inlined as CTE, never persisted | Intermediate logic you don't need to store |

### Incremental models
```sql
-- models/marts/fct_events.sql
{{ config(materialized='incremental', unique_key='event_id') }}

SELECT * FROM {{ ref('stg_events') }}
{% if is_incremental() %}
WHERE event_timestamp > (SELECT MAX(event_timestamp) FROM {{ this }})
{% endif %}
```

First run: full load. Every subsequent run: only new rows since last max timestamp.

### Tests
```yaml
# schema.yml
models:
  - name: fct_orders
    columns:
      - name: order_id
        tests:
          - unique
          - not_null
      - name: customer_id
        tests:
          - not_null
          - relationships:
              to: ref('dim_customers')
              field: customer_id
```

Run `dbt test` — fails immediately if data quality breaks.

### Lineage
dbt auto-generates a DAG from `ref()` dependencies. You get a visual lineage graph showing exactly which models depend on which.

---

## Why It Matters (What Problem It Solves)

**Before dbt:** transformations lived in stored procedures, ad-hoc scripts, or ETL tool GUIs — no version control, no tests, no documentation, hard to understand dependencies.

**With dbt:** transformations are code — in git, tested, documented, lineage tracked.

---

## How to Say It in the Interview
> "dbt is a SQL-first transformation framework that runs inside your data warehouse. You write SELECT statements — dbt materializes them as tables or views, figures out the execution order from ref() dependencies, runs data quality tests, and generates lineage documentation. It's the de-facto T in modern ELT stacks where you load raw data first (via Fivetran or Airbyte) and transform it in-warehouse. The big value is that transformations are now code — version controlled, tested, and self-documenting."

---

## Follow-ups & Answers

**"How does dbt handle incremental loads?"**
> Incremental models use `is_incremental()` to add a filter on the first run vs. subsequent runs. You define a `unique_key` for upsert — dbt generates a MERGE statement on supported warehouses. Each full run only processes rows since the last watermark.

**"What's the difference between dbt Core and dbt Cloud?"**
> dbt Core is open-source CLI — you schedule it yourself (Airflow, cron). dbt Cloud is a managed platform — hosted IDE, built-in scheduler, CI/CD, observability. Most teams use Core in production orchestrated by Airflow.

**"How do you test data quality in dbt?"**
> Built-in generic tests: `unique`, `not_null`, `accepted_values`, `relationships`. For custom logic: singular tests — just a SQL file that returns rows only when there's a failure (empty result = test passes).

---

## Common Mistakes
- Saying dbt does extraction or loading — it only transforms
- Not knowing that dbt runs SQL inside the warehouse (no separate compute)
- Confusing `table` and `incremental` — tables truncate and reload fully each run

---

## Key Concepts Tested
- Where dbt fits in the stack (T in ELT)
- Models, ref(), materialization types
- Incremental models with watermarks
- dbt tests for data quality
- Version control and lineage as key benefits
