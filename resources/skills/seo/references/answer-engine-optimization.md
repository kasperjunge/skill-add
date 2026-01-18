# Answer Engine Optimization (AEO) Reference

Comprehensive guide to optimizing for ChatGPT, Perplexity, Google AI Overviews, and other LLM-powered search.

## Table of Contents
1. AEO Fundamentals
2. Head vs Tail Differences
3. Question Research
4. Answer-Optimized Content
5. Platform-Specific Strategies
6. Answer Tracking
7. Experiment Design

---

## 1. AEO Fundamentals

### What is AEO?

AEO (Answer Engine Optimization) = GEO (Generative Engine Optimization)

Core concept: LLMs use **RAG** (Retrieval Augmented Generation)
- They **search** for relevant content
- Then **summarize** the search results

This is NOT the same as training data. You can influence RAG immediately.

### Key Difference from Traditional SEO

| Traditional SEO | AEO |
|-----------------|-----|
| Rank #1 = Win | Be mentioned MANY times = Win |
| One URL wins | Multiple citations summarized |
| Domain authority takes years | Can win immediately via citations |
| ~6 word queries | ~25 word queries |

### The Citation Game

Your goal: **Be mentioned in as many citations as possible**

LLMs don't rank results #1-10 like Google. They summarize multiple sources. The product mentioned most often across citations typically appears first in answers.

---

## 2. Head vs Tail Differences

### The Head (Competitive Queries)

For queries like "best CRM software":
- Need to be mentioned across many citation sources
- Single URL ranking #1 doesn't win
- Brand mentions matter more than links

### The Tail (Long, Specific Queries)

The tail is **4x larger** in chat vs search:
- Average query: ~25 words vs ~6 words
- Follow-up questions create new queries
- Specific use cases asked

**Opportunity**: Many tail queries have never been asked in Google search.

**Examples of tail queries**:
- "Which CRM integrates with Gmail and has automation under $50/month?"
- "Best CRM for a 3-person marketing agency that does B2B consulting"
- "How do I migrate from Salesforce to HubSpot without losing custom fields?"

### Early Stage Advantage

Unlike traditional SEO:
- You don't need years of domain authority
- A Reddit comment can get you cited tomorrow
- A YouTube video can show up immediately
- New products get mentioned if people discuss them

---

## 3. Question Research

### Step 1: Transform Keywords to Questions

Take your money keywords and competitors' paid search terms:

```
Keyword: "project management software"

Questions:
- What is the best project management software for small teams?
- Which project management tool integrates with Slack?
- How much does project management software cost?
- What's the difference between Asana and Monday?
- Best free project management software for startups?
```

### Step 2: Map Follow-Up Questions

For each main question, identify likely follow-ups:

```
Main: "What's the best CRM for small business?"

Follow-ups:
- What features should I look for?
- How much should I pay?
- Do I need integrations?
- What about [specific competitor]?
- Can I migrate from spreadsheets?
```

### Step 3: Mine Real Questions

Sources:
- **Sales calls**: What questions do prospects ask?
- **Support tickets**: What do customers need help with?
- **Reddit**: What do people ask in your category?
- **Quora**: What questions get asked repeatedly?
- **ChatGPT/Perplexity**: Ask questions, note follow-ups suggested

### Question Categorization

| Type | Example | Priority |
|------|---------|----------|
| Commercial | "Best X for Y" | High |
| Comparison | "X vs Y" | High |
| How-to | "How to do X with Y" | Medium |
| Informational | "What is X" | Low (AI handles) |

---

## 4. Answer-Optimized Content

### The Citation-Worthy Formula

Content that gets cited:
1. **Leads with direct answer** (first sentence answers query)
2. **Clear, quotable statements**
3. **Unique data/statistics**
4. **Expert credentials demonstrated**

### Structure for Citation

```markdown
# [Question as Title]

[Direct answer in first sentence. This is what LLMs extract.]

## Key Points
- Point 1 with specific detail
- Point 2 with data
- Point 3 with example

## Detailed Explanation
[Supporting content...]

## Expert Take
[Credentials + insight]
```

