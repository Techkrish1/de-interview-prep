# Data File Formats — Parquet vs ORC vs Avro vs JSON

**Type:** Theoretical
**Topic:** File Formats, Columnar Storage, Schema Evolution, Compression

---

## The Question
> "Compare data file formats — Parquet, ORC, Avro, and JSON. When would you use each and why is Parquet the default for analytics?"

---

## Row vs Columnar — The Core Distinction

```
Row-oriented (JSON, Avro):
  Row 1: [id=1, name="Alice", amount=200, country="IN"]
  Row 2: [id=2, name="Bob",   amount=150, country="US"]

Columnar (Parquet, ORC):
  id:      [1, 2, 3]
  amount:  [200, 150, 350]
  country: ["IN", "US", "IN"]
```

**Query:** `SELECT SUM(amount) FROM orders WHERE country = 'IN'`

```
Row format:  reads ALL columns for every row → 100% of data
Columnar:    reads only 'amount' + 'country' → ~15% of data
```

Columnar wins for analytics. Row wins for write-heavy and full-record operations.

---

## Parquet

Columnar, binary, self-describing (schema embedded in footer).

**Why it dominates analytics:**
- **Column pruning** — reads only columns in SELECT
- **Predicate pushdown** — row group min/max stats let Spark skip irrelevant chunks
- **Compression** — columnar layout compresses far better (similar values together)
- **Splittable** — multiple Spark tasks read one file in parallel

**Row group predicate pushdown:**
```
orders.parquet
  Row Group 1: amount min=10,  max=95    → WHERE amount > 1000: SKIP entire group
  Row Group 2: amount min=500, max=2000  → WHERE amount > 1000: READ
  Row Group 3: amount min=1,   max=800   → WHERE amount > 1000: SKIP entire group
```

```python
df.write.parquet("s3://bucket/orders")                   # default Snappy
df.write.option("compression", "gzip").parquet("...")    # higher ratio, slower
```

**Use for:** analytics tables, data lake, Spark/Hive/BigQuery/Athena — all native Parquet.

---

## ORC

Columnar, binary — originally from the Hive ecosystem. Similar capabilities to Parquet (predicate pushdown, compression, splittable). ORC slightly faster in Hive; Parquet better supported across the broader ecosystem.

**Use for:** Hive-heavy or legacy Hadoop stacks. Prefer Parquet in new systems.

---

## Avro

Row-oriented, binary, schema stored as JSON in file header.

**Key strength — schema evolution:**
```json
{"type": "record", "name": "Order", "fields": [
  {"name": "id",     "type": "int"},
  {"name": "amount", "type": "double"},
  {"name": "status", "type": ["null", "string"], "default": null}
]}
```

| Change | Compatibility |
|---|---|
| Add field with default | Backward compatible |
| Remove field with default | Forward compatible |
| Change field type | Breaking |

Kafka + Confluent Schema Registry use Avro by default — consumers auto-negotiate schema versions.

**Use for:** Kafka messages, event streaming, write-heavy append logs, anywhere schema evolves frequently.

---

## JSON

Row-oriented, text, human-readable. No binary encoding, no column pruning, no predicate pushdown. Schema must be inferred. Poor compression. Not splittable without JSON Lines.

**Use for:** REST API responses, config files, small datasets. Never as a storage format for large analytical tables.

---

## Comparison

| | Parquet | ORC | Avro | JSON |
|---|---|---|---|---|
| Orientation | Columnar | Columnar | Row | Row |
| Format | Binary | Binary | Binary | Text |
| Schema | Embedded | Embedded | Header | Inferred |
| Schema evolution | Limited | Limited | Excellent | None |
| Analytics speed | Excellent | Excellent | Poor | Poor |
| Write speed | Good | Good | Excellent | Good |
| Ecosystem | Universal | Hive/Hadoop | Kafka/Streaming | APIs |
| Compression | Excellent | Excellent | Good | Poor |

---

## How to Say It in the Interview
> "The core split is row vs columnar. Columnar formats like Parquet only read the columns your query needs — huge win for analytics where you select 3 of 50 columns. They compress better because similar values are stored together. Parquet adds row group statistics for predicate pushdown — a filter on amount can skip entire file sections without reading them. That's why it's the default for data lake analytics.
>
> Avro is row-oriented but excels at schema evolution — Kafka uses it with Schema Registry for exactly this reason. JSON is fine for APIs but a poor storage format: no binary encoding, no column pruning, poor compression. If I see JSON files in a data lake I'd convert them to Parquet."

---

## Follow-ups & Answers

**"Which compression codec for Parquet?"**
> Snappy (default) — fast decompress, moderate ratio, good for analytics. GZIP — better ratio, slower, good for archival. ZSTD (Spark 3+) — strong middle ground, better than Snappy, faster than GZIP.

**"Can you add a column to a Parquet file without rewriting?"**
> Not directly — schema is in the file footer. Delta Lake handles this with `mergeSchema=true`, tracking schema evolution across files via its transaction log.

**"Why does Kafka use Avro instead of Parquet?"**
> Kafka writes individual records one at a time. Parquet is designed for large batch writes (128MB row groups) — inefficient for single-record streams. Avro writes records efficiently one-by-one, and its Schema Registry gives consumers automatic schema version negotiation.

---

## Common Mistakes
- Saying "Parquet is faster" without explaining column pruning + predicate pushdown
- Not knowing Avro is row-oriented
- Recommending JSON as a data lake storage format
- Not knowing ORC and Parquet are roughly equivalent; ORC is just Hive-native

---

## Key Concepts Tested
- Row vs columnar — when each wins
- Parquet: column pruning, row group stats, predicate pushdown, compression
- Avro: schema evolution, Kafka/streaming
- JSON: never a production analytics storage format
- Compression codecs: Snappy vs GZIP vs ZSTD
