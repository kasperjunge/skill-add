# Assumption Mapping

How to surface, categorize, and prioritize the assumptions underlying your solutions.

---

## Why Assumptions Matter

Every solution is built on assumptions—beliefs we hold that might not be true. Untested assumptions are the primary source of product failure.

**The trap:** Teams build solutions assuming they'll work, then discover too late that a core assumption was wrong.

**The fix:** Surface assumptions explicitly, then test the riskiest ones before committing resources.

---

## The Four Assumption Types

### 1. Desirability Assumptions

**Question:** Will customers want this?

**Examples:**
- "Users will prefer automated recommendations over manual selection"
- "Customers care about this problem enough to change behavior"
- "This is a top-3 priority for our target users"
- "Users will trust AI-generated suggestions"

**Signals you have desirability risk:**
- No direct customer quotes supporting the need
- The opportunity came from internal brainstorming, not research
- Similar solutions have failed in the market
- You're solving a "nice to have," not a "must have"

### 2. Usability Assumptions

**Question:** Can customers figure out how to use this?

**Examples:**
- "Users will understand how to configure this feature"
- "The new workflow will be intuitive without training"
- "Users will notice and find this feature"
- "The learning curve won't cause abandonment"

**Signals you have usability risk:**
- New interaction patterns unfamiliar to users
- Complex configuration or setup required
- Feature buried in UI or requires discovery
- Significant change from current behavior

### 3. Feasibility Assumptions

**Question:** Can we build this?

**Examples:**
- "We can integrate with their legacy systems"
- "The algorithm will perform well at scale"
- "We can ship this in the planned timeframe"
- "Our infrastructure can handle the load"
- "We have the expertise to build this"

**Signals you have feasibility risk:**
- Using new/unfamiliar technology
- Depending on external systems or APIs
- Tight timeline with unknown complexity
- Team lacks experience in this area

### 4. Viability Assumptions

**Question:** Does this work for the business?

**Examples:**
- "Users will pay $X/month for this feature"
- "This won't cannibalize our existing revenue"
- "Customer acquisition cost will be sustainable"
- "We can support this without scaling the team"
- "This complies with regulations"

**Signals you have viability risk:**
- New pricing model or revenue stream
- Regulatory or legal uncertainty
- Significant support/operations burden
- Unclear unit economics

---

## Surfacing Assumptions

### Technique 1: "What Must Be True?"

For each solution, ask: "For this to succeed, what must be true?"

Then categorize each answer:
- About customer desire? → Desirability
- About customer ability? → Usability
- About our ability to build? → Feasibility
- About business model? → Viability

### Technique 2: Pre-Mortem

Imagine the solution failed. Ask: "Why did it fail?"

Each failure reason reveals an assumption:
- "Users didn't care" → Desirability assumption
- "Users couldn't figure it out" → Usability assumption
- "We couldn't build it in time" → Feasibility assumption
- "It cost too much to support" → Viability assumption

### Technique 3: Question Storming

Generate as many questions as possible about the solution:
- "Will users want...?"
- "Can users figure out...?"
- "Can we build...?"
- "Will the business model support...?"

Each question is an assumption in disguise.

---

## Prioritizing Assumptions

Not all assumptions need testing. Focus on those that are:
- **High risk** - If wrong, the solution fails
- **Low confidence** - We don't have evidence it's true

### The 2x2 Matrix

```
                    HIGH RISK
                        │
         ┌──────────────┼──────────────┐
         │              │              │
         │   MONITOR    │  TEST FIRST  │
         │              │              │
         │  Could hurt  │  Could kill  │
         │  but won't   │  the whole   │
         │  kill us     │  solution    │
         │              │              │
LOW ─────┼──────────────┼──────────────┼───── HIGH
CONFIDENCE              │              CONFIDENCE
         │              │              │
         │   IGNORE     │   PROCEED    │
         │              │              │
         │  Low risk,   │  We have     │
         │  who cares   │  evidence    │
         │              │              │
         └──────────────┼──────────────┘
                        │
                    LOW RISK
```

### Prioritization Questions

For each assumption, ask:

**Risk:** "If this assumption is wrong, what happens?"
- Solution completely fails → High risk
- Solution is degraded but viable → Medium risk
- Minor inconvenience → Low risk

