---
name: seo
description: Comprehensive SEO optimization covering traditional search (Google/Bing), answer engines (ChatGPT, Perplexity, AI Overviews), and agent/LLM accessibility (llms.txt, semantic HTML, structured data). Use for SEO audits, content discoverability, meta tags, structured data, llms.txt creation, citation optimization, Reddit/YouTube strategies, or programmatic SEO. Triggers include "SEO audit", "AEO", "optimize for ChatGPT", "citation optimization", "Reddit SEO strategy", "YouTube SEO", "llms.txt", "programmatic SEO", "answer engine optimization", or explicit "/seo".
---

# SEO Skill

Comprehensive SEO optimization covering three pillars:
1. **Traditional SEO** - Google/Bing (mid-funnel focus)
2. **Answer Engine Optimization (AEO)** - ChatGPT, Perplexity, AI Overviews
3. **Agent & LLM Accessibility** - llms.txt, structured data, semantic HTML

## Core Concept: The New SEO Landscape

Traditional SEO focused on ranking #1 to win clicks. With AI Overviews and LLM-powered search, the game has changed:

| Traditional SEO | Answer Engine Optimization |
|-----------------|---------------------------|
| Rank #1 → Win click | Be mentioned MANY times across citations |
| ~6 word queries | ~25 word queries (4x longer) |
| Requires domain authority (years) | Can win immediately via citations |
| Top-of-funnel discovery | AI handles top-funnel now |

**Key insight**: Mid-funnel intent is where SEO opportunity remains. AI handles discovery; SEO handles intent.

---

## Workflow Overview

Execute these 8 phases:
1. **Discovery & Fit Assessment** - Is SEO right for this product?
2. **Site/Content Analysis** - Current state assessment
3. **Traditional SEO Assessment** - Mid-funnel optimization
4. **Answer Engine Optimization** - AEO strategy
5. **Citation Strategy** - Multi-platform citation plan
6. **Agent & LLM Accessibility** - Technical accessibility
7. **Implementation/Creation** - Execute recommendations
8. **Monitoring & Measurement** - Track share of voice

---

## Phase 1: Discovery & Fit Assessment

**Goal**: Determine if SEO is right for this product and select workflow mode.

### Mode Selection

**Audit Mode** - Analyzing existing site/content:
- User provides URL or content
- Output: Recommendations, issues, implementation guide

**Creation Mode** - Generating optimized content:
- User provides topic, keywords, or brief
- Output: SEO-optimized content with all assets

### Critical Fit Assessment

Before proceeding, assess if SEO makes sense:

**SEO is likely a good fit if**:
- Clear search journey exists (users search to find this)
- Users convert online (not requiring sales team)
- Mid-funnel intent keywords exist
- Product solves a searchable problem

**SEO may NOT be right if**:
- No clear answer to "what will someone search to find this?"
- B2B SaaS with long sales cycles/committee decisions
- Products requiring sales motion to convert
- No online conversion path

**Read**: `references/traditional-seo.md` for "When NOT to do SEO" framework.

### Initial Context

Gather:
- Target URL or topic
- Primary goals (traffic, citations, conversions)
- Target audience
- Competitive context
- Funnel position (top/mid/bottom)

---

## Phase 2: Site/Content Analysis

**Goal**: Deep understanding of current state.

### For Audit Mode

1. **Fetch and analyze target URL**:
   - Use WebFetch to retrieve page content
   - Examine HTML structure, meta tags, headers
   - Check for structured data presence

2. **Content inventory**:
   - Main topics and themes
   - Content structure and hierarchy
   - Internal linking patterns

3. **Citation presence check**:
   - Search ChatGPT/Perplexity for relevant queries
   - Note which competitors are being cited
   - Identify citation gaps

### For Creation Mode

1. **Research target topic**:
   - Use WebSearch to understand landscape
   - Analyze top-ranking and top-cited content
   - Identify content gaps

