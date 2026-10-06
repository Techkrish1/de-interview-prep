# CAP Theorem — Consistency, Availability, and Partition Tolerance

**Type:** Theoretical
**Topic:** Distributed Systems, CAP Theorem, Database Trade-offs

---

## The Question
> "Explain the CAP theorem. How does it apply to databases and data systems you work with?"

---

## The Theorem

A distributed system can guarantee at most **2 of 3** properties simultaneously:

- **C — Consistency**: every read returns the most recent write (all nodes see the same data at the same time)
- **A — Availability**: every request gets a response (not necessarily the latest data)
- **P — Partition Tolerance**: the system keeps working even when network partitions occur (nodes can't talk to each other)

**The catch:** In any real distributed system, network partitions WILL happen. So P is non-negotiable — you always must tolerate partitions. The real choice is: **CP or AP?**

---

## CP — Consistency over Availability

When a partition occurs, the system blocks or returns an error rather than return stale data.

```
Node A ──✂── Node B    (network partition)

User writes to Node A
User reads from Node B
CP system: "I can't confirm this is fresh — returning error"
AP system: "Here's what I have, may be stale"
```

**CP databases:** HBase, Zookeeper, MongoDB (with majority write concern), Cassandra (quorum reads)

**Use case:** Financial transactions, inventory systems, anything where stale data causes real harm.

---

## AP — Availability over Consistency

When a partition occurs, the system returns the best available data (possibly stale) and resolves conflicts later.

**AP databases:** DynamoDB, Cassandra (eventual consistency mode), CouchDB

**Use case:** Shopping cart, social media feeds, DNS — stale data for a few seconds is acceptable; unavailability is not.

---

## Eventual Consistency

AP systems converge to consistency eventually — once the partition heals, nodes sync and reach agreement. Most modern NoSQL systems are AP with eventual consistency.

```
User updates profile on Node A (partition exists)
User reads from Node B → sees old profile (stale but available)
Partition heals → Node B syncs → now consistent
```

---

## How This Applies to DE Systems

| System | Type | Why |
|---|---|---|
| HBase | CP | Row-level strong consistency for OLTP |
| Cassandra | Tunable (AP by default) | Tune per-operation: `ONE`, `QUORUM`, `ALL` |
| Kafka | CP for partition leader | Leader election ensures one source of truth |
| DynamoDB | AP (eventual default) | `ConsistentRead=true` for CP on single items |
| Delta Lake | CP | ACID transactions via optimistic concurrency |
| Zookeeper | CP | Used by Kafka/HBase for leader election |

**Cassandra tunable consistency:**
```
Write with ConsistencyLevel.QUORUM   → majority must acknowledge (CP-ish)
Read  with ConsistencyLevel.ONE      → fastest, possibly stale (AP-ish)
Read  with ConsistencyLevel.QUORUM + Write QUORUM → strong consistency
```

---

## How to Say It in the Interview
> "CAP says a distributed system can only guarantee two of three: consistency, availability, or partition tolerance. Since network partitions are unavoidable in distributed systems, the real trade-off is CP vs AP. CP systems — like HBase or Zookeeper — return an error rather than stale data during a partition. AP systems — like Cassandra in default mode or DynamoDB — return the best available data and reconcile later. In DE, Delta Lake gives CP semantics for batch data through ACID transactions. Kafka guarantees CP for each partition's leader. For operational data stores, Cassandra lets you tune the trade-off per operation."

---

## Common Mistakes
- Saying "you can't have all three" without noting that P is always required — the real choice is C vs A
- Treating CA (no partition tolerance) as viable in production distributed systems
- Confusing consistency here (all nodes same data) with ACID consistency (data satisfies constraints)

---

## Key Concepts Tested
- C, A, P definitions
- P is non-negotiable → real choice is CP vs AP
- CP vs AP use cases (financial vs social)
- Eventual consistency
- Where common DE tools fall (Kafka, Cassandra, Delta Lake, DynamoDB)
