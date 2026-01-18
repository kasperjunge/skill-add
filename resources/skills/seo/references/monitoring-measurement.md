# Monitoring & Measurement Reference

Detailed guide to tracking SEO and AEO success.

## Table of Contents
1. Traditional SEO Metrics
2. Answer Engine Metrics
3. Answer Tracking Methodology
4. Experiment Framework
5. Reporting Templates

---

## 1. Traditional SEO Metrics

### Traffic Metrics

| Metric | Description | Tool |
|--------|-------------|------|
| Organic Sessions | Visits from search | Google Analytics |
| Organic Users | Unique visitors from search | Google Analytics |
| Impressions | Times shown in search | Search Console |
| Clicks | Times clicked from search | Search Console |
| CTR | Clicks / Impressions | Search Console |

### Ranking Metrics

| Metric | Description | Tool |
|--------|-------------|------|
| Average Position | Ranking position for queries | Search Console |
| Keyword Rankings | Position for specific keywords | Rank tracker |
| SERP Features | Featured snippets, etc. | Rank tracker |

### Conversion Metrics

| Metric | Description | Tool |
|--------|-------------|------|
| Goal Completions | Conversions from organic | Google Analytics |
| Conversion Rate | Conversions / Sessions | Google Analytics |
| Revenue | Revenue from organic | Google Analytics |

### What to Track

**Weekly**:
- Traffic trends
- Major ranking changes
- Conversion rates

**Monthly**:
- Traffic vs. previous month/year
- Ranking distribution
- Content performance

**Quarterly**:
- ROI analysis
- Competitive positioning
- Strategy review

---

## 2. Answer Engine Metrics

### Share of Voice

**Definition**: Percentage of times you appear in AI answers for target queries.

**Calculation**:
```
Ask question 100 times
You appear 35 times
Share of Voice = 35%
```

### Brand Mention Rate

**Definition**: Times your brand is mentioned in AI answers (even without citation).

**Types**:
- Direct mention (brand name in answer)
- Citation mention (in sources)
- Implicit mention (description matches your product)

### Average Position

**Definition**: When you do appear, average position in citations or answer text.

**Calculation**:
```
Position 1: 10 appearances
Position 2: 15 appearances
Position 3: 10 appearances

Average Position = (10×1 + 15×2 + 10×3) / 35 = 2.0
```

### Citation Diversity

**Definition**: Number of unique sources citing your content.

**Track**:
- Which citation sources mention you
- Frequency per source
- New vs. recurring sources

### LLM Referral Traffic

**Definition**: Traffic coming from LLM sources.

**Identify in Analytics**:
- Referrer contains "chat.openai.com"
- Referrer contains "perplexity.ai"
- Direct traffic spike after LLM mention

---

## 3. Answer Tracking Methodology

### Why It's Different

Keyword tracking: Same query → Same result
Answer tracking: Same query → Different result each time

LLMs sample from probability distributions. Results vary.

### Tracking Approach

**Step 1: Build Query Set**
- 50-100 target queries
- Include question variants
- Mix of head and tail

**Step 2: Multi-Run Sampling**
- Ask each query multiple times (10-20x)
- Record all responses
- Note citations for each

**Step 3: Calculate Metrics**
- Share of voice (appearance %)
- Average position when appearing
- Citation sources

**Step 4: Track Over Time**
- Weekly or bi-weekly sampling
- Same queries each time
- Compare trends

### Platform Coverage

Track across multiple platforms:
- ChatGPT (with search enabled)
- Perplexity
- Google AI Overview
- Claude (if applicable)

### Tools

60+ answer tracking tools exist. Evaluate:
- Multi-platform support
- Historical tracking
- Competitor comparison
- Export capabilities
- Pricing

**Rule**: Use the cheapest tool that meets your needs.

### Manual Tracking (Low Volume)

For small scale, manual tracking works:

```markdown
| Query | Date | Platform | You Appeared? | Position | Top Citations |
|-------|------|----------|---------------|----------|---------------|
| "best X" | 1/15 | ChatGPT | Yes | 2 | [list] |
| "best X" | 1/15 | Perplexity | No | - | [list] |
```

---

## 4. Experiment Framework

### Why Experiment?

Most AEO "best practices" are unproven. Test for your situation.

### Experiment Structure

```
Hypothesis: [Intervention] will increase [metric] by [amount]

Setup:
- 100 target questions
- 50 test group, 50 control group
- Baseline measurement

Intervention (test group only):
- [Specific action]

Timeline:
- Week 1-2: Baseline
- Week 3: Intervention
- Week 4-6: Measurement

Analysis:
- Test group change vs. control group change
- Statistical significance
```