2. **Question research**:
   - Transform keywords → questions
   - Identify follow-up questions users ask
   - Map the full question cluster

**Read**: `references/analysis-checklists.md` for detailed procedures.

---

## Phase 3: Traditional SEO Assessment (Mid-Funnel Focus)

**Goal**: Optimize for Google/Bing mid-funnel searches.

**Read**: `references/traditional-seo.md` for detailed guidance.

### On-Page Elements

#### Title Tags
- 50-60 characters
- Primary keyword near beginning
- Unique, compelling, accurate

#### Meta Descriptions
- 150-160 characters
- Include call-to-action
- Reflect page content accurately

#### Header Structure
- Single H1 per page
- Logical H2-H6 hierarchy
- Keywords in headers (natural, not stuffed)

### Content Quality

#### E-E-A-T Signals
- **Experience**: First-hand knowledge demonstrated
- **Expertise**: Credentials and depth shown
- **Authoritativeness**: Recognition from others
- **Trustworthiness**: Accuracy, transparency

#### Follow-Up Question Coverage
Critical for both SEO and AEO: Answer ALL subtopics and follow-up questions.
- Mine questions from sales calls, customer support
- Cover edge cases and specific use cases
- Structure content to address question clusters

### Help Center Optimization

Underrated SEO opportunity:
- Move help center from subdomain → subdirectory
- Cross-link help center pages
- Fill long-tail from support tickets
- Open to community for obscure questions

---

## Phase 4: Answer Engine Optimization (AEO)

**Goal**: Optimize for ChatGPT, Perplexity, AI Overviews citations.

**Read**: `references/answer-engine-optimization.md` for detailed methodology.

### Core AEO Concept

LLMs use RAG (Retrieval Augmented Generation) - they search, then summarize. Your goal: be mentioned in as many citations as possible.

### Question Research

