# Growth Frameworks Reference

Deep dive on the core frameworks used in growth strategy.

---

## 1. The Sean Ellis PMF Test

### The Question

> "How would you feel if you could no longer use [product]?"

**Response options:**
- Very disappointed
- Somewhat disappointed
- Not disappointed (or: I've already stopped using it)

### The Threshold

**40% "very disappointed"** = leading indicator of product-market fit

Important caveats:
- This is a **leading indicator**, not definitive PMF
- Actual retention/usage is the true test
- The 40% isn't scientifically precise—it's a focusing mechanism
- Cultural differences exist (Nubank uses 50% because "Brazilians are optimistic")

### When to Survey

Target a **random sample** of users who:
- Have actually used the product (not just signed up)
- Used it 2+ times (experienced the core value)
- Used it within the last 1-2 weeks (haven't churned yet)
- Sample size: Minimum 30 responses for directional signal

**Do NOT survey:**
- Landing page visitors
- People who just signed up
- Users who churned months ago
- People who only saw a demo

### Critical Follow-Up Questions

For "very disappointed" users:

1. **"What is the primary benefit you get from [product]?"**
   - First as open-ended to crowdsource benefits
   - Then as multiple choice (force them to pick ONE)

2. **"Why is that benefit important to you?"**
   - Gets the emotional context
   - Reveals messaging hooks

**Example from Xobni:**
- Benefit: "Helps me find things faster in email"
- Why important: "I'm drowning in email"
- **Result:** "Drowning in email?" became their most effective acquisition hook

### Additional Useful Questions

- "What would you use as an alternative if [product] didn't exist?"
  - Reveals competitive landscape
  - "Somewhat disappointed" users usually have easy alternatives

- "What type of person do you think would benefit most from [product]?"
  - Identifies target persona in user's words

- "How did you discover [product]?"
  - Reveals working acquisition channels

- "Have you recommended [product] to anyone?"
  - Leading indicator of word-of-mouth potential

### The Superhuman Approach

Rahul Vohra's enhancement for improving PMF score:

1. Identify the core benefit that "very disappointed" users love
2. Find "somewhat disappointed" users who **also** care about that same benefit
3. Ask them: "What would it take for this to become a must-have for you?"
4. Build those features—staying true to core value while expanding appeal

**Why this works:** You're not diluting for everyone; you're expanding for people who already care about your core value.

### Case Study: Lookout (7% → 40% in 2 Weeks)

**Situation:** Mobile security app with multiple features (backup, find phone, firewall, antivirus). Only 7% said "very disappointed."

**Discovery:** The 7% were almost entirely focused on antivirus functionality.

**Actions (2 weeks):**
1. Repositioned entire product around antivirus
2. Streamlined onboarding to set up antivirus first
3. First message after setup: "You're now protected from viruses"

**Result:** Next cohort hit 40% "very disappointed." Six months later: 60%. Eventually became a unicorn.

**Key insight:** Often you don't need to change the product—just the positioning and onboarding sequence.

---

## 2. AARRR (Pirate Metrics)

The classic growth funnel framework by Dave McClure.

### The Stages

| Stage | Question | Example Metrics |
|-------|----------|-----------------|
| **Acquisition** | How do users find you? | Visitors, signups, app installs |
| **Activation** | Do they have a great first experience? | Completed onboarding, first key action |
| **Retention** | Do they come back? | DAU/MAU, return visits, churn rate |
| **Referral** | Do they tell others? | Invites sent, viral coefficient |
| **Revenue** | Do they pay? | Conversion rate, LTV, ARPU |

### The Sean Ellis Reordering

**Traditional approach:**
```
Acquisition → Activation → Retention → Referral → Revenue
```

**Sean Ellis approach:**
```
Activation → Retention/Engagement → Referral → Revenue → Acquisition
```

**Why work backwards?**

1. **Acquisition is most competitive.** If you're not efficient at converting and retaining, you'll never find profitable acquisition channels.

2. **Leaky bucket problem.** Pouring users into a broken funnel wastes money and burns potential users.

3. **Math compounds.** Small improvements in activation multiply through the entire funnel.

**LogMeIn example:**
- Before: 5% of signups actually used product → Could only spend $10k/month on acquisition
- After: 50% signup-to-usage rate → Same channels now scaled to $1M/month
- Same product, same channels—just fixed activation

### Applying AARRR

For each stage:
1. Define your key metric
2. Identify current performance
3. Benchmark against competitors/industry
4. Identify 3-5 experiments to improve
5. ICE score and prioritize

---

## 3. ICE Scoring

Simple framework for prioritizing growth experiments.

### The Components

| Factor | Question | Scale |
|--------|----------|-------|
| **Impact** | If this works, how much will it move our key metric? | 1-10 |
| **Confidence** | How sure are we this will work? | 1-10 |
| **Ease** | How easy/fast is this to implement? | 1-10 |

**ICE Score = (Impact + Confidence + Ease) / 3**

Or simply: Impact × Confidence × Ease (for more spread)

### Why ICE Works

1. **Simple.** Anyone can understand and use it immediately.

2. **Crowdsources ideas.** When you have a systematic way to compare ideas, people across the company can contribute without endless debates.

3. **Transparent prioritization.** When ideas aren't chosen, you can explain why (low confidence, high effort, etc.)

4. **Forces estimation.** Even rough estimates are better than no estimates.

### ICE Scoring Tips

**Impact:**
- 10 = Could 2x+ our key metric
- 7-9 = Significant improvement (20-50%)
- 4-6 = Moderate improvement (5-20%)
- 1-3 = Marginal improvement (<5%)

**Confidence:**
- 10 = We've seen this work elsewhere, have strong data
- 7-9 = Good evidence, similar things have worked
- 4-6 = Reasonable hypothesis, some supporting data
- 1-3 = Pure guess, no evidence

**Ease:**
- 10 = Can do in a few hours, no dependencies
- 7-9 = A few days, minimal dependencies
- 4-6 = A week or two, some complexity
- 1-3 = Months of work, many dependencies

### RICE Alternative

Intercom's extension adds **Reach**:

**RICE = (Reach × Impact × Confidence) / Effort**

Sean Ellis's view: "Reach is already factored into Impact. ICE is simpler."

Use RICE if your team wants more precision; use ICE if you want speed.

---

## 4. North Star Metric

A single metric that captures the core value you deliver.

### Characteristics of a Good North Star

1. **Reflects value delivered to customers** (not just business value)
2. **Not a ratio** (can grow "up and to the right" over time)
3. **Correlates to revenue growth**
4. **Leading indicator** of long-term success
5. **Time-capped** for focus (daily or weekly beats monthly)

### Examples

| Company | North Star | Why It Works |
|---------|------------|--------------|
| Airbnb | Nights booked | Each night = value delivered to guest and host |
| Amazon | Monthly purchases | Each purchase = value delivered regardless of price |
| Uber | Weekly rides | Each ride = value delivered |
| Facebook | Daily active users | Engagement = value to user |
| Spotify | Time spent listening | Listening = value delivered |
| Slack | Daily active users | Usage = value to team |

### The DAU vs MAU Story

Facebook's shift from Monthly Active Users to Daily Active Users:

**Before (MAU focus):**
- Team got credit for any user who logged in once/month
- No incentive to increase frequency
- Features optimized for breadth, not depth

**After (DAU focus):**
- Team incentivized to bring users back daily
- Product became much more engaging (arguably too engaging)
- Massive impact on feature development

**Lesson:** The metric you choose shapes behavior. Choose carefully.

### North Star Selection Process

**30-minute team exercise:**

1. Start with PMF research: What's the core value according to "very disappointed" users?

2. Brainstorm 3-5 candidate metrics that reflect that value

3. Apply checklist to each:
   - [ ] Not a ratio
   - [ ] Can grow over time
   - [ ] Correlates to revenue
   - [ ] Reflects customer value
   - [ ] Leading indicator

4. Pick one. Commit for at least a quarter.

5. Define supporting metrics (input metrics that drive the North Star)

### North Star vs. Revenue

**Why not use revenue as North Star?**

Revenue is an output, not an input. It's a lagging indicator of value delivered.

Amazon example: A $1000 TV purchase and a $10 toothbrush purchase deliver similar value to the customer (both solved a need). Monthly purchases captures this better than GMV.

Revenue should **correlate** with your North Star, but the North Star should guide daily decisions about building value.

---

## Framework Selection Guide

| Situation | Use This Framework |
|-----------|-------------------|
| "Do we have product-market fit?" | Sean Ellis PMF Test |
| "Where should we focus our growth efforts?" | AARRR Audit |
| "Which experiment should we run first?" | ICE Scoring |
| "What's our key metric?" | North Star selection |
| "How do we improve our PMF score?" | Superhuman approach |

---

## Key Quotes

**Sean Ellis:**
> "Once you got a high enough percentage of users saying they'd be very disappointed, most of those products did pretty well. If you felt too low, those products tended to suffer."

> "Ignore the people who say they'd be somewhat disappointed. They're telling you it's a nice-to-have."

> "If you start paying attention to what your somewhat disappointed users are telling you and then you start tweaking based on their feedback, maybe you're going to dilute it for your must-have users."

> "Moving retention often is really hard, but it's usually much more a function of onboarding to the right user experience than it is about the tactical things that people try to do to improve retention."

> "Customer acquisition is so hard that if you're not really efficient at converting and retaining and monetizing people, you're going to really struggle on the customer acquisition side."
