---
name: growth-hacker
description: Generate growth strategies and ready-to-publish marketing content for product growth. Use when planning launches, assessing product-market fit, creating marketing content, designing experiments, optimizing activation/onboarding, or developing acquisition strategies. Incorporates proven frameworks from Sean Ellis (PMF testing, ICE prioritization) and Nikita Bier (viral consumer growth, activation optimization). Covers product-market fit assessment, activation optimization, viral loops, SEO, email marketing, social media, landing pages, and growth experiments.
---

# Growth Hacker Skill

Help founders and product teams accelerate growth through proven frameworks, tactical experiments, and ready-to-publish content.

## Core Principles

### Sean Ellis Principles
1. **Retention is the ultimate PMF test**; surveys are leading indicators
2. **Ignore "somewhat disappointed" users**—they dilute your must-have experience
3. **Customer acquisition is LAST, not first**: Activation → Engagement → Referral → Revenue → Acquisition
4. "If you're not efficient at converting, retaining, and monetizing, you can't find scalable acquisition"
5. **Qualitative + quantitative together** = better experiments
6. Ask users: "How did you find us? How do you normally find products like this?"

### Nikita Bier Principles
1. Look for **"latent demand"**—people going through distortive processes to get value
2. Three reasons people download apps: **make/save money, find love, unplug from reality**
3. If there's ANY uncertainty about PMF, you don't have it. **It's binary.**
4. **Every tap is a miracle**—optimize ruthlessly
5. **Test the BEST possible version** to eliminate confounding variables
6. **Marketing = Product**. Ads, in-app experience, and invites must all align
7. **Naming matters**—even affects invite behavior at critical moments

## Workflows

### 1. Product-Market Fit Assessment

Use when: User wants to assess if they have PMF or understand their core value proposition.

**Steps:**
1. Design PMF survey using the Sean Ellis question:
   - "How would you feel if you could no longer use [product]?"
   - Options: Very disappointed, Somewhat disappointed, Not disappointed
2. Target: Random sample of **activated users** (used 2+ times, within last 2 weeks)
3. Benchmark: **40% "very disappointed"** = leading indicator of PMF
4. **Critical follow-ups** for "very disappointed" users:
   - "What is the primary benefit you get from [product]?"
   - "Why is that benefit important to you?"
5. Analyze responses to identify:
   - Core value proposition (in customer language)
   - Who considers it a must-have
   - What they used before
   - What problem they're solving

**Output:** PMF score, core value statement, positioning recommendations, and next steps.

> For detailed frameworks, read `references/frameworks.md`

### 2. Growth Audit

Use when: User wants a comprehensive assessment of growth opportunities.

**Steps:**
1. Identify current growth stage (pre-PMF, early traction, scaling, mature)
2. Map existing channels and metrics across AARRR funnel
3. Identify biggest levers and gaps
4. **Prioritize in this order** (Sean Ellis sequence):
   - Activation (speed to value, onboarding)
   - Engagement (retention, habit formation)
   - Referral (viral loops, word of mouth)
   - Revenue (monetization, pricing)
   - Acquisition (channels, paid/organic)
5. ICE score top 5-10 experiments
6. Create prioritized growth plan

**Output:** Prioritized experiment roadmap with ICE scores.

### 3. Activation Optimization

Use when: User wants to improve onboarding, reduce churn, or increase activation rate.

**Steps:**
1. Map current time-to-value (how long until user experiences core benefit?)
2. Apply **3-second rule**: Can user experience value in first 3 seconds?
3. Identify biggest drop-off points in funnel
4. Diagnose problems:
   - Ask bounced users directly: "What happened?"
   - Look for inspiration from adjacent products
5. Design experiments to either:
   - **Reduce friction** (fewer steps, clearer UI, eliminate signup walls)
   - **Increase desire** (better value prop, social proof, urgency)
6. **Test best possible version** (eliminate confounding variables)

**Key insight from LogMeIn:** They improved signup-to-usage from 5% → 50% by focusing on onboarding. This enabled scaling paid channels from $10k/month to $1M/month.

> For detailed tactics, read `references/activation-playbook.md`

### 4. Latent Demand Discovery

Use when: User is exploring new product ideas or market opportunities.

**Steps:**
1. Look for people going through **distortive processes** to get value
   - Example: Sarahah was #1 app in US despite being entirely in Arabic
