---
publish_at: "2026-09-30T15:00:00Z"
folder: system-design
filename: real-time-fraud-detection-pipeline.md
title: Design a real-time fraud detection pipeline for a payment system
---

# Design a Real-Time Fraud Detection Pipeline for a Payment System

**Type:** System Design
**Topic:** Streaming, Feature Engineering, ML Serving, Low Latency

---

## The Question
> "Design a system that detects fraudulent transactions in real time for a payment platform processing 10,000 transactions per second. Fraud decisions must be made in under 200ms."

---

## Requirements Breakdown

| Requirement | Constraint |
|---|---|
| Throughput | 10,000 transactions/sec |
| Latency | < 200ms end-to-end decision |
| Accuracy | Low false positives (blocking legit users is bad) |
| Explainability | Why was a transaction flagged? |
| Adaptability | Fraud patterns change — model must be retrained |

---

## Architecture

```
Payment API
    │
    ▼
  Kafka                          ← ingestion, 10K/sec, partitioned by card_id
    │
    ├──────────────────────────────────────────────────────┐
    │                                                      │
    ▼                                                      ▼
Flink (real-time features)                          S3 (raw events)
    │                                                      │
    │  - velocity: txns in last 1min, 5min, 1hr           │
    │  - avg spend per merchant (rolling)                  ▼
    │  - geo-distance from last txn             Spark batch (daily)
    │  - is_new_device flag                         - retrain ML model
    ▼                                               - compute offline features
Feature Store (Redis)           ◄──────────────────────────┘
    │
    ▼
ML Scoring Service (REST API)   ← model loaded in memory (XGBoost / LightGBM)
    │
    ▼
Rules Engine                    ← hard rules: amount > $10K, new country, etc.
    │
    ▼
Decision: APPROVE / FLAG / BLOCK
    │
    ▼
Payment API response            ← total latency: < 200ms
    │
    ▼
  Kafka (fraud-decisions topic)  ← audit log, downstream alerts, analyst review
```

---

## Key Components Explained

### 1. Feature Engineering in Flink (< 50ms)

```python
# Flink: compute rolling features per card_id
# Velocity: how many txns in last 60 seconds?
txns_last_60s = df.groupBy(
    "card_id",
    session_window("event_time", gap_duration="60 seconds")
).count()

# Flink stores results in Redis with TTL
# Key: "velocity:card_id:60s" → Value: count
```

### 2. Feature Store (Redis)

- Pre-computed features stored with TTL
- ML scoring service reads from Redis in ~1ms
- Flink updates features continuously as events arrive
- Batch job updates longer-window features (7-day avg spend) nightly

### 3. ML Scoring (< 100ms)

```python
# Model loaded in memory — no DB call
model = xgboost.Booster()
model.load_model("fraud_model_v12.bin")

def score(features: dict) -> float:
    dmatrix = xgboost.DMatrix([list(features.values())])
    return float(model.predict(dmatrix)[0])   # fraud probability 0–1
```

### 4. Rules Engine (< 10ms)

Hard rules that always apply, regardless of model score:
- Transaction > $10,000 → always flag for manual review
- Card used in 2 different countries within 30 minutes → block
- First transaction on a new device AND amount > $500 → flag

---

## Latency Budget

| Step | Target |
|---|---|
| Kafka consume → Flink feature lookup | 20ms |
| Redis feature read | 1ms |
| ML model scoring | 50ms |
| Rules engine | 10ms |
| Response to payment API | 200ms total |

---

## How to Say It in the Interview
> "I'd use Kafka as the ingestion layer partitioned by card_id — this ensures all events for the same card go to the same partition for stateful processing. Flink computes real-time features like transaction velocity and geographic distance, storing results in Redis. When a new transaction arrives, the scoring service reads features from Redis, runs the ML model in memory, and applies hard rules — all within 200ms. Raw events go to S3 in parallel for a daily batch job that retrains the model on fresh fraud patterns. The fraud decision is published back to Kafka for auditing and analyst review."

---

## Follow-ups & Answers

**"How do you handle model drift as fraud patterns change?"**
> Continuous monitoring: compare model score distribution weekly. If fraud recall drops or false positive rate rises, trigger retraining. Use A/B testing — route 5% of traffic to the new model, compare metrics before full rollout.

**"How do you avoid blocking legitimate users (false positives)?"**
> Tiered response: low-confidence flags trigger step-up authentication (OTP) instead of hard block. Only high-confidence fraud gets blocked. Track false positive rate in the feedback loop — flagged transactions reviewed by analysts feed back into training labels.

**"What if Redis goes down?"**
> Fall back to a degraded mode: use only the rules engine (no ML scoring) until Redis recovers. This accepts slightly higher fraud risk over blocking all transactions. Circuit breaker pattern in the scoring service.

---

## Common Mistakes
- Not specifying latency budget per component — 200ms disappears fast
- Forgetting the feedback loop (analyst decisions → retraining labels)
- No degraded mode / circuit breaker for downstream failures
- Batch-only approach — can't make real-time decisions at 200ms with batch

---

## Key Concepts Tested
- Kafka partitioning for stateful stream processing
- Flink streaming feature engineering
- Feature store pattern (Redis)
- ML model serving in low-latency context
- Hard rules + ML hybrid approach
- Latency budget across components
- Model retraining pipeline
