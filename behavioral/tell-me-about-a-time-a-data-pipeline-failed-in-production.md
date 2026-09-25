# Tell Me About a Time When a Data Pipeline Failed in Production

**Type:** Behavioral
**Topic:** Incident handling, debugging, stakeholder communication

---

## The Question
> "Tell me about a time when a data pipeline failed in production. What happened, how did you diagnose it, and what did you change to prevent it from happening again?"

---

## The STAR Framework

| Part | What to cover | Time |
|---|---|---|
| **S**ituation | Context — what was the pipeline, what was at stake | 15 sec |
| **T**ask | Your specific role and responsibility | 10 sec |
| **A**ction | Diagnosis, fix, communication — be specific | 60 sec |
| **R**esult | Metrics, prevention, outcome | 20 sec |

---

## Sample Answer

> **Situation:**
> "I was supporting a customer who had a critical CDI pipeline syncing order data from Salesforce to their Snowflake warehouse. The pipeline ran every 4 hours and fed a live revenue dashboard used by their finance team for end-of-day reporting."
>
> **Task:**
> "The customer raised a P1 case — the pipeline had been silently failing for 6 hours, the dashboard showed stale data, and their finance team had already sent incorrect numbers to leadership. My job was to diagnose the root cause and restore normal operation."
>
> **Action:**
> "First I checked pipeline activity logs — jobs showed `SUCCESSFUL` status, which was the first red flag. Digging into session logs I found the Salesforce connector was hitting an API rate limit — jobs completed without error but wrote zero rows. The customer's Salesforce org had recently grown past the API call threshold.
>
> I took three steps: one, reconfigured the connector to use bulk API instead of REST API — bulk processes 10,000 records per call versus 200. Two, added a post-load row count validation — if rows written equals zero, the pipeline raises a failure rather than silently succeeding. Three, set up a Snowflake row count monitor that alerts the team if the table hasn't grown within the expected window."
>
> **Result:**
> "Pipeline restored within 2 hours. The zero-row detection has since caught two more silent failures before they reached the dashboard. The customer moved from reactive to proactive monitoring."

---

## Why This Answer Works
- Uses real Informatica/CDI context — sounds lived-in
- Shows diagnostic thinking — not just "I restarted the pipeline"
- Three specific actions — bulk API, row count validation, alerting
- Result has numbers — "2 hours", "two more failures caught"
- Prevention step — every strong answer includes what changed permanently

---

## Pattern for Any Pipeline Failure Story

```
Silent/noisy failure
  → checked logs (show your diagnostic process)
  → found non-obvious root cause
  → immediate fix
  → permanent prevention (monitoring, validation, alert)
  → communicated to stakeholders
```

---

## Other Behavioral Questions to Prep

| Question | Trait Being Tested |
|---|---|
| "Tell me about a time you disagreed with a technical decision" | Collaboration, assertiveness |
| "Describe a time you had to learn something new quickly" | Self-learning, adaptability |
| "Tell me about a time you improved a process" | Initiative, impact |
| "Describe a time you worked with a difficult stakeholder" | Communication, empathy |
| "Tell me about your most complex project" | Technical depth, ownership |

---

## How to Deliver It
- **Open with the impact:** "The pipeline was silently writing zero rows — no error, just stale data — for 6 hours undetected." Grabs attention immediately.
- Use **"I"** not **"we"** — show personal ownership
- Keep it under **2 minutes**
- Always end with the **prevention step** — what permanently changed

---

## Common Mistakes
- Choosing a story where you had no real involvement
- Describing only the fix, not the diagnosis — thought process is what's evaluated
- No prevention step — fixing once without learning is a red flag
- Going over 3 minutes — practice cutting to 2
- Starting defensively: "It wasn't really my fault..."

---

## Key Traits Tested
- Ownership and accountability
- Systematic root cause analysis
- Proactive monitoring mindset
- Stakeholder communication under pressure
- Learning from failure — prevention over reaction
