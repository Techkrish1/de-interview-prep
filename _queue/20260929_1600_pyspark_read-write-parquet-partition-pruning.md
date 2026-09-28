---
publish_at: "2026-09-29T10:30:00Z"
folder: pyspark-problems
filename: read-write-parquet-with-partition-pruning.md
title: Read and write Parquet efficiently with partition pruning in PySpark
---

# Read and Write Parquet Efficiently with Partition Pruning in PySpark

**Type:** PySpark Problem
**Topic:** Parquet, Partitioning, Partition Pruning, File Formats

---

## The Question
> "How do you read and write Parquet files in PySpark? What is partition pruning and how does it improve performance?"

---

## Writing Parquet — Best Practices

```python
# Basic write
df.write.format("parquet").mode("overwrite").save("s3://bucket/orders/")

# Write with partitioning — ALWAYS partition large tables
df.write \
  .format("parquet") \
  .partitionBy("year", "month")   \   # creates folder: year=2024/month=01/
  .mode("overwrite") \
  .save("s3://bucket/orders/")

# Control number of output files per partition
df.repartition(4, "year", "month") \
  .write.format("parquet") \
  .partitionBy("year", "month") \
  .mode("overwrite") \
  .save("s3://bucket/orders/")
```

**Resulting S3 structure:**
```
s3://bucket/orders/
├── year=2024/
│   ├── month=01/
│   │   ├── part-0000.parquet
│   │   └── part-0001.parquet
│   └── month=02/
│       └── part-0000.parquet
└── year=2023/
    └── month=12/
        └── part-0000.parquet
```

---

## Reading Parquet — With and Without Partition Pruning

```python
# Read ALL data — no pruning (slow for large datasets)
df = spark.read.parquet("s3://bucket/orders/")

# Read with filter — Spark prunes partitions automatically ✅
df = spark.read.parquet("s3://bucket/orders/") \
          .filter("year = 2024 AND month = 1")

# Verify pruning happened
df.explain()
# Look for: PartitionFilters: [isnotnull(year), (year = 2024), (month = 1)]
```

**What partition pruning does:**
Instead of reading all partitions (every `year=*/month=*/` folder), Spark reads **only** the matching folders. For a 3-year table queried for 1 month, this means reading `1/36` of the data.

---

## Partition Pruning — Visual

```
Without filter:
Spark reads ALL 36 folders ──► scan 36 × 500MB = 18GB

With filter (year=2024, month=1):
Spark reads ONLY 1 folder  ──► scan 1 × 500MB = 500MB
                                → 36x faster, 36x cheaper
```

---

## Choosing the Right Partition Column

| Good partition columns | Bad partition columns |
|---|---|
| Low-cardinality: `date`, `year`, `month`, `country`, `status` | High-cardinality: `user_id`, `order_id` (millions of tiny folders) |
| Frequently used in WHERE filters | Rarely queried |
| Even distribution across values | Highly skewed (e.g., 90% rows have `country='US'`) |

**Rule of thumb:** Partition by the column most often used in your WHERE/filter clauses.

---

## Parquet vs Other Formats

| Format | Encoding | Best for | Compression |
|---|---|---|---|
| **Parquet** | Columnar | Analytics, OLAP — read subsets of columns fast | Snappy, Gzip, Zstd |
| **ORC** | Columnar | Hive ecosystem, predicate pushdown | Zlib, Snappy |
| **Avro** | Row-based | Streaming, Kafka, full row reads | Deflate, Snappy |
| **CSV/JSON** | Row-based | Human-readable, small files | None |

**Use Parquet for data lakes.** Use Avro for Kafka/streaming. Never use CSV in production at scale.

---

## Schema Enforcement on Read

```python
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType

schema = StructType([
    StructField("order_id",  StringType(),  False),
    StructField("amount",    DoubleType(),  True),
    StructField("status",    StringType(),  True),
])

# Enforce schema — rejects files with wrong types
df = spark.read.schema(schema).parquet("s3://bucket/orders/")
```

---

## How to Say It in the Interview
> "I write Parquet with `partitionBy` on low-cardinality columns used in filters — typically date or month. This creates a folder hierarchy like `year=2024/month=01/` on S3. When reading with a filter on those columns, Spark prunes partitions — it only opens the matching folders, skipping the rest entirely. For a 3-year dataset filtered to 1 month, that's 36x less data scanned. I always verify pruning worked by checking `explain()` for `PartitionFilters` in the physical plan."

---

## Follow-ups & Answers

**"What is predicate pushdown — how is it different from partition pruning?"**
> Partition pruning skips entire folders/partitions at the file-system level. Predicate pushdown pushes filters into the Parquet reader — it reads only the row groups within a file that match the filter (using Parquet column statistics: min/max per row group). Both reduce data read, but at different levels.

**"What happens if you partition by a high-cardinality column like user_id?"**
> Creates millions of tiny folders — each with 1-2 small files. This is the "small files problem": listing millions of S3 paths is slow, and reading many tiny Parquet files has high per-file overhead. Solution: partition by date, and within each partition use bucketing by user_id if needed.

**"What is `coalesce` vs `repartition` when writing?"**
> `repartition(n)` shuffles data to create exactly n even partitions (full shuffle). `coalesce(n)` reduces partitions without a full shuffle but can create uneven file sizes. Use `repartition` before writing for even file sizes; `coalesce` only when reducing and imbalance is acceptable.

---

## Common Mistakes
- Partitioning by high-cardinality columns (user_id, order_id) — creates small files problem
- Not verifying partition pruning with `explain()` — assuming it happened
- Mixing `repartition` and `partitionBy` semantics
- Writing CSV/JSON at scale instead of Parquet

---

## Key Concepts Tested
- Parquet format and columnar storage advantages
- `partitionBy` in PySpark writes
- Partition pruning — how it works and how to verify
- Predicate pushdown
- Good vs bad partition columns
- Parquet vs ORC vs Avro vs CSV
