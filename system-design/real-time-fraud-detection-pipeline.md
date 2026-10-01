# Design a Real-Time Fraud Detection Pipeline for a Payment System

**Type:** System Design
**Topic:** Streaming, Feature Store, ML Serving, Low Latency

---

## The Question
> "Design a system that detects fraudulent transactions in real time for a payment platform processing 10,000 transactions per second. Decisions must be made in under 200ms."

---

## Architecture

```
Payment API
    │
    ▼
  Kafka (partitioned by card_id)
    │
    ├─────────────────────────────────────┐
    ▼                                     ▼
Flink (real-time features)           S3 (raw events)
  - txn velocity (1min, 5min, 1hr)        │
  - avg spend per merchant                ▼
  - geo-distance from last txn     Spark batch (daily)
  - is_new_device                    - retrain ML model
    │
    ▼
Redis (Feature Store)  ◄─── batch features (7-day avg)
    │
    ▼
ML Scoring Service (model in memory — XGBoost)
    │
    ▼
Rules Engine (hard rules: amount > $10K, new country)
    │
    ▼
Decision: APPROVE / FLAG / BLOCK  (total < 200ms)
    │
    ▼
Kafka (fraud-decisions) → audit log, analyst review
```

---

## Latency Budget

| Step | Target |
|---|---|
| Kafka → Flink feature lookup | 20ms |
| Redis read | 1ms |
| ML model scoring | 50ms |
| Rules engine | 10ms |
| **Total** | **< 200ms** |

---

## Key Design Decisions

**Why Kafka partitioned by card_id?**
All events for the same card go to the same partition → stateful Flink processing (velocity counting) without cross-partition state sharing.

**Why Redis for feature store?**
Sub-millisecond reads. Pre-computed features available instantly when a transaction arrives — no recomputation at scoring time.

**Why ML + Rules Engine hybrid?**
ML catches complex patterns. Hard rules are interpretable and always enforced (regulatory requirement). Tiered response: low-confidence flags → step-up auth (OTP), high-confidence → block.

---

## How to Say It in the Interview
> "I'd use Kafka partitioned by card_id — all events for the same card go to the same partition for stateful processing. Flink computes real-time features like velocity and geo-distance, storing results in Redis. When a new transaction arrives, the scoring service reads features from Redis, runs the ML model in memory, and applies hard rules — all within 200ms. Raw events go to S3 in parallel for daily model retraining. The fraud decision is published back to Kafka for auditing."

---

## Follow-ups & Answers

**"How do you handle model drift?"**
> Monitor fraud recall and false positive rate weekly. If they degrade, trigger retraining. Use A/B testing — route 5% of traffic to new model before full rollout.

**"Redis goes down?"**
> Circuit breaker: fall back to rules-only mode until Redis recovers. Accepts slightly higher fraud risk over blocking all transactions.

**"False positives — blocking legitimate users?"**
> Tiered response: low confidence → OTP step-up, not hard block. Track false positive rate in feedback loop — analyst-reviewed decisions feed back as training labels.

---

## Common Mistakes
- No latency budget — 200ms disappears fast without planning
- No feedback loop for model retraining
- No degraded mode for downstream failures
- Batch-only — can't decide at 200ms

---

## Key Concepts Tested
- Kafka partitioning for stateful streaming
- Feature store pattern (Redis)
- ML model serving in low-latency context
- Hard rules + ML hybrid
- Latency budget per component
- Model retraining pipeline