### Writing Tips

**DO**:
- Answer the question immediately
- Use specific numbers and data
- Include expert credentials
- Create quotable one-liners
- Address follow-up questions

**DON'T**:
- Long introductions before answer
- Vague or hedging language
- Generic content anyone could write
- Missing the actual question

### Example Transformation

**Before (SEO-optimized)**:
```
In today's fast-paced business environment, choosing the right
CRM software is more important than ever. With so many options
available, it can be overwhelming to make the right choice...
```

**After (AEO-optimized)**:
```
The best CRM for small business in 2025 is HubSpot for most teams,
due to its free tier and ease of use. For sales-heavy teams,
Pipedrive offers better pipeline management at $14/month.
```

---

## 5. Platform-Specific Strategies

### ChatGPT

**Citation overlap with Google**: ~35%

- Uses Bing for real-time search
- Values recency for current topics
- Brand mentions matter
- Shopping results getting more visual

### Perplexity

**Citation overlap with Google**: ~70%

- More aligned with Google rankings
- Strong emphasis on authoritative sources
- FAQ-style content performs well
- Updates index daily (freshness matters)

### Google AI Overviews

- Uses Google's own index
- Heavily tied to traditional SEO
- Brand safety concerns limit some content
- Links appear within answer

### Meta AI

- Facebook/Instagram integration
- Consumer-focused queries
- Less B2B relevance currently

### Strategy by Platform

| Platform | Priority | Approach |
|----------|----------|----------|
| ChatGPT | High | Citation diversity, brand mentions |
| Perplexity | High | Traditional SEO + freshness |
| AI Overviews | High | Google SEO + structure |
| Meta AI | Low (B2B) | Consumer brands only |

---

## 6. Answer Tracking

### How Answer Tracking Differs

**Keyword tracking**: Same query → Same results
**Answer tracking**: Same query → Different answers each time

LLMs sample from a distribution. You need to:
- Ask questions multiple times
- Track appearance frequency
- Monitor average position when mentioned

### Key Metrics

**Share of Voice**: % of runs where you appear
```
Ask "best CRM" 100 times
You appear 35 times
Share of Voice = 35%
```

**Average Position**: When mentioned, where?
```
Position 1: 10 times
Position 2: 15 times
Position 3: 10 times
Average = 2.0
```

**Brand Mention**: Times brand mentioned (not just linked)

### Tools

60+ answer tracking tools exist. Selection criteria:
- Multi-platform support (ChatGPT, Perplexity, etc.)
- Historical tracking
- Competitor comparison
- Reasonable pricing

**Rule**: Use the cheapest tool that meets your needs. This is commodity functionality.

---

## 7. Experiment Design

### Why Experiments Matter

Most AEO "best practices" are unproven. Run your own experiments.

### Framework

**Step 1: Select Questions**
- Pick 100+ relevant questions
- Ensure current baseline tracking

**Step 2: Split Groups**
- 50 questions = Test group
- 50 questions = Control group
- Match difficulty/volume

**Step 3: Intervene on Test Only**
Examples:
- Reddit comments on test queries only
- YouTube videos for test queries only
- Landing pages for test queries only

**Step 4: Wait**
- 2-4 weeks minimum
- Track both groups

**Step 5: Compare**
- Did test group improve vs control?
- Statistical significance?

**Step 6: Reproduce**
- Success once = lucky
- Success 3x = pattern

### Common Experiments

| Experiment | Intervention | Measurement |
|------------|--------------|-------------|
| Reddit impact | 10 authentic comments | Share of voice change |
| YouTube impact | 5 videos on topics | Citation frequency |
| Landing page | New pages for questions | Appearance rate |
| Content refresh | Update old content | Position improvement |

### What We Know Works

Based on experiments:
- ✅ Traditional SEO (landing pages)
- ✅ YouTube videos (especially B2B)
- ✅ Authentic Reddit participation
- ✅ Help center optimization
- ⚠️ Paid affiliate mentions (expensive)
- ❌ Spam/fake accounts (banned)
- ❌ 100% AI content (detected/penalized)
