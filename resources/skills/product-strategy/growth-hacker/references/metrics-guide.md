# Metrics Guide

How to measure growth and know if you're on track.

---

## Metrics by Growth Stage

### Pre-PMF Stage

**Focus:** Finding product-market fit, not scaling.

**Key metrics:**
| Metric | What It Tells You |
|--------|------------------|
| PMF Score (Sean Ellis) | % "very disappointed" if product disappeared |
| Activation rate | % of signups who hit aha moment |
| Qualitative feedback | What users love/hate (not yet quantifiable) |
| Retention (early cohorts) | Do people come back? (even with small n) |
| NPS/word of mouth | Are users recommending? |

**Warning signs you're measuring wrong:**
- Obsessing over DAU with 100 users
- A/B testing with insufficient sample
- Tracking vanity metrics (signups, downloads)

**What to do instead:**
- Talk to users constantly
- Watch users interact with product
- Run PMF surveys
- Focus on depth with small user base

### Early Traction Stage

**Focus:** Validating growth loops work.

**Key metrics:**
| Metric | What It Tells You |
|--------|------------------|
| Activation rate | Are you getting users to value? |
| D1, D7, D30 retention | Are users forming habits? |
| Viral coefficient (K) | Does growth compound? |
| Referral rate | What % of users invite others? |
| Time to value | How fast do users hit aha moment? |

**Benchmarks (consumer apps):**
- D1 retention: 40%+ good, 60%+ excellent
- D7 retention: 20%+ good, 30%+ excellent
- D30 retention: 10%+ good, 20%+ excellent

**Benchmarks (B2B SaaS):**
- D1 retention: 60%+ good, 80%+ excellent
- Weekly retention: 40%+ good, 60%+ excellent
- Monthly retention: 80%+ good (stickier products)

### Scaling Stage

**Focus:** Efficient growth, unit economics.

**Key metrics:**
| Metric | What It Tells You |
|--------|------------------|
| CAC (Customer Acquisition Cost) | Cost to acquire one customer |
| LTV (Lifetime Value) | Total value from one customer |
| LTV:CAC ratio | Efficiency of growth (3:1+ healthy) |
| Payback period | Months to recoup CAC |
| Marginal ROI by channel | Which channels are most efficient? |
| Revenue retention | Are customers expanding or contracting? |

**LTV:CAC Benchmarks:**
- 1:1 = Barely breaking even
- 3:1 = Healthy, sustainable growth
- 5:1+ = Could invest more in acquisition

---

## Core Metric Definitions

### Activation Rate

**Formula:** Users who hit activation milestone / Total signups

**What counts as "activated"?**
- Should be an **experience-based** action
- User has received core value at least once
- Early enough to be actionable (ideally within first session)

**Examples:**
- Dropbox: Uploaded one file
- Facebook: Added 7 friends in 10 days
- LogMeIn: Completed one remote session
- Slack: Team sent 2,000 messages

**Choosing your activation metric:**
1. Start with qualitative hypothesis: "When do users 'get it'?"
2. Look for correlation with long-term retention
3. Pick something in first session/day if possible
4. Make it specific and measurable

### Retention Cohorts

**What it is:** Percentage of users returning after time period, grouped by signup date.

**How to read a cohort chart:**

```
         Week 0  Week 1  Week 2  Week 3  Week 4
Jan 1    100%    45%     32%     28%     25%
Jan 8    100%    48%     35%     30%     27%
Jan 15   100%    52%     38%     33%     -
Jan 22   100%    55%     -       -       -
```

**What to look for:**
- **Flattening curve:** Retention stabilizing (good sign)
- **Improving cohorts:** Later cohorts retain better (product improving)
- **Cliff drops:** Sharp decline at specific point (something broken)

### Viral Coefficient (K-factor)

**Formula:** K = (invites per user) × (conversion rate of invites)

**Example:**
- Average user invites 5 people
- 20% of invites convert
- K = 5 × 0.2 = 1.0

**Interpretation:**
- K < 1: Growth slowing without paid acquisition
- K = 1: Self-sustaining (each user brings 1 new user)
- K > 1: Viral growth (each user brings 1+ new users)

**Note:** True K > 1 is rare and usually temporary.

### Customer Acquisition Cost (CAC)

**Formula:** Total acquisition spend / New customers acquired

**Include in "total spend":**
- Ad spend
- Sales team costs
- Marketing team costs
- Tools and software
- Content production

**CAC by channel:** Calculate separately for each channel to find most efficient.

### Lifetime Value (LTV)

**Simple formula:** ARPU × Customer lifespan (in months)

**Better formula:** ARPU × (1 / monthly churn rate)

**Example:**
- ARPU: $50/month
- Monthly churn: 5%
- LTV = $50 × (1 / 0.05) = $50 × 20 = $1,000

---

## North Star Metrics

### What Makes a Good North Star

A North Star metric should:

1. **Reflect value delivered** to customers (not just business value)
2. **Be a count, not a ratio** (can grow "up and to the right")
3. **Correlate with revenue** over time
4. **Be a leading indicator** of success
5. **Be time-bounded** (daily/weekly > monthly)

### Company Examples

| Company | North Star | Why It Works |
|---------|------------|--------------|
| Airbnb | Nights booked | Value delivered regardless of price |
| Uber | Weekly rides | Frequency of value delivery |
| Facebook | Daily active users | Engagement = value |
| Spotify | Time spent listening | Consumption = value |
| Slack | Messages sent | Usage = value to team |
| Amazon | Monthly purchases | Transactions = value delivered |
| Netflix | Hours watched | Consumption = value |
| Hubspot | Weekly active teams | Team adoption = value |