Transform keywords → questions:
1. Take money keywords (yours and competitors' paid search)
2. Convert to question format
3. Include follow-up question variants

Example: "CRM software" →
- "What is the best CRM for small businesses?"
- "Which CRM integrates with Gmail?"
- "How much does CRM software cost?"

### Answer-Optimized Content

Structure content for citation:
- Lead with direct answers (first sentence should answer the query)
- Use clear, quotable statements
- Include unique data and statistics
- Demonstrate expertise with credentials

### Platform Considerations

| Platform | Citation Overlap with Google | Notes |
|----------|------------------------------|-------|
| ChatGPT | ~35% | Different ranking signals |
| Perplexity | ~70% | More Google-aligned |
| AI Overviews | High | Google's own summarization |

---

## Phase 5: Citation Strategy

**Goal**: Build presence across all citation sources.

**Read**: `references/citation-strategies.md` for platform-specific tactics.

### Citation Groups Framework

#### 1. Your Site
- Traditional SEO landing pages
- Help center content
- FAQ pages with question-answer format

#### 2. Video (YouTube/Vimeo)
- Huge B2B opportunity (few videos on technical topics)
- No community gatekeeping like Reddit
- Target high-LTV, non-glamorous keywords
- Example: "AI payment processing API tutorial"

#### 3. UGC (Reddit, Quora)
**Reddit Strategy** (most important):
- Spam does NOT work - fake accounts banned
- Winning approach:
  - Real account with history
  - Say who you are and where you work
  - Give genuinely useful answers
  - Even 5 good comments can help

**Quora Strategy**:
- Answer questions with expertise
- Link to resources where relevant
- Build topic authority

#### 4. Tier 1 Affiliates
- Dot Dash Meredith (Good Housekeeping, Investopedia, etc.)
- G2, Capterra, TrustRadius
- Industry publications

#### 5. Tier 2 Affiliates & Blogs
- Niche blogs in your space
- Guest posting (authentic, not spam)
- PR mentions

---

## Phase 6: Agent & LLM Accessibility

**Goal**: Make content machine-readable for AI agents.

**Read**: `references/agent-accessibility.md` for detailed guidance.

### llms.txt

A machine-readable file helping LLMs understand site structure.

**Location**: `/llms.txt` at site root

**Contents**:
- Site purpose and scope
- Key pages and purposes
- Content organization
- API/data access points
- Contact/attribution

**Run**: `scripts/generate_llms_txt.py` to create template.

### Structured Data (Schema.org)

Priority schemas by content type:

| Content Type | Schema |
|--------------|--------|
| Articles | `Article`, `BlogPosting` |
| Products | `Product`, `Offer` |
| FAQ | `FAQPage`, `Question` |
| How-to | `HowTo`, `Step` |
| Organizations | `Organization` |
| People | `Person` |

**Run**: `scripts/generate_schema.py` to create JSON-LD.

### Semantic HTML

- Proper heading hierarchy (H1 → H2 → H3)
- Semantic elements (`<article>`, `<section>`, `<nav>`)
- ARIA labels for accessibility
- Clear document outline

---

## Phase 7: Implementation/Creation

**Goal**: Execute optimization or generate content.

### Audit Mode: Prioritized Recommendations

Structure by priority:
1. **Critical**: Issues blocking discoverability
2. **High**: Significant impact improvements
3. **Medium**: Moderate impact optimizations
4. **Low**: Nice-to-have enhancements

For each recommendation include:
- What to change
- Why it matters
- How to implement (code snippet)
- Expected impact

### Creation Mode: Complete Package

Produce:
1. **Main content**: SEO and AEO optimized
2. **Meta tags**: Title, description, OG tags
3. **Structured data**: JSON-LD schema
4. **llms.txt entry**: If site-level content

**Use templates**: `assets/templates/` for consistent formatting.

---

## Phase 8: Monitoring & Measurement

**Goal**: Track success and iterate.

**Read**: `references/monitoring-measurement.md` for detailed methodology.

### Key Metrics

#### Share of Voice
- % of prompts where domain is cited
- Track across ChatGPT, Perplexity, Gemini

#### Answer Tracking
- Different from keyword tracking (answers vary per run)
- Track average rank and appearance frequency
- Monitor multiple question variants

#### Referral Traffic
- LLM traffic sources in analytics
- Conversion rates by source

### Experiment Framework

For citation strategies:
1. Select 100+ questions
2. Split into test (50) and control (50) groups
3. Intervene on test group only
4. Wait 2-4 weeks
5. Compare results
6. Reproduce successful experiments

### Weekly Monitoring

- Panel of 50-100 high-intent queries
- Log which domains are cited
- Track week-over-week changes

---

## Deliverable Generation

**Read**: `references/output-template.md` for full templates.

### Audit Deliverable

```markdown
# SEO Audit: [Site/Page Name]

## Executive Summary
## Fit Assessment
## Traditional SEO Findings
## AEO Findings
## Citation Strategy
## Agent Accessibility
## Prioritized Recommendations
## Implementation Checklist
## Monitoring Plan
```

### Creation Deliverable

```markdown
# SEO Content Package: [Topic]

## Optimized Content
[Main content]

## SEO Assets
- Meta tags
- Structured data (JSON-LD)
- llms.txt entry

## Citation Strategy
## Implementation Notes
## Success Metrics
```

---

## Quick Reference

### Conversion Benchmark
Webflow: **6X higher conversion** from LLM traffic vs Google search

### Citation Overlap
- ChatGPT ↔ Google: ~35%
- Perplexity ↔ Google: ~70%

### Content Freshness
Visibility drops 2-3 days post-publication (for timely topics)

### Reddit Rule
Even 5 authentic, useful comments > 10,000 spam comments

---

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `generate_llms_txt.py` | Create llms.txt template |
| `generate_schema.py` | Create JSON-LD structured data |
| `analyze_headers.py` | Extract/analyze header structure |
| `meta_generator.py` | Generate meta tags from content |
| `question_transformer.py` | Transform keywords → questions |
| `content_analyzer.py` | Analyze content for SEO factors |