2. Identify signals of unmet demand:
   - Workarounds people are using
   - High engagement on "wrong" products
   - Forums/Reddit threads with repeated questions
3. Crystallize the **true motivation** (not surface behavior)
4. Design product that delivers that value **directly**

**Three core motivations** (Nikita Bier):
- Make or save money
- Find love/connection
- Unplug from reality

**Output:** Product opportunity hypothesis with evidence of latent demand.

### 5. Experiment Design

Use when: User has a growth hypothesis to test.

**Steps:**
1. Define hypothesis clearly: "We believe [change] will [impact] because [reason]"
2. **ICE score** the idea:
   - **Impact**: Best case, how much could this move the metric? (1-10)
   - **Confidence**: How sure are we this will work? (1-10)
   - **Ease**: How easy is this to implement? (1-10)
3. Design minimum viable test
4. Define success metrics and sample size
5. Plan iteration path: "If this works, then we'll..."

**Output:** Experiment brief ready to execute.

### 6. Content Generation

Use when: User needs marketing content (emails, social posts, landing pages).

**Steps:**
1. Identify channel and goal
2. **Use customer language** from PMF research
   - Example: Xobni used "drowning in email?" as hook because users said exactly that
3. Select appropriate template from `assets/templates/`
4. Adapt to product voice/positioning
5. Optimize for platform specifics
6. Include CTA and tracking suggestions

> For platform-specific tactics, read `references/platform-playbooks.md`

### 7. North Star Metric Selection

Use when: User needs help defining their key metric.

**Steps:**
1. Identify the core value delivered (from PMF research)
2. Design metric that reflects **units of value delivered**
3. Apply checklist:
   - [ ] Not a ratio (can be "up and to the right" over time)
   - [ ] Correlates to revenue growth
   - [ ] Reflects value to customers (not just business value)
   - [ ] Time-capped for focus (daily/weekly beats monthly)
4. Run 30-minute team alignment exercise

**Examples:**
- Airbnb: Nights booked
- Amazon: Monthly purchases
- Uber: Weekly rides
- Facebook: Daily active users (not monthly—this shift changed behavior significantly)

> For metrics guidance, read `references/metrics-guide.md`

## Key Frameworks Summary

| Framework | When to Use | Key Insight |
|-----------|-------------|-------------|
| **Sean Ellis PMF Test** | Assessing product-market fit | 40% "very disappointed" = leading indicator |
| **AARRR Funnel** | Mapping growth opportunities | Work backwards: Activation before Acquisition |
| **ICE Scoring** | Prioritizing experiments | Simple beats complex; enables crowdsourcing |
| **North Star Metric** | Aligning team on growth | Reflects value delivered, not revenue |
| **3-Second Rule** | Optimizing activation | Users must experience value in 3 seconds |
| **Latent Demand** | Finding opportunities | Look for distortive workarounds |

## Reference Files

- `references/frameworks.md` - Deep dive on PMF test, AARRR, ICE, North Star metrics with case studies
- `references/activation-playbook.md` - Speed to value tactics, friction reduction, testing methodology
- `references/platform-playbooks.md` - Channel-specific tactics for Twitter, LinkedIn, Product Hunt, etc.
- `references/metrics-guide.md` - KPIs by stage, cohort analysis, benchmarks

## Templates

- `assets/templates/pmf-survey.md` - PMF survey questions and follow-ups
- `assets/templates/email-sequences.md` - Welcome, re-engagement, launch emails
- `assets/templates/social-posts.md` - Twitter threads, LinkedIn posts
- `assets/templates/landing-page.md` - Hero section, social proof, CTA formulas

## Quick Reference: The Growth Sequence

Most founders do this:
```
Acquisition → Activation → Retention → Revenue → Referral
```

Sean Ellis says do this instead:
```
Activation → Engagement → Referral → Revenue → Acquisition
```

**Why?** Customer acquisition is so competitive that if you're not efficient at converting, retaining, and monetizing users, you'll never find scalable acquisition channels. Fix the leaky bucket first.

## Quick Reference: PMF Signals

**You have PMF if:**
- 40%+ say "very disappointed" if product disappeared
- Things are breaking every few days from growth
- You're measuring hourly actives, not daily
- "If your product's working, you'll know" (Nikita Bier)

**You don't have PMF if:**
- Any uncertainty exists
- You're trying to convince yourself
- Users need convincing to use it
- Growth requires constant paid acquisition
