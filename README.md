# Data Engineering Interview Prep

Structured notes for Data Engineering interview preparation. Each file is named after the interview question.

## Structure

```
de-interview-prep/
├── theoretical/          # Concepts, architecture, design decisions
├── sql-problems/         # SQL queries, window functions, optimization
├── pyspark-problems/     # PySpark transformations, RDD, DataFrame API
├── real-life-scenarios/  # End-to-end pipeline design, trade-offs
├── system-design/        # Large-scale system design questions
└── behavioral/           # Situational and behavioral questions
```

## Questions Covered

### Theoretical
| Question | File |
|---|---|
| ETL vs ELT — difference and when to choose | [etl-vs-elt.md](theoretical/etl-vs-elt.md) |
| What is the difference between Star Schema and Snowflake Schema? | [star-schema-vs-snowflake-schema.md](theoretical/star-schema-vs-snowflake-schema.md) |
| Kafka architecture — topics, partitions, consumer groups, offsets, delivery guarantees | [kafka-architecture-topics-partitions-consumer-groups-offsets.md](theoretical/kafka-architecture-topics-partitions-consumer-groups-offsets.md) |
| What are ACID properties and how does Delta Lake implement them? | [acid-properties-and-delta-lake.md](theoretical/acid-properties-and-delta-lake.md) |
| What is the difference between a Data Lake, Data Warehouse, and Lakehouse? | [data-lake-vs-data-warehouse-vs-lakehouse.md](theoretical/data-lake-vs-data-warehouse-vs-lakehouse.md) |
| Spark execution model — DAG, stages, tasks, and shuffle | [spark-execution-model-dag-stages-tasks-shuffle.md](theoretical/spark-execution-model-dag-stages-tasks-shuffle.md) |
| Partitioning strategies — hash, range, and list | [partitioning-strategies-hash-range-list.md](theoretical/partitioning-strategies-hash-range-list.md) |

### SQL Problems
| Question | File |
|---|---|
| Find each user's 2nd most recent transaction and running total spend | [2nd-most-recent-transaction-and-running-total.md](sql-problems/2nd-most-recent-transaction-and-running-total.md) |
| Calculate month-over-month revenue growth by category | [month-over-month-revenue-growth-by-category.md](sql-problems/month-over-month-revenue-growth-by-category.md) |
| Deduplicate a table and keep only the latest record per user | [deduplicate-keep-latest-record-per-user.md](sql-problems/deduplicate-keep-latest-record-per-user.md) |
| Find users who logged in on at least 3 consecutive days | [find-users-with-consecutive-login-days.md](sql-problems/find-users-with-consecutive-login-days.md) |
| Find the median salary for each department | [find-median-salary-per-department.md](sql-problems/find-median-salary-per-department.md) |

### PySpark Problems
| Question | File |
|---|---|
| Find top 3 products by revenue for each category | [top-3-products-by-revenue-per-category.md](pyspark-problems/top-3-products-by-revenue-per-category.md) |
| Broadcast join and handling data skew | [broadcast-join-and-handling-data-skew.md](pyspark-problems/broadcast-join-and-handling-data-skew.md) |
| Read and write Parquet efficiently with partition pruning in PySpark | [read-write-parquet-with-partition-pruning.md](pyspark-problems/read-write-parquet-with-partition-pruning.md) |
| PySpark UDFs — when to use and why to avoid them | [pyspark-udfs-when-to-use-and-alternatives.md](pyspark-problems/pyspark-udfs-when-to-use-and-alternatives.md) |

### Real-life Scenarios
| Question | File |
|---|---|
| Sync a 500M-row MySQL table to warehouse incrementally | [incremental-load-vs-cdc-500-million-row-mysql-to-warehouse.md](real-life-scenarios/incremental-load-vs-cdc-500-million-row-mysql-to-warehouse.md) |
| Data quality checks in a production data pipeline | [data-quality-checks-in-a-production-data-pipeline.md](real-life-scenarios/data-quality-checks-in-a-production-data-pipeline.md) |
| Implement SCD Type 2 to track historical changes in a customer dimension | [scd-type-2-implementation.md](real-life-scenarios/scd-type-2-implementation.md) |

### System Design
| Question | File |
|---|---|
| Design a daily ETL pipeline using Airflow with failure handling and alerts | [daily-etl-pipeline-design-using-airflow.md](system-design/daily-etl-pipeline-design-using-airflow.md) |
| Design a real-time fraud detection pipeline for a payment system | [real-time-fraud-detection-pipeline.md](system-design/real-time-fraud-detection-pipeline.md) |

### Behavioral
| Question | File |
|---|---|
| Tell me about a time a data pipeline failed in production | [tell-me-about-a-time-a-data-pipeline-failed-in-production.md](behavioral/tell-me-about-a-time-a-data-pipeline-failed-in-production.md) |
| Tell me about a time you had to learn a new technology quickly | [tell-me-about-a-time-you-learned-new-technology-quickly.md](behavioral/tell-me-about-a-time-you-learned-new-technology-quickly.md) |
