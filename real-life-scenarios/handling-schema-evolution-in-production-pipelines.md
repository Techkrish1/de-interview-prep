# How Do You Handle Schema Evolution in a Production Data Pipeline?

**Type:** Real-life Scenario
**Topic:** Schema Evolution, Delta Lake, Avro, Breaking Changes

---

## The Question
> "A source system added a new column and removed an old one. Your downstream pipeline breaks. How do you prevent and handle schema evolution in production?"

---

## Why It's a Real Problem

```
Day 1 schema: orders(order_id, customer_id, amount, status)
Day 30:       orders(order_id, customer_id, amount, status, discount_pct)  ← new col
Day 60:       orders(order_id, customer_id, total_amount, status)          ← renamed
```

Without schema management, pipelines fail with `AnalysisException: cannot resolve column`.

---

## Types of Schema Changes

| Change | Impact |
|---|---|
| Add column with default | Non-breaking (safe) |
| Remove column | Breaking — downstream readers fail |
| Rename column | Breaking — looks like remove + add |
| Change data type | Breaking (e.g., INT → STRING may work; STRING → INT fails on non-numeric) |
| Reorder columns | Breaking for positional readers |

---

## Defense Layer 1 — Schema Registry (Kafka / Avro)

For streaming sources, use Confluent Schema Registry — producers must register schema changes; backward/forward compatibility is enforced before a message is published.

```python
# Producer must register new schema — registry rejects breaking changes
schema_registry_client.register("orders-value", new_schema)
# If incompatible → raises SchemaRegistryError before any message is sent
```

Compatibility modes:
- `BACKWARD`: new schema can read old data (safe to add optional fields)
- `FORWARD`: old schema can read new data
- `FULL`: both directions
- `NONE`: anything goes (dangerous)

---

## Defense Layer 2 — Schema-on-Read with Explicit Selection

Never use `SELECT *` in production pipelines. Explicitly name every column.

```python
# Fragile:
df = spark.read.parquet("s3://orders")   # schema inferred, breaks on change

# Resilient:
schema = StructType([
    StructField("order_id",    LongType(),   nullable=False),
    StructField("customer_id", LongType(),   nullable=False),
    StructField("amount",      DoubleType(), nullable=True),
])
df = spark.read.schema(schema).parquet("s3://orders")
# New columns in source are simply ignored
# Removed columns → null (if nullable) or error (if not null)
```

---

## Defense Layer 3 — Delta Lake Schema Evolution

Delta Lake tracks schema in its transaction log. You can opt into automatic schema evolution:

```python
# Merge new columns automatically:
df.write \
  .format("delta") \
  .option("mergeSchema", "true") \
  .mode("append") \
  .save("s3://delta/orders")
```

Or enforce schema strictly and alert on any change:
```python
df.write \
  .format("delta") \
  .option("mergeSchema", "false")   # default — fails if schema doesn't match
  .mode("append") \
  .save("s3://delta/orders")
# Raises AnalysisException if source adds a column → alerts, investigated before data lands
```

---

## Handling a Breaking Change in Production

```
Breaking change detected (pipeline fails or alert fires)
         │
1. Quarantine new data — don't let bad schema corrupt the table
         │
2. Assess the change:
   - New column added? → add nullable column to downstream schema with default
   - Column removed?   → check if downstream uses it; if yes, get data from source or use last-known
   - Column renamed?   → add alias / mapping in ingestion layer
   - Type changed?     → CAST in transformation with fallback on parse error
         │
3. Update schema in all affected layers (ingestion → transform → serving)
         │
4. Backfill if needed — reprocess historical data with new schema
         │
5. Update schema registry / contract with source team
```

---

## Schema Contract (Proactive)

The best defense: agree on schema contracts with upstream teams before changes happen.

```yaml
# schema_contract.yaml
table: orders
version: 2
required_columns:
  - name: order_id    type: BIGINT   nullable: false
  - name: customer_id type: BIGINT   nullable: false
  - name: amount      type: DOUBLE   nullable: true
optional_columns:
  - name: discount_pct type: DOUBLE  nullable: true
breaking_change_notice: 14 days
```

---

## How to Say It in the Interview
> "Schema evolution is one of the most common sources of production pipeline failures. My layered approach: first, use a Schema Registry for Kafka sources to enforce backward compatibility before bad schemas reach the pipeline. Second, always define schemas explicitly — never SELECT * in production. Third, use Delta Lake with mergeSchema=true for additive changes, and fail-fast mode to catch removals or renames before data is corrupted. And proactively, establish schema contracts with upstream teams — a 14-day notice before breaking changes gives time to update all downstream consumers before the change goes live."

---

## Common Mistakes
- Using `SELECT *` or inferred schemas in production
- No alerting when schema changes — silent corruption
- Not distinguishing additive vs breaking changes
- Not having a backfill plan when a schema fix requires historical reprocessing

---

## Key Concepts Tested
- Types of schema changes and which are breaking
- Schema Registry for streaming (Kafka/Avro)
- Delta Lake mergeSchema vs strict enforcement
- Explicit schema definition in Spark
- Schema contracts with upstream teams
