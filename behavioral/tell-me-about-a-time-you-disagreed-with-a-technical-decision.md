# Tell Me About a Time You Disagreed with a Technical Decision

**Type:** Behavioral
**Topic:** Conflict, Technical Judgment, Communication

---

## The Question
> "Tell me about a time you disagreed with a technical decision made by your team or manager. How did you handle it?"

---

## Why Interviewers Ask This

They want to see:
1. You can form your own technical opinions (not just follow orders)
2. You express disagreement constructively, not passively or aggressively
3. You can commit and execute even when you disagree
4. You learn from outcomes — whether you were right or wrong

---

## STAR Answer Framework

> **Situation:** "Our team was designing a data sync solution for a customer — syncing 200M records from Oracle to Snowflake nightly. The team lead proposed a full-extract-every-night approach using Informatica CDI. I had concerns about this."
>
> **Task:** "I believed an incremental approach using a watermark on the `last_modified` timestamp would be significantly faster and cheaper — the full extract was taking 8+ hours and causing load on the Oracle source. I needed to make this case without overstepping."
>
> **Action:** "I didn't push back in the meeting — I prepared first. I benchmarked both approaches on a 5% sample: full extract took 40 minutes for the sample, incremental took under 3 minutes once the watermark was set. I documented this with timing data and an estimate of what it would mean at full scale — projecting the full extract at ~8 hours vs incremental at ~35 minutes.
>
> I brought this to my lead in a one-on-one rather than challenging them publicly. I framed it as 'I ran some numbers, wanted to get your thoughts' — not 'you're wrong.' They reviewed it, agreed the incremental approach was better, and we updated the design."
>
> **Result:** "The incremental pipeline ran in under 45 minutes nightly. The customer avoided adding read replicas to their Oracle source to handle the load. My lead appreciated the proactive analysis — and since then I've been included in design discussions earlier."

---

## Why This Answer Works

- You disagreed based on **data**, not opinion
- You chose the right forum (one-on-one, not public)
- You framed it collaboratively ("wanted your thoughts") not confrontationally
- You show the outcome was positive for everyone, not just that you were "right"

---

## What If You Were Wrong?

Also a valid story — even stronger in some ways:

> "I challenged the approach, presented my case. After discussion, I realized my analysis had missed a constraint — X. I acknowledged I was wrong, learned from it, and committed to the original plan."

Shows intellectual honesty and ability to change your mind on evidence.

---

## How to Deliver It
- Lead with the stakes — why the decision mattered
- Name your specific concern — not "I disagreed" but "I thought X would cause Y"
- Show the work you did before raising it — data, benchmark, a written summary
- End with the relationship outcome, not just the technical outcome

---

## Follow-ups & Answers

**"What if your manager disagreed and you still thought you were right?"**
> "I'd make my case clearly once — with data. If they still decided the other way, I'd commit and execute. I'd document my concern privately in case it became relevant later. I've learned that sometimes the decision looks wrong technically but is right for business reasons I'm not fully seeing."

**"Would you do anything differently?"**
> Raise it sooner. I spent time building a full benchmark before saying anything — a quick 10-minute conversation earlier might have surfaced that this was already discussed and ruled out for other reasons.

---

## Common Mistakes
- Story where you were right and the manager was simply wrong — sounds arrogant
- Story where you stayed silent and didn't raise the concern — shows lack of initiative
- No data or reasoning — "I just felt it was wrong"
- Story that shows you couldn't commit after losing the argument

---

## Key Traits Tested
- Technical judgment and confidence
- Collaborative communication
- Data-driven decision making
- Ability to commit even under disagreement
- Self-awareness and humility