### Example Experiments

#### Reddit Intervention
```
Hypothesis: 10 authentic Reddit comments will increase
share of voice by 15% for related queries.

Setup:
- 50 queries where Reddit is cited
- 25 test, 25 control

Intervention:
- Post 10 helpful comments on threads
  related to test queries only

Timeline: 4 weeks

Measurement:
- Share of voice change test vs. control
```

#### YouTube Intervention
```
Hypothesis: 5 YouTube videos will result in video
citations for related queries.

Setup:
- 50 queries with no current video citations
- 25 test, 25 control

Intervention:
- Create 5 videos targeting test queries

Timeline: 6 weeks (account for indexing)

Measurement:
- Video citation rate test vs. control
```

#### Content Refresh
```
Hypothesis: Updating content to answer questions directly
will increase citation rate by 20%.

Setup:
- 50 existing pages
- 25 test, 25 control

Intervention:
- Rewrite test pages with direct answers first
- Add FAQ section
- Update with current data

Timeline: 4 weeks

Measurement:
- Citation rate change test vs. control
```

### Reproducibility

One successful experiment = possibly luck
Three successful experiments = pattern

Always reproduce experiments before scaling.

---

## 5. Reporting Templates

### Weekly Report

```markdown
# SEO/AEO Weekly Report: [Date Range]

## Summary
- Organic traffic: [number] ([+/-X%] WoW)
- LLM referral traffic: [number] ([+/-X%] WoW)
- Share of voice: [X%] ([+/-X%] WoW)

## Key Wins
- [Win 1]
- [Win 2]

## Key Issues
- [Issue 1]
- [Issue 2]

## Actions This Week
- [ ] Action 1
- [ ] Action 2

## Next Week Focus
- Focus area 1
- Focus area 2
```

### Monthly Report

```markdown
# SEO/AEO Monthly Report: [Month]

## Executive Summary
[2-3 sentences on overall performance]

## Traffic
| Metric | This Month | Last Month | MoM Change | YoY Change |
|--------|------------|------------|------------|------------|
| Organic Sessions | | | | |
| LLM Referrals | | | | |

## Rankings/Share of Voice
| Query Category | Avg Position/SoV | Change |
|----------------|------------------|--------|
| Category 1 | | |
| Category 2 | | |

## Conversions
| Metric | This Month | Last Month | Change |
|--------|------------|------------|--------|
| Goal Completions | | | |
| Conversion Rate | | | |
| Revenue | | | |

## Citation Presence
| Platform | This Month | Last Month | Change |
|----------|------------|------------|--------|
| Reddit | | | |
| YouTube | | | |
| G2 | | | |

## Content Published
- [Content 1]: Performance summary
- [Content 2]: Performance summary

## Technical Updates
- [Update 1]
- [Update 2]

## Experiment Results
- [Experiment 1]: Result
- [Experiment 2]: Result

## Next Month Priorities
1. Priority 1
2. Priority 2
3. Priority 3

## Resource Needs
- [Need 1]
- [Need 2]
```

### Quarterly Business Review

```markdown
# SEO/AEO Quarterly Review: [Quarter]

## Executive Summary
[Key highlights and business impact]

## Performance vs. Goals
| Goal | Target | Actual | Status |
|------|--------|--------|--------|
| Goal 1 | | | |
| Goal 2 | | | |

## Traffic Trends
[Chart: 13-week traffic trend]

## Share of Voice Trends
[Chart: 13-week SoV trend by platform]

## ROI Analysis
| Investment | Return | ROI |
|------------|--------|-----|
| Content | | |
| Technical | | |
| Tools | | |
| Total | | |

## Competitive Position
- Position vs. Competitor A
- Position vs. Competitor B

## Strategy Performance
What worked:
- Strategy 1
- Strategy 2

What didn't work:
- Strategy 3
- Strategy 4

## Next Quarter Strategy
1. Strategic priority 1
2. Strategic priority 2
3. Strategic priority 3

## Budget Request
| Item | Amount | Justification |
|------|--------|---------------|
| Item 1 | | |
| Item 2 | | |
```

---

## KPI Dashboard

### Recommended Metrics to Track

**SEO Foundation**:
- Organic sessions (weekly)
- Organic conversions (weekly)
- Average position (weekly)

**AEO Performance**:
- Share of voice (bi-weekly)
- Brand mention rate (bi-weekly)
- LLM referral traffic (weekly)

**Citation Health**:
- Citation diversity (monthly)
- Platform presence (monthly)

**Experiments**:
- Active experiments (ongoing)
- Success rate (quarterly)
