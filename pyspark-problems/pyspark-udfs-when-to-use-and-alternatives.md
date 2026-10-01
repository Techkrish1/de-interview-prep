# PySpark UDFs — When to Use and Why to Avoid Them

**Type:** PySpark Problem
**Topic:** UDFs, Pandas UDFs, Performance, Catalyst Optimization

---

## The Question
> "When would you use a PySpark UDF? Why should you avoid them and what are the alternatives?"

---

## What a UDF Is

```python
from pyspark.sql import functions as F
from pyspark.sql.types import StringType

def categorize_amount(amount):
    if amount < 100:   return "low"
    elif amount < 500: return "medium"
    else:              return "high"

udf_categorize = F.udf(categorize_amount, StringType())
df = df.withColumn("tier", udf_categorize(df.amount))
```

---

## Why UDFs Are Slow — The Python-JVM Boundary

Spark runs on the JVM. Your Python UDF runs in a separate Python process. For **every row**:

```
JVM → serialize row to pickle → send to Python worker
Python runs function
Python → serialize result → send back to JVM → deserialize
```

```
No UDF:  10M rows, native JVM function   → ~2 seconds
With UDF: 10M rows, row-by-row pickle    → ~40 seconds
```

UDFs also **break Catalyst optimization** — Spark cannot inspect Python bytecode to apply predicate pushdown, column pruning, or code generation.

---

## Pandas UDFs — Vectorized Alternative

Operate on Arrow column batches instead of row-by-row. 10–100× faster than row-by-row UDFs.

```python
from pyspark.sql.functions import pandas_udf
import pandas as pd

@pandas_udf(StringType())
def categorize_amount(amounts: pd.Series) -> pd.Series:
    return amounts.apply(
        lambda x: "low" if x < 100 else ("medium" if x < 500 else "high")
    )

df = df.withColumn("tier", categorize_amount(df.amount))
```

Apache Arrow serializes entire column batches at once — no per-row pickle overhead.

---

## Best Alternative — Native Spark Functions

Stay entirely in JVM, fully Catalyst-optimized, no Python involved.

```python
# UDF (slow):
udf_fn = F.udf(lambda x: "low" if x < 100 else "medium" if x < 500 else "high", StringType())

# Native (fast):
df.withColumn("tier",
    F.when(df.amount < 100, "low")
     .when(df.amount < 500, "medium")
     .otherwise("high")
)
```

| Task | Native alternative |
|---|---|
| Conditional logic | `F.when().otherwise()` |
| String ops | `F.regexp_replace`, `F.substring`, `F.concat` |
| Date math | `F.datediff`, `F.date_add`, `F.date_format` |
| JSON parsing | `F.from_json`, `F.get_json_object` |
| Math | `F.round`, `F.log`, `F.sqrt` |

---

## Decision Tree

```
Need custom logic on a column?
  │
  ├── Express with F.when / F.regexp / built-ins?  → use native (fastest)
  │
  ├── Batch numeric/string ops with pandas/numpy?  → Pandas UDF
  │
  └── Complex Python / external library?
        └── Use UDF — or mapPartitions for expensive init
```

### `mapPartitions` — Expensive Initialization

Load a model or open a connection once per partition, not per row:

```python
def score_partition(rows):
    model = load_model("s3://models/fraud_v2")   # once per partition
    for row in rows:
        yield row + (model.predict(row.features),)

df.rdd.mapPartitions(score_partition).toDF(schema)
```

---

## How to Say It in the Interview
> "UDFs cross the Python-JVM boundary on every row — Spark serializes to pickle, sends to a Python worker, runs the function, serializes back. They also break Catalyst optimization. My first choice is always native Spark functions — F.when, F.regexp_replace, F.datediff — they stay in JVM and Catalyst can optimize them. When I genuinely need Python, Pandas UDFs use Apache Arrow to process column batches at once — 10–100× faster than row-by-row. A raw UDF is a last resort. If it needs to initialize something expensive like a model, I'd use mapPartitions to do that once per partition."

---

## Follow-ups & Answers

**"What is Apache Arrow?"**
> Columnar in-memory format for zero-copy data exchange between JVM and Python — basis of Pandas UDF performance. Eliminates per-row pickle serialization.

**"Can you register a UDF for SQL?"**
> `spark.udf.register("categorize", fn, StringType())` then `spark.sql("SELECT categorize(amount) FROM orders")`. Same performance penalty applies.

**"What about Scala UDFs?"**
> Run on the JVM directly — no serialization boundary, integrated with Catalyst code generation. Significantly faster than Python UDFs when custom logic is unavoidable.

---

## Common Mistakes
- Using a UDF for `F.when`, `F.regexp_replace`, or other built-ins that already exist
- Not knowing Pandas UDFs exist — saying row-by-row UDFs are the only option
- Loading a model inside a UDF (per row) instead of using `mapPartitions`
- Saying UDFs "work fine" without knowing the performance cost

---

## Key Concepts Tested
- Python-JVM serialization overhead
- Catalyst optimization and why UDFs break it
- Pandas UDF — Apache Arrow, batch processing
- Native `pyspark.sql.functions` as preferred alternative
- `mapPartitions` for expensive per-partition initialization
