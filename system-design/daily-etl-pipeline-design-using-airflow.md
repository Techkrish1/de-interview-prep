# Design a Daily ETL Pipeline Using Apache Airflow with Failure Handling and Alerts

**Type:** System Design
**Topic:** Apache Airflow, Orchestration, Pipeline Design

---

## The Question
> "Design a daily ETL pipeline using Apache Airflow that extracts data from 5 different sources, transforms and loads it into a data warehouse, handles failures gracefully, and sends alerts. Walk me through your design."

---

## What Airflow Is — Say This First
> Airflow is a **workflow orchestrator** — it schedules, monitors, and manages task dependencies. It does NOT move or process data itself. It tells your Spark jobs, SQL queries, and Python scripts when to run and in what order.

| Term | Meaning |
|---|---|
| **DAG** | Pipeline definition — a Python file |
| **Task** | One unit of work (run Spark job, call API, run SQL) |
| **Operator** | Type of task — `PythonOperator`, `SparkSubmitOperator`, `BashOperator` |
| **Sensor** | Waits for an external condition before proceeding |
| **XCom** | Pass small values between tasks |
| **Execution Date** | Logical date the DAG run represents — not actual run time |

---

## Pipeline Design

**DAG dependency graph:**
```
start
  │
  ├── extract_mysql    ──┐
  ├── extract_api      ──┤
  ├── extract_s3       ──┼──► transform ──► load ──► dq_check ──► notify_success
  ├── extract_postgres ──┤
  └── extract_kafka    ──┘
```
All 5 extracts run **in parallel** → transform fans in → load → quality check → alert.

---

## The DAG Code

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.utils.dates import days_ago
from datetime import timedelta

default_args = {
    "owner": "data-engineering",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,     # 5m → 10m → 20m
    "email_on_failure": True,
    "email": ["de-alerts@company.com"],
    "execution_timeout": timedelta(hours=2),
    "on_failure_callback": on_failure_slack_alert,
}

with DAG(
    dag_id="daily_etl_pipeline",
    default_args=default_args,
    schedule_interval="0 2 * * *",         # 2 AM daily
    start_date=days_ago(1),
    catchup=False,                          # don't backfill missed runs
    tags=["etl", "daily"],
) as dag:

    extract_mysql    = PythonOperator(task_id="extract_mysql",    python_callable=extract_from_mysql)
    extract_api      = PythonOperator(task_id="extract_api",      python_callable=extract_from_api)
    extract_s3       = PythonOperator(task_id="extract_s3",       python_callable=extract_from_s3)
    extract_postgres = PythonOperator(task_id="extract_postgres", python_callable=extract_from_postgres)
    extract_kafka    = PythonOperator(task_id="extract_kafka",    python_callable=extract_from_kafka)

    transform = SparkSubmitOperator(
        task_id="transform",
        application="s3://jobs/transform.py",
        conn_id="spark_cluster",
    )

    load      = PythonOperator(task_id="load_to_warehouse", python_callable=load_to_snowflake)
    dq_check  = PythonOperator(task_id="dq_check",          python_callable=run_great_expectations)
    notify    = PythonOperator(task_id="notify_success",    python_callable=send_slack_success)

    # Dependencies
    [extract_mysql, extract_api, extract_s3, extract_postgres, extract_kafka] >> transform
    transform >> load >> dq_check >> notify
```

---

## Failure Handling

### Retries with exponential backoff
```python
"retries": 3,
"retry_exponential_backoff": True,   # retries at 5m, 10m, 20m
```

### Immediate Slack alert on failure
```python
def on_failure_slack_alert(context):
    task_id = context["task_instance"].task_id
    dag_id  = context["dag"].dag_id
    log_url = context["task_instance"].log_url
    send_slack(f"FAILED: {dag_id}.{task_id} | Logs: {log_url}")
```

### SLA miss — alert if task hangs
```python
extract_mysql = PythonOperator(
    task_id="extract_mysql",
    python_callable=extract_from_mysql,
    sla=timedelta(hours=1),
)
```

### Idempotency — every task safe to rerun
```python
def extract_from_mysql(execution_date, **kwargs):
    output_path = f"s3://raw/orders/date={execution_date.date()}/data.parquet"
    df.write.mode("overwrite").parquet(output_path)   # overwrite = idempotent
```

---

## Data Quality Check
```python
def run_great_expectations(**kwargs):
    df = spark.read.table("warehouse.orders_daily")
    assert df.count() > 0,                            "Table is empty"
    assert df.filter("order_id IS NULL").count() == 0, "Null order_ids"
    assert df.filter("amount < 0").count() == 0,      "Negative amounts"
    kwargs["ti"].xcom_push(key="row_count", value=df.count())
```

---

## Monitoring Signals

| Signal | Tool | Threshold |
|---|---|---|
| Task failure | Airflow + Slack callback | Any failure |
| DAG run duration | SLA | > 4 hours |
| Row count drop | Great Expectations | < 80% of yesterday |
| Data freshness | Airflow Sensor | Data older than 26 hours |

---

## How to Say It in the Interview
> "I'd model this as an Airflow DAG with the 5 extract tasks running in parallel — no dependency between them. Transform fans in from all 5, then load, quality check, and success notification run sequentially. For failures: 3 retries with exponential backoff, an `on_failure_callback` fires a Slack alert immediately, and SLA timers catch hung tasks. Every extract is idempotent — partitions output by execution date and overwrites — so reruns are safe. After load, a Great Expectations step validates row counts, nulls, and anomalies before analysts see the data."

---

## Follow-ups & Answers

**"What is `catchup=False` and why?"**
> Without it, re-enabling a paused DAG triggers backfill runs for every missed interval — can overload the cluster. `catchup=False` runs only the latest interval.

**"What's the difference between `execution_date` and actual run time?"**
> `execution_date` is the logical period — a 2AM daily DAG run on Sept 25 has `execution_date` = Sept 24 (processes yesterday's data). Critical for idempotent partitioning and backfills.

**"How do you pass data between tasks?"**
> XCom for small values (row counts, file paths). Never use XCom for large datasets — pass the S3 path or table name instead. Large data travels via storage, not through Airflow's metadata DB.

**"If one extract fails, does the whole DAG stop?"**
> Yes — `transform` requires all 5. If any extract exhausts retries, `transform` is skipped. Use `trigger_rule="one_success"` or `"all_done"` if you want downstream tasks to run regardless.

---

## Common Mistakes
- Calling Airflow a data processing tool — it's an orchestrator
- Not mentioning idempotency — reruns must be safe
- Forgetting `catchup=False` — causes backfill storms
- Not explaining the fan-in pattern for parallel extracts
- Confusing `execution_date` with actual wall-clock time

---

## Key Concepts Tested
- Airflow DAG structure: tasks, operators, sensors, dependencies
- Parallel vs sequential task design with fan-in
- Retry strategy and exponential backoff
- Idempotency and safe reruns
- SLA monitoring and on_failure_callback
- XCom — what to pass and what not to
- Data quality with Great Expectations / dbt tests
