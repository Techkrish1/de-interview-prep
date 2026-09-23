# ETL vs ELT — What is the difference and when would you choose one over the other?

**Type:** Theoretical
**Topic:** Data Pipeline Architecture

---

## The Question
> "Can you explain the difference between ETL and ELT? When would you choose one over the other?"

---

## Core Difference

| | ETL | ELT |
|---|---|---|
| Flow | Extract → Transform → Load | Extract → Load → Transform |
| Where transform runs | External server / middleware | Inside the data warehouse |
| Raw data stored? | No — only cleaned data lands | Yes — raw layer always available |
| Reprocessing | Hard (raw data is gone) | Easy — rerun the SQL/dbt model |
| Best for | Compliance-heavy, RDBMS targets | Cloud DWH (Snowflake, BigQuery, Redshift) |
| Tooling | Informatica IICS, Talend, SSIS | Fivetran + dbt, Airbyte + dbt |
| Latency | Higher (transform before load) | Lower (raw load is fast) |

---

## Concrete Example — Same Problem, Two Approaches

**Scenario:** Pull order data from MySQL into a warehouse for analytics.

**ETL (e.g., Informatica IICS):**
```
MySQL → [Pipeline Server: mask emails, drop cancelled orders, join products] → Redshift
```
Warehouse only sees clean, structured data.

**ELT (e.g., Fivetran + dbt + BigQuery):**
```
MySQL → BigQuery raw.orders (all data, as-is) → dbt model transforms inside BigQuery
```
```sql
-- models/orders_clean.sql
SELECT
  order_id,
  sha256(customer_email) AS hashed_email,
  amount,
  order_date
FROM raw.orders
WHERE status != 'cancelled'
```
Raw data always stays — you can reprocess any time if logic changes.

---

## When to Choose Which

**Choose ETL when:**
- PII (emails, SSNs) cannot enter the warehouse unmasked — HIPAA, GDPR, PCI-DSS
- Target is a traditional RDBMS with limited compute
- Strict data quality gates — bad rows must never reach the target

**Choose ELT when:**
- Cloud warehouse with elastic compute (Snowflake, BigQuery, Redshift)
- Need to reprocess history — raw layer is always available
- Team uses dbt for version-controlled SQL transforms
- Need fast ingestion — raw load is near-instant, transform is deferred

**Rule of thumb:** Modern cloud stack → ELT. Regulated data (healthcare, finance) → ETL at edge, ELT downstream.

---

## Where dbt Fits
> dbt is the **T in ELT** — runs `SELECT` statements inside the warehouse, materializes results as tables/views. Adds version control, automated testing, and lineage. Does not move or extract data.

```
Fivetran (EL)  →  raw tables in Snowflake  →  dbt transforms  →  analytics-ready tables
```

---

## How to Say It in the Interview
> "The core difference is *where* transformation happens — outside the warehouse in ETL, inside in ELT. ETL transforms before loading — useful when data has PII that can't enter the warehouse unmasked. ELT loads raw data first and transforms it inside using dbt. The reason ELT became the default on modern cloud stacks is that compute inside BigQuery or Snowflake is elastic and cheap, and keeping the raw layer means you can always reprocess if business logic changes. I'd choose ETL for compliance-heavy data — say a healthcare dataset. For everything else on a cloud warehouse, ELT with dbt is cleaner and more flexible."

---

## Follow-ups & Answers

**"What is dbt and where does it fit?"**
> dbt is the transformation layer in ELT. It runs SQL `SELECT` statements inside your warehouse and materializes them as tables or views. Adds version control, testing (schema and data tests), and lineage documentation. It's version-controlled SQL for analytics engineers.

**"Can you use both ETL and ELT in the same pipeline?"**
> Yes — common pattern: lightweight ETL at ingestion to mask PII before it hits the raw layer, then ELT with dbt for all downstream transformations.

**"What happens if business logic changes in ETL?"**
> Raw data was never stored, so you must re-extract from source and rerun the whole pipeline. In ELT, just update the dbt model and rerun — much faster.

---

## Common Mistakes
- Saying ETL is always worse — wrong for regulated industries
- Not mentioning reprocessability as ELT's key advantage
- Forgetting dbt entirely
- Calling ELT "loading dirty data" — frame it as "deferred transformation"

---

## Key Concepts Tested
- Data warehouse architecture
- Compute-storage separation in cloud DWHs
- dbt and modern data stack
- Compliance-driven design decisions