### The DAU vs MAU Insight

**Facebook's shift from MAU to DAU:**

When focused on Monthly Active Users:
- Team got credit if user logged in once/month
- No incentive to increase visit frequency
- Features optimized for broad appeal

When shifted to Daily Active Users:
- Team incentivized to bring users back daily
- Product became stickier (sometimes too sticky)
- Features optimized for habit formation

**Key insight:** The metric you choose shapes team behavior. Choose deliberately.

### North Star Selection Exercise

**30-minute team exercise:**

1. **Define core value** (5 min)
   - What do "very disappointed" users say they love?
   - What's the atomic unit of value we deliver?

2. **Brainstorm metrics** (10 min)
   - What metric reflects that value being delivered?
   - Generate 3-5 candidates

3. **Score each candidate** (10 min)
   - Apply checklist: Count not ratio? Correlates to revenue? Leading indicator? Time-bounded?

4. **Choose and commit** (5 min)
   - Pick one
   - Commit for at least one quarter
   - Define supporting/input metrics

---

## Input Metrics

Your North Star is an output. Input metrics are the levers that drive it.

### Example: Airbnb

**North Star:** Nights booked

**Input metrics:**
- New guest signups (acquisition)
- Search-to-booking rate (activation)
- Host response rate (activation)
- Guest return rate (retention)
- Review completion rate (referral)
- Average nights per booking (expansion)

### Building Your Input Tree

```
                    North Star
                        |
        --------------------------------
        |               |              |
    Acquisition    Activation      Retention
        |               |              |
    [inputs]        [inputs]       [inputs]
```

For each input, identify:
1. What drives this metric?
2. What experiments could improve it?
3. What's the current baseline?

---

## PMF Indicators

### Quantitative Signals

**Strong PMF:**
- 40%+ "very disappointed" on PMF survey
- Retention curves flatten (not decline to zero)
- Organic/word-of-mouth > 50% of acquisition
- Usage frequency matches or exceeds expectation
- NPS > 50

**Weak PMF:**
- < 40% "very disappointed"
- Retention curves decline continuously
- Require constant paid acquisition
- Low usage frequency
- NPS < 20

### Qualitative Signals

**Strong PMF:**
- Users complain when product is down
- Users defend product unprompted
- Users ask for more features (not complaining about core)
- Sales cycles shortening (B2B)
- "Pull" from market (not pushing)

**Weak PMF:**
- Silence from users
- Users need convincing to try
- Core value frequently questioned
- Long sales cycles getting longer
- Constant "pushing" required

### The Binary Test

> "If your product's working, you'll know. And if there's any uncertainty, it's not working." — Nikita Bier

PMF is largely binary for consumer products:
- Things breaking from growth = PMF
- Measuring hourly actives (not daily) = PMF
- Can't keep servers up = PMF
- "We might have something" = Not PMF

---

## Cohort Analysis Basics

### Why Cohorts Matter

Aggregate metrics hide trends. A user acquired today is different from one acquired 6 months ago.

**Example:**
- Overall retention: 30%
- But: Early cohorts retain at 40%, recent cohorts at 20%
- Insight: Something changed that hurt retention

### How to Build a Cohort Chart

1. **Group users by signup date** (week or month)
2. **Track behavior over time** (D1, D7, D30, etc.)
3. **Calculate % still active** at each interval
4. **Compare cohorts** to spot trends

### What to Look For

**Improving cohorts:**
- Later cohorts retain better
- Product/onboarding improvements working

**Declining cohorts:**
- Later cohorts retain worse
- Something broke or market changed

**Flattening curves:**
- Retention stabilizes after initial drop
- Core users found; focus on expanding this

**Continuous decline:**
- No stable user base
- Core value not strong enough

---

## Benchmarks Reference

### SaaS Metrics

| Metric | Good | Great | World Class |
|--------|------|-------|-------------|
| Monthly churn | <5% | <3% | <1% |
| Net revenue retention | >100% | >110% | >130% |
| LTV:CAC | 3:1 | 5:1 | 7:1+ |
| CAC payback | <18 mo | <12 mo | <6 mo |

### Consumer App Metrics

| Metric | Good | Great | World Class |
|--------|------|-------|-------------|
| D1 retention | 40% | 50% | 60%+ |
| D7 retention | 20% | 30% | 40%+ |
| D30 retention | 10% | 15% | 25%+ |
| Viral coefficient | 0.3 | 0.5 | 1.0+ |

### Marketplace Metrics

| Metric | Good | Great | World Class |
|--------|------|-------|-------------|
| Take rate | 10-15% | 15-25% | 25%+ |
| Repeat rate | 30% | 50% | 70%+ |
| Supply fill rate | 70% | 85% | 95%+ |

---

## Key Quotes

**Sean Ellis:**
> "Probably retention cohorts are more accurate [than PMF survey], but the problem is, how long do you have to look at a retention cohort before you know that you've actually long-term retained someone?"

> "I don't think there's necessarily one exact right answer of what is that aha moment. There might be two or three different things. I think it's that intentionality about picking something that's experience-based."

**Nikita Bier:**
> "Our metric was hourly actives per day. Not daily active users, hourly active users. You'll start seeing that and it'll be abundantly obvious what product-market fit is."

> "If your product's working, you'll know. And if there's any uncertainty, it's not working."