**Confidence:** "What evidence do we have?"
- Strong data/research → High confidence
- Some signals → Medium confidence
- Just our intuition → Low confidence

### Priority Ranking

1. **Test First:** Low confidence + High risk
2. **Test Second:** Low confidence + Medium risk, or Medium confidence + High risk
3. **Monitor:** Medium confidence + Medium risk
4. **Proceed:** High confidence (any risk level)
5. **Ignore:** Low risk (any confidence level)

---

## Assumption Testing Methods

### For Desirability

| Method | Speed | Confidence |
|--------|-------|------------|
| Customer interviews | Fast | Medium |
| Surveys | Fast | Low-Medium |
| Fake door test | Fast | Medium-High |
| Landing page | Medium | Medium-High |
| Concierge MVP | Slow | High |

**Fake door test:** Show the feature in UI, measure clicks, then explain "coming soon."

### For Usability

| Method | Speed | Confidence |
|--------|-------|------------|
| 5-second test | Fast | Low |
| Paper prototype | Fast | Medium |
| Clickable prototype | Medium | Medium-High |
| Wizard of Oz | Medium | High |
| Unmoderated usability test | Medium | Medium |

**Wizard of Oz:** User thinks it's automated, but human is behind the scenes.

### For Feasibility

| Method | Speed | Confidence |
|--------|-------|------------|
| Expert review | Fast | Medium |
| Spike / time-box | Fast-Medium | Medium-High |
| Proof of concept | Medium | High |
| Architecture review | Fast | Medium |

**Spike:** Time-boxed exploration (e.g., "spend 2 days seeing if this API works").

### For Viability

| Method | Speed | Confidence |
|--------|-------|------------|
| Competitive analysis | Fast | Low |
| Pricing survey | Fast | Low-Medium |
| Pricing page test | Medium | Medium-High |
| Pilot/beta with pricing | Slow | High |
| Unit economics modeling | Fast | Medium |

---

## Documenting Assumptions

### Assumption Card Format

```
ASSUMPTION
[Statement of what we believe to be true]

TYPE
[ ] Desirability  [ ] Usability  [ ] Feasibility  [ ] Viability

CONFIDENCE: Low / Medium / High
Evidence: [What makes us believe this?]

RISK: Low / Medium / High
If wrong: [What happens to the solution?]

PRIORITY: Test First / Test Second / Monitor / Proceed / Ignore

TEST PLAN
Method: [How we'll test]
Success criteria: [What would validate/invalidate]
Timeline: [How long]
```

### Example

```
ASSUMPTION
Users will prefer automated task prioritization over manual sorting

TYPE
[x] Desirability  [ ] Usability  [ ] Feasibility  [ ] Viability

CONFIDENCE: Low
Evidence: One customer mentioned it in an interview; no quantitative data

RISK: High
If wrong: Core value prop fails; users won't adopt the feature

PRIORITY: Test First

TEST PLAN
Method: Show prototype to 10 users, ask them to organize their tasks
Success criteria: 7+ prefer automated; qualitative feedback positive
Timeline: 1 week
```

---

## Common Mistakes

### Mistake 1: Testing Low-Risk Assumptions

Don't waste time testing things that don't matter. If the assumption is wrong but the solution still works, skip it.

### Mistake 2: Over-Confidence from Limited Data

"We talked to 3 users" ≠ high confidence. Be honest about what you know.

### Mistake 3: Testing Desirability When Usability is the Risk

If users clearly want something but can't figure out how to use it, more desirability testing won't help.

### Mistake 4: Confirmation Bias in Testing

Design experiments that can actually invalidate your assumption, not just confirm it.

### Mistake 5: Not Defining Success Criteria Upfront

Decide what "validates" and "invalidates" before you run the test, not after you see results.

---

## Key Quotes

> "The biggest risk is not that we'll build something nobody wants—it's that we'll discover that after we've spent months building it." - Teresa Torres

> "An assumption is something we believe to be true but haven't yet validated." - Teresa Torres

> "Test the riskiest assumption first. If it fails, you've saved yourself from building the wrong thing." - Marty Cagan
