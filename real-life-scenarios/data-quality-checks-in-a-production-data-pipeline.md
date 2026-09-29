# How Do You Implement Data Quality Checks in a Production Data Pipeline?

**Type:** Real-life Scenario
**Topic:** Data Quality, dbt tests, Great Expectations, PySpark assertions

---

## The Question
> "How do you implement data quality checks in a production data pipeline? What kinds of checks do you run and where do you run them?"

---

## Three Layers of DQ Checks

```
Source Data → [Layer 1: Ingestion Checks] → Raw Zone
                                               ↓
                               [Layer 2: Transformation Checks]
                                               ↓
                              Curated Zone → [Layer 3: Output Checks] → BI / ML
```

---

## Layer 1 — Ingestion / Schema Checks

Run before writing to the lake.

```python
def validate_schema(df, expected_cols):
    missing = set(expected_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

def row_count_check(df, min_rows=1000):
    count = df.count()
    if count < min_rows:
        raise ValueError(f"Only {count} rows — expected >= {min_rows}")
```

| Check | Why |
|---|---|
| Schema match (column names + types) | Source schema changes silently break downstream |
| Null rate on critical columns | `customer_id IS NULL` should never happen |
| Row count vs yesterday ± 20% | Catches silent upstream data drops |
| Duplicate primary keys | Idempotent ingestion may double-insert |

---

## Layer 2 — Transformation Checks

**In dbt:**
```yaml
# schema.yml
models:
  - name: fct_orders
    columns:
      - name: order_id
        tests: [unique, not_null]
      - name: total_amount
        tests:
          - dbt_utils.accepted_range:
              min_value: 0
              max_value: 100000
      - name: status
        tests:
          - accepted_values:
              values: ['pending', 'completed', 'cancelled']
```

**In PySpark:**
```python
def assert_no_nulls(df, col_name):
    null_count = df.filter(df[col_name].isNull()).count()
    assert null_count == 0, f"{col_name} has {null_count} nulls"

def assert_positive(df, col_name):
    neg = df.filter(df[col_name] < 0).count()
    assert neg == 0, f"{col_name} has {neg} negative values"
```

---

## Layer 3 — Output / Business Rule Checks

```python
# Revenue today must be within 30% of 7-day average
today_rev  = df.filter(df.date == today).agg(sum("revenue")).collect()[0][0]
avg_7d_rev = df.filter(df.date >= today - 7).agg(avg("revenue")).collect()[0][0]

if abs(today_rev - avg_7d_rev) / avg_7d_rev > 0.30:
    raise ValueError(f"Revenue {today_rev} deviates >30% from 7-day avg {avg_7d_rev}")
```

```sql
-- Referential integrity: every order must have a valid customer
SELECT COUNT(*) FROM fct_orders o
LEFT JOIN dim_customers c ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL
-- Must return 0
```

---

## What to Do When a Check Fails

```
Check fails
     ↓
Log failure with details (which check, row count, example bad rows)
     ↓
Alert (PagerDuty / Slack)
     ↓
Route bad data to quarantine table — don't drop it
     ↓
Block downstream pipeline tasks
     ↓
Fix at source or apply transformation-side repair, then reprocess quarantine
```

**Quarantine pattern:**
```python
good_rows = df.filter(df.amount >= 0)
bad_rows  = df.filter(df.amount < 0)

good_rows.write.parquet("s3://curated/orders")
bad_rows.write.parquet("s3://quarantine/orders")
```

---

## Tools

| Tool | Layer | What It Does |
|---|---|---|
| dbt tests | Transformation | Declarative YAML tests on model columns |
| Great Expectations | Any | Python-native DQ expectations with HTML reports |
| Soda Core | Any | SQL-based DQ checks with alerting |
| PySpark assertions | Ingestion/Transform | Custom checks in pipeline code |
| Airflow sensors | Orchestration | Block downstream tasks on DQ failure |

---

## How to Say It in the Interview
> "I implement DQ in three layers. At ingestion: schema consistency, null rates on key columns, row count anomalies. During transformation: dbt tests or PySpark assertions for nulls, range checks, referential integrity. At the output layer: statistical checks like revenue deviating 30% from the 7-day average. When a check fails, bad rows go to a quarantine table, an alert fires, and downstream tasks are blocked. Good rows still flow through — you don't block everything for one bad batch."

---

## Follow-ups & Answers

**"What is Great Expectations?"**
> Python DQ framework — you define expectations like `expect_column_values_to_not_be_null("customer_id")` and run them as a validation suite. Integrates with Airflow and dbt. Generates HTML data quality reports.

**"How do you handle a DQ failure mid-pipeline without losing upstream work?"**
> Quarantine bad records, alert, block downstream tasks. Clean records still flow. Once fixed, reprocess only the quarantined batch — not the full pipeline.

**"Difference between DQ checks and data validation?"**
> Validation = schema/type/format/range correctness. Quality = broader: freshness (arriving on time?), completeness (all rows present?), consistency (matches another source?), accuracy. Validation is a subset of quality.

---

## Common Mistakes
- Checking only one layer — schema OR business rules, not both
- Silently dropping bad records instead of quarantining
- Not alerting — pipeline succeeds but dashboards show wrong numbers
- Blocking the full pipeline for one bad record — quarantine and continue

---

## Key Concepts Tested
- Multi-layer DQ strategy
- Null, uniqueness, range, referential integrity checks
- Quarantine pattern
- dbt tests + Great Expectations
- Pipeline blocking vs graceful degradation
