# Explain Kafka Architecture — Topics, Partitions, Consumer Groups, Offsets, and Delivery Guarantees

**Type:** Theoretical
**Topic:** Apache Kafka, Distributed Messaging, Stream Processing

---

## The Question
> "Explain Kafka's architecture — topics, partitions, consumer groups, and offsets. How does Kafka guarantee message delivery?"

---

## Core Architecture

```
Producers                  Kafka Cluster                       Consumers
                     ┌───────────────────────────┐
                     │   Topic: orders            │
P1 ─── write ──────► │  Partition 0: [0,1,2,3...] │ ──► Consumer Group A
                     │  Partition 1: [0,1,2,3...] │ ──► Consumer Group A
P2 ─── write ──────► │  Partition 2: [0,1,2,3...] │ ──► Consumer Group A
                     └───────────────────────────┘
                                                    ──► Consumer Group B (independent)
```

---

## Key Concepts

### Topic
A named, append-only stream of records. Producers write to a topic; consumers read from it.

### Partition
A topic is split into N ordered, immutable sequences stored on disk.

- **Why partition?** Parallelism — multiple consumers read different partitions simultaneously
- **Partition key** determines routing: `hash(key) % num_partitions`
- **Same key → same partition always** — guarantees ordering per key

```
order_id=101 → hash(101) % 3 = 0 → Partition 0  (always)
order_id=102 → hash(102) % 3 = 1 → Partition 1  (always)
```

### Offset
Sequential integer assigned to each record within a partition. Consumers track which offset they've read up to. **Resetting offset = replaying all data from that point.**

```
Partition 0:  [offset=0][offset=1][offset=2][offset=3] →
```

### Consumer Group
A group of consumers that jointly consume a topic. Kafka assigns each partition to exactly one consumer in the group.

```
3 partitions, 3 consumers:        3 partitions, 2 consumers:
  C1 → P0                           C1 → P0 + P1
  C2 → P1                           C2 → P2
  C3 → P2

Rule: max parallelism = number of partitions
      extra consumers sit idle
```

Multiple groups read the same topic **independently** — each group maintains its own offset. Analytics, fraud detection, and notifications can all consume the same `orders` topic without interfering.

---

## Delivery Guarantees

| Guarantee | Offset commit timing | Risk |
|---|---|---|
| **At-most-once** | Before processing | Message lost if crash after commit, before processing |
| **At-least-once** | After processing | Duplicate if crash after processing, before commit |
| **Exactly-once** | Transactional producer + idempotent consumer | No loss, no duplicates — highest overhead |

**Practical default:** At-least-once + idempotent sink (dedup on consumer side). True exactly-once is available but more expensive.

---

## Replication — Fault Tolerance

```
Partition 0:
  Broker 1 → Leader   (all reads/writes go here)
  Broker 2 → Replica  (in-sync)
  Broker 3 → Replica  (in-sync)

Broker 1 dies → Broker 2 elected leader automatically
```

`replication.factor=3` — data survives 2 broker failures.

---

## Retention — Kafka Is Not Long-Term Storage

```
retention.ms=604800000    # delete after 7 days (default)
```

For permanent storage: read from Kafka into S3/Delta Lake. Kafka is a transport layer, not an archive.

**Log compaction** (alternative): retains the latest record per key indefinitely. Used for changelog topics where you only need current state per entity.

---

## How to Say It in the Interview
> "Kafka is a distributed, append-only log. A topic is split into partitions — each partition is an ordered sequence with per-record offsets. Producers write to partitions based on a key hash so all records with the same key always land in the same partition, guaranteeing ordering per key. Consumers track their own offset — this enables replay by resetting the offset.
>
> Consumer groups give parallelism — each partition goes to exactly one consumer in the group, so max parallelism equals the number of partitions. Multiple independent groups read the same topic without interfering.
>
> For delivery: at-least-once is the practical default — commit offset after processing. For exactly-once, Kafka has transactional producers, but most teams use at-least-once with idempotent sinks since it's simpler."

---

## Follow-ups & Answers

**"What happens if a consumer crashes?"**
> Kafka detects missed heartbeats and triggers a rebalance — redistributes that consumer's partitions to remaining consumers. Consumption pauses briefly during rebalance.

**"How do you choose number of partitions?"**
> `max(throughput_target / throughput_per_partition, num_consumers)`. Can increase later, cannot decrease. More partitions = more parallelism but more overhead.

**"Kafka vs RabbitMQ?"**
> Kafka retains messages after consumption — consumers read independently and replay. RabbitMQ deletes on consumption. Kafka = high-throughput event streaming. RabbitMQ = task queues and routing.

**"What is log compaction?"**
> Retains only the latest record per key indefinitely instead of time-based deletion. Used for changelog topics — e.g., latest customer profile per customer_id.

---

## Common Mistakes
- Saying "Kafka guarantees ordering" — only within a partition, not across
- Adding more consumers than partitions — extras sit idle
- Confusing offset commit timing with delivery guarantee
- Treating Kafka as long-term storage — it has limited retention

---

## Key Concepts Tested
- Topics, partitions, offsets
- Partition key → ordering per key
- Consumer groups — parallelism and fan-out
- At-most-once / at-least-once / exactly-once
- Replication factor and fault tolerance
- Retention vs log compaction
