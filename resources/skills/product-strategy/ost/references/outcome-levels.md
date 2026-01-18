# Business Outcomes vs Product Outcomes

Understanding the distinction between outcome levels is critical for building effective OSTs.

---

## The Problem

Teams often conflate three different things:

1. **Outputs** - What we ship (features, pages, tools)
2. **Product Outcomes** - Changes in customer behavior
3. **Business Outcomes** - Changes in business metrics

Building outputs doesn't guarantee outcomes. The OST connects them explicitly.

---

## Business Outcomes

**Definition:** Company-level metrics that reflect business health.

**Characteristics:**
- Lagging indicators (results of many factors)
- Often quarterly or annual goals
- Influenced by multiple teams, not just product
- Directly tied to company strategy

**Examples:**

| Business Outcome | Typical Owner |
|------------------|---------------|
| Increase annual revenue by 20% | Executive team |
| Reduce churn from 5% to 3% | Cross-functional |
| Expand to enterprise segment | Go-to-market |
| Improve NPS from 30 to 50 | Company-wide |
| Increase market share | Company-wide |

**The challenge:** Product teams can't directly control business outcomes. Too many variables.

---

## Product Outcomes

**Definition:** Changes in customer behavior that product teams can directly influence.

**Characteristics:**
- Leading indicators (predict business outcomes)
- Measurable in weeks, not quarters
- Within product team's control
- Directly tied to product changes

**Examples:**

| Product Outcome | Why It Matters |
|-----------------|----------------|
| Increase weekly active usage from 2→4 days | Predicts retention |
| Reduce time-to-first-value from 7 days→1 day | Predicts activation |
| Increase feature adoption from 10%→40% | Predicts engagement |
| Reduce task completion time by 50% | Predicts satisfaction |
| Increase sharing/invite rate | Predicts growth |

**The insight:** Product outcomes are the behavioral changes that *cause* business outcomes.

---

## Connecting the Levels

**Example 1: Retention**

```
Business Outcome: Reduce annual churn from 8% to 5%
                           │
                           ▼
Product Outcome:  Increase weekly active days from 2 to 4
                           │
    ┌──────────────────────┼──────────────────────┐
    ▼                      ▼                      ▼
Opportunity:        Opportunity:           Opportunity:
Users forget        Users don't see        Users outgrow
to come back        value in first week    basic features
```

**Example 2: Revenue Growth**

```
Business Outcome: Increase revenue by 25%
                           │
        ┌──────────────────┼──────────────────┐
        ▼                                     ▼
Product Outcome:                    Product Outcome:
Increase trial→paid                 Increase expansion
conversion from 5%→10%              revenue per account
        │                                     │
        ▼                                     ▼
Opportunities from                  Opportunities from
trial user research                 power user research
```

**Example 3: Market Expansion**

```
Business Outcome: Win 10 enterprise accounts
                           │
                           ▼
Product Outcome:  Get 50% of enterprise trials
                  to complete security review
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
Opportunity:        Opportunity:       Opportunity:
IT needs SSO        Security team      Procurement needs
integration         needs audit logs   compliance docs
```

---

## How to Find Product Outcomes

### Method 1: Work Backwards

Start with business outcome, ask: "What customer behavior would drive this?"

| Business Outcome | Ask | Product Outcome |
|------------------|-----|-----------------|
| Reduce churn | What do retained customers do that churned ones don't? | Use feature X weekly |
| Increase revenue | What do paying customers do that free ones don't? | Complete onboarding in <24hrs |
| Grow market share | What makes customers choose us over competitors? | Experience value before signup |

### Method 2: Analyze Your Funnel

Map the customer journey, find the behaviors that predict success:

```
Signup → Onboarding → First Value → Habit → Expansion → Advocacy
   │          │            │          │         │           │
   └──────────┴────────────┴──────────┴─────────┴───────────┘
                    Each step is a potential product outcome
```

### Method 3: Cohort Analysis

Compare successful vs unsuccessful customers:

- What did retained customers do in week 1 that churned customers didn't?
- What did converted customers do during trial that non-converters didn't?
- What did power users do early that casual users didn't?

The differentiating behaviors become your product outcomes.

---

## Common Mistakes

### Mistake 1: Treating Outputs as Outcomes

| Output (Wrong) | Outcome (Right) |
|----------------|-----------------|
| Launch new dashboard | Increase daily check-ins by 30% |
| Ship mobile app | Increase usage sessions per week |
| Add Slack integration | Reduce time to respond to alerts |
| Redesign settings page | Increase feature configuration rate |

### Mistake 2: Product Outcomes Too Broad

| Too Broad | More Specific |
|-----------|---------------|
| Increase engagement | Increase comments per post |
| Improve retention | Increase 7-day return rate |
| Boost conversion | Increase trial→paid in first 14 days |

### Mistake 3: No Clear Connection

If you can't explain *why* the product outcome drives the business outcome, the connection is weak.

**Bad:** "We'll increase page views" → "Revenue will grow"
**Good:** "We'll increase saves/bookmarks" → "Saved items predict purchase" → "Revenue will grow"

---

## Testing Your Outcomes

### Business Outcome Checklist
- [ ] Tied to company strategy?
- [ ] Measurable (even if lagging)?
- [ ] Meaningful to leadership?
- [ ] Within 12-month planning horizon?

### Product Outcome Checklist
- [ ] A customer behavior (not a feature)?
- [ ] Directly influenceable by product changes?
- [ ] Measurable in weeks?
- [ ] Plausibly connected to business outcome?
- [ ] Specific enough to guide decisions?

---

## Examples by Company Type

### B2B SaaS
| Business Outcome | Product Outcome |
|------------------|-----------------|
| Reduce churn | Increase weekly active users per account |
| Increase expansion | Increase features used per account |
| Shorten sales cycle | Increase trial engagement score |

### Consumer App
| Business Outcome | Product Outcome |
|------------------|-----------------|
| Increase DAU | Increase content created per user |
| Grow revenue | Increase premium feature usage |
| Improve retention | Decrease days between sessions |

### Marketplace
| Business Outcome | Product Outcome |
|------------------|-----------------|
| Increase GMV | Increase transactions per buyer |
| Improve liquidity | Decrease time-to-first-match |
| Reduce CAC | Increase organic invite rate |

---

## Key Quotes

> "A product outcome is a change in customer behavior that drives business results." - Teresa Torres

> "Outputs are easy to measure but don't guarantee success. Outcomes are harder to measure but actually matter." - Josh Seiden

> "The best product outcomes are leading indicators—they predict the business outcomes before the business outcomes happen." - Teresa Torres
