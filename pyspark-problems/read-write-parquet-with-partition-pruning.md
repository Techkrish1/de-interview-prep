# Read and Write Parquet Efficiently with Partition Pruning in PySpark

**Type:** PySpark Problem
**Topic:** Parquet, Partitioning, Partition Pruning

---

## The Question
> "How do you read and write Parquet files in PySpark? What is partition pruning and how does it improve performance?"

---

## Writing with Partitioning

```python
# Partition by low-cardinality column used in filters
df.write \
  .format("parquet") \
  .partitionBy("year", "month") \
  .mode("overwrite") \
  .save("s3://bucket/orders/")

# Results in:
# s3://bucket/orders/year=2024/month=01/part-0000.parquet
#                              month=02/part-0000.parquet
#                   year=2023/month=12/part-0000.parquet
```

---

## Reading with Partition Pruning

```python
# Without filter — scans ALL partitions (slow)
df = spark.read.parquet("s3://bucket/orders/")

# With filter — Spark opens ONLY matching folders ✅
df = spark.read.parquet("s3://bucket/orders/") \
          .filter("year = 2024 AND month = 1")

# Verify pruning worked
df.explain()
# Look for: PartitionFilters: [(year = 2024), (month = 1)]
```

**Impact:** 3-year table, queried for 1 month → reads 1/36 of the data → 36x cheaper.

---

## Good vs Bad Partition Columns

| Good | Bad |
|---|---|
| `date`, `year`, `month`, `country` | `user_id`, `order_id` (millions of tiny files) |
| Low cardinality, used in WHERE | High cardinality, rarely filtered |

---

## Parquet vs Other Formats

| Format | Type | Best for |
|---|---|---|
| **Parquet** | Columnar | Analytics — fast column reads, high compression |
| **ORC** | Columnar | Hive ecosystem |
| **Avro** | Row-based | Kafka/streaming, full row reads |
| **CSV/JSON** | Row-based | Small files, human-readable only |

---

## Schema Enforcement on Read

```python
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

schema = StructType([
    StructField("order_id", StringType(), False),
    StructField("amount",   DoubleType(), True),
])
df = spark.read.schema(schema).parquet("s3://bucket/orders/")
```

---

## How to Say It in the Interview
> "I write Parquet with `partitionBy` on low-cardinality columns used in filters — typically date or month. This creates a folder hierarchy on S3. When reading with a filter on those columns, Spark prunes partitions — opens only matching folders, skips the rest. For a 3-year dataset filtered to 1 month, that's 36x less data scanned. I always verify with `explain()` and look for `PartitionFilters` in the plan."

---

## Follow-ups & Answers

**"Partition pruning vs predicate pushdown — difference?"**
> Partition pruning skips entire folders at the filesystem level. Predicate pushdown pushes filters into the Parquet reader — skips row groups within a file using min/max statistics. Both reduce data read, at different levels.

**"High-cardinality partition column problem?"**
> Creates millions of tiny folders — small files problem. S3 path listing is slow, per-file overhead is high. Partition by date, use bucketing by high-cardinality key if needed.

---

## Common Mistakes
- Partitioning by `user_id` or `order_id` — small files problem
- Not verifying partition pruning with `explain()`
- Using CSV at scale instead of Parquet

---

## Key Concepts Tested
- `partitionBy` in writes
- Partition pruning and verification with explain()
- Good vs bad partition columns
- Predicate pushdown vs partition pruning
- Parquet vs ORC vs Avro
