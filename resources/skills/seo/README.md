# SEO Skill for Claude Code

A comprehensive SEO optimization skill covering traditional search, answer engines, and LLM accessibility.

## The Problem

SEO has fundamentally changed. With AI Overviews, ChatGPT, and Perplexity handling discovery, the old playbook of "rank #1 → win click" no longer works.

| Traditional SEO | Answer Engine Optimization |
|-----------------|---------------------------|
| Rank #1 → Win click | Be mentioned across multiple citations |
| ~6 word queries | ~25 word queries (4x longer) |
| Requires domain authority (years) | Can win immediately via citations |
| Top-of-funnel discovery | AI handles top-funnel now |

**Key insight**: Mid-funnel intent is where SEO opportunity remains. AI handles discovery; SEO handles intent.

## What This Skill Does

This skill enables Claude to perform SEO audits, create optimized content, and develop citation strategies across three pillars:

### 1. Traditional SEO
Google/Bing optimization with a mid-funnel focus:
- On-page optimization (titles, meta descriptions, headers)
- E-E-A-T signals (Experience, Expertise, Authoritativeness, Trust)
- Help center optimization strategies
- Content structure and internal linking

### 2. Answer Engine Optimization (AEO)
Optimize for ChatGPT, Perplexity, and Google AI Overviews:
- Question-based keyword research
- Citation-optimized content structure
- Follow-up question coverage
- Platform-specific strategies

### 3. Agent & LLM Accessibility
Make your content machine-readable:
- `llms.txt` file generation
- Schema.org structured data (JSON-LD)
- Semantic HTML optimization
- API/data accessibility

## Key Stats

- **6X higher conversion** from LLM traffic vs Google search (Webflow data)
- **~35% overlap** between ChatGPT and Google citations
- **~70% overlap** between Perplexity and Google citations
- Content freshness drops **2-3 days** post-publication for timely topics

## 8-Phase Workflow

1. **Discovery & Fit Assessment** - Is SEO right for this product?
2. **Site/Content Analysis** - Current state assessment
3. **Traditional SEO Assessment** - Mid-funnel optimization
4. **Answer Engine Optimization** - AEO strategy
5. **Citation Strategy** - Multi-platform citation plan
6. **Agent & LLM Accessibility** - Technical accessibility
7. **Implementation/Creation** - Execute recommendations
8. **Monitoring & Measurement** - Track share of voice

## Usage

```
/seo                                    # Start SEO analysis
/seo audit my website                   # Full SEO audit
/seo create an AEO strategy             # Answer engine optimization
/seo how do I show up in ChatGPT?       # Citation strategy
/seo create an llms.txt file            # LLM accessibility
/seo optimize for Perplexity            # Platform-specific optimization
```

## Included Tools

### Python Scripts

| Script | Purpose |
|--------|---------|
| `generate_llms_txt.py` | Generate llms.txt files for LLM accessibility |
| `generate_schema.py` | Create JSON-LD structured data |
| `analyze_headers.py` | Extract and analyze header structure |
| `meta_generator.py` | Generate optimized meta tags |
| `question_transformer.py` | Transform keywords into questions for AEO |
| `content_analyzer.py` | Analyze content for SEO factors |

### Templates

- **llms.txt template** - Machine-readable site description
- **Meta tags template** - Title, description, Open Graph tags
- **Schema templates** - Article, Product, FAQ, HowTo, Organization, Person

## Project Structure

```
seo/
├── SKILL.md                    # Main skill workflow
├── README.md                   # This file
├── references/
│   ├── traditional-seo.md      # Google/Bing optimization guide
│   ├── answer-engine-optimization.md  # AEO methodology
│   ├── citation-strategies.md  # Platform-specific tactics
│   ├── agent-accessibility.md  # llms.txt, schema.org
│   ├── analysis-checklists.md  # Audit procedures
│   ├── monitoring-measurement.md  # Answer tracking
│   └── output-template.md      # Deliverable templates
├── scripts/
│   ├── generate_llms_txt.py
│   ├── generate_schema.py
│   ├── analyze_headers.py
│   ├── meta_generator.py
│   ├── question_transformer.py
│   └── content_analyzer.py
└── assets/
    └── templates/
        ├── llms-txt-template.txt
        ├── meta-tags-template.html
        └── schema-templates/
            ├── article.json
            ├── product.json
            ├── faq.json
            ├── howto.json
            ├── organization.json
            └── person.json
```

## Citation Strategy Framework

The skill covers five citation groups:

1. **Your Site** - Landing pages, help center, FAQs
2. **Video (YouTube)** - High-LTV B2B opportunity with low competition
3. **UGC (Reddit, Quora)** - Authentic engagement over spam
4. **Tier 1 Affiliates** - G2, Capterra, industry publications
5. **Tier 2 Affiliates & Blogs** - Niche blogs, guest posting, PR

### Reddit Strategy

> Even 5 authentic, useful comments > 10,000 spam comments

The skill emphasizes genuine engagement:
- Real account with history
- Transparent about who you are
- Genuinely useful answers
- No fake accounts or spam

## Sources & Credits

This skill incorporates insights from:
- **Ethan Smith** (Graphite CEO) - Answer Engine Optimization expert
- **Eli Schwartz** - Author of "Product-Led SEO"
- Industry research on llms.txt, GEO, and AI search optimization

## Installation

This skill is part of the [agent-resources](https://github.com/kasperjunge/agent-resources) collection. To use it:

1. Clone the repository
2. Place the `seo/` folder in your Claude Code skills directory
3. Invoke with `/seo` or related triggers

## Triggers

The skill activates on:
- "SEO audit"
- "AEO" / "Answer Engine Optimization"
- "optimize for ChatGPT/Perplexity"
- "citation optimization"
- "Reddit SEO strategy"
- "YouTube SEO"
- "llms.txt"
- "programmatic SEO"
- Explicit `/seo`

## License

Part of the agent-resources skill collection.
