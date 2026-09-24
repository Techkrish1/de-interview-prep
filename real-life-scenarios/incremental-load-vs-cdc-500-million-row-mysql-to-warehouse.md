# How Would You Sync a 500-Million-Row MySQL Table to a Data Warehouse Incrementally?

**Type:** Real-life Scenario
**Topic:** Incremental Loading, CDC, Delta Lake MERGE

---

## The Question
> "You have a MySQL production database with a 500-million-row orders table. It receives about 1 million inserts and updates every day. You need to sync this data into your data warehouse for analytics. How would you design the pipeline?"

---

## Two Strategies — Know Both

| Strategy | How it works | Captures Deletes? | DB Load |
|---|---|---|---|
| Watermark-based incremental | Query rows where `updated_at > last_run_time` | No | Medium |
| CDC (Change Data Capture) | Read MySQL binary log via Debezium | Yes | Zero |

---

## Strategy 1 — Watermark-based Incremental Load

**Flow:**
```
1. Read last_processed_timestamp from metadata table
2. SELECT * FROM orders WHERE updated_at > last_processed_timestamp
3. Upsert into warehouse (Delta MERGE)
4. Update last_processed_timestamp
```

**PySpark implementation:**
```python
# Read last watermark
last_ts = spark.read.table("metadata.pipeline_state") \
               .filter("pipeline = 'orders'") \
               .select("last_processed_ts").collect()[0][0]

# Incremental extract from MySQL
new_data = spark.read.jdbc(
    url=jdbc_url,
    table="orders",
    properties=conn_props
).filter(F.col("updated_at") > last_ts)

# Upsert into Delta Lake
from delta.tables import DeltaTable

delta_table = DeltaTable.forName(spark, "warehouse.orders")

delta_table.alias("target").merge(
    new_data.alias("source"),
    "target.order_id = source.order_id"
).whenMatchedUpdateAll() \
 .whenNotMatchedInsertAll() \
 .execute()

# Advance watermark
spark.sql("UPDATE metadata.pipeline_state SET last_processed_ts = now() WHERE pipeline = 'orders'")
```

**Key limitation:** Does not capture hard deletes. If a row is deleted from MySQL, the warehouse still has it.

---

## Strategy 2 — CDC via Debezium + Kafka (Production Standard)

**Architecture:**
```
MySQL binlog
     │
     ▼
 Debezium (Kafka Connect)   ← reads binlog, zero DB load
     │
     ▼
  Kafka topic: orders.changes
     │
     ▼
  Flink / Spark Streaming   ← processes CDC events
     │
     ▼
  Delta Lake / Snowflake    ← upserted, accurate table
```

**What a CDC event looks like:**
```json
{
  "op": "u",
  "before": { "order_id": 101, "status": "pending" },
  "after":  { "order_id": 101, "status": "shipped" },
  "ts_ms": 1700000000000
}
```
- `op: c` = insert, `op: u` = update, `op: d` = delete, `op: r` = snapshot read

**Why CDC beats watermark:**
- Captures deletes
- Zero extra load on source DB — reads the binlog, not the table
- Real-time — events flow as they happen
- Full change history — every version of a row is recorded

---

## Warehouse-Side Upsert — Delta Lake MERGE

```python
delta_table.alias("t").merge(
    incoming.alias("s"),
    "t.order_id = s.order_id"
).whenMatchedUpdate(
    condition="s.op != 'd'",
    set={"status": "s.status", "updated_at": "s.updated_at"}
).whenMatchedDelete(
    condition="s.op = 'd'"
).whenNotMatchedInsert(
    condition="s.op != 'd'",
    values={"order_id": "s.order_id", "status": "s.status"}
).execute()
```

---

## How to Say It in the Interview
> "I'd first push back on a nightly full load — at 500 million rows that's expensive and slow. The right approach depends on whether the source table has a reliable `updated_at` timestamp and whether we need to capture deletes.
>
> If `updated_at` is reliable and deletes don't matter, watermark-based incremental load works — query only rows updated since last run, upsert using Delta Lake MERGE.
>
> For production, CDC via Debezium is the gold standard. It reads MySQL's binary log — zero load on the source, captures every insert, update, and delete in real time, streams through Kafka, and the warehouse side applies changes via MERGE."

---

## Follow-ups & Answers

**"What if the table has no `updated_at` column?"**
> You're forced to use CDC — no reliable way to detect changes without a timestamp. Full daily diff (hash all rows) works but is very expensive.

**"How do you handle schema changes?"**
> Watermark: schema changes break the pipeline — manual fix needed.
> CDC + Schema Registry (Avro/Protobuf): Debezium detects evolution, publishes new schema version, consumers adapt automatically.

**"What is SCD Type 2 and when does it apply?"**
> SCD (Slowly Changing Dimension) Type 2 keeps full history of changes with `valid_from`/`valid_to` columns. Applies to dimension tables (customers, products) where you need historical accuracy. For fact tables like orders, a straight upsert is usually sufficient.

---

## Common Mistakes
- Proposing nightly full load for a 500M row table
- Not mentioning that watermark misses deletes
- Not knowing Debezium or CDC tools
- Not explaining the MERGE/upsert pattern on the warehouse side
- Ignoring schema evolution

---

## Key Concepts Tested
- Incremental loading: watermark vs CDC
- Change Data Capture: Debezium, Kafka Connect, MySQL binlog
- Delta Lake MERGE / upsert
- Handling inserts, updates, and deletes
- Schema evolution with Schema Registry
- SCD Type 1 vs Type 2
