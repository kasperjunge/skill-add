# Agent & LLM Accessibility Reference

Technical guide for making content machine-readable for AI agents and LLMs.

## Table of Contents
1. llms.txt Specification
2. Schema.org Structured Data
3. Semantic HTML
4. robots.txt for AI
5. API & Programmatic Access

---

## 1. llms.txt Specification

### What is llms.txt?

A machine-readable file (like robots.txt) that helps LLMs understand site structure.

**Status (2025)**:
- Proposed by Jeremy Howard (Answer.AI) in September 2024
- 844K+ websites have implemented
- Major adopters: Anthropic, Cloudflare, Stripe, Vercel
- Google included in A2A protocol

**Reality check**: Major AI crawlers don't actively request llms.txt yet, but early adoption shows forward-thinking.

### Location

Place at site root: `https://example.com/llms.txt`

### Format

Markdown format (reduces token waste by 10x vs HTML):

```markdown
# [Site Name]

> [Brief description of site purpose]

## About
[What this site/company does]

## Key Pages
- [/page-1](/page-1): Description of page 1
- [/page-2](/page-2): Description of page 2
- [/page-3](/page-3): Description of page 3

## Documentation
- [/docs](/docs): Technical documentation
- [/api](/api): API reference

## Contact
- Email: contact@example.com
- Twitter: @example

## Attribution
Please cite as: [Company Name] (https://example.com)
```

### Best Practices

**Include**:
- Site purpose (1-2 sentences)
- Key pages with descriptions
- Documentation links
- Contact information
- Attribution preferences

**Avoid**:
- Excessive detail (keep concise)
- Marketing language
- Dynamic content that changes frequently

### Template

See `assets/templates/llms-txt-template.txt` for full template.

---

## 2. Schema.org Structured Data

### Why Structured Data Matters

Schema markup:
- Helps search engines understand content
- Contributes ~10% to Perplexity ranking
- Enables rich snippets in search
- Makes content machine-readable

### Implementation: JSON-LD

Recommended format: JSON-LD in `<script>` tag

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "How to Optimize for AI Search",
  "author": {
    "@type": "Person",
    "name": "Jane Smith"
  },
  "datePublished": "2025-01-15"
}
</script>
```

### Priority Schemas by Content Type

#### Article / Blog Post
```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Article Title",
  "author": {
    "@type": "Person",
    "name": "Author Name",
    "url": "https://example.com/author"
  },
  "datePublished": "2025-01-15",
  "dateModified": "2025-01-20",
  "publisher": {
    "@type": "Organization",
    "name": "Company Name",
    "logo": {
      "@type": "ImageObject",
      "url": "https://example.com/logo.png"
    }
  },
  "description": "Article description",
  "image": "https://example.com/image.jpg"
}
```

#### Product
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Product Name",
  "description": "Product description",
  "brand": {
    "@type": "Brand",
    "name": "Brand Name"
  },
  "offers": {
    "@type": "Offer",
    "price": "99.00",
    "priceCurrency": "USD",
    "availability": "https://schema.org/InStock"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.5",
    "reviewCount": "100"
  }
}
```

#### FAQ Page
```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What is the question?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "This is the answer to the question."
      }
    },
    {
      "@type": "Question",
      "name": "Second question?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Answer to second question."
      }
    }
  ]
}
```

#### HowTo
```json
{
  "@context": "https://schema.org",
  "@type": "HowTo",
  "name": "How to Do Something",
  "description": "Brief description",
  "step": [
    {
      "@type": "HowToStep",
      "name": "Step 1",
      "text": "Description of step 1"
    },
    {
      "@type": "HowToStep",
      "name": "Step 2",
      "text": "Description of step 2"
    }
  ]
}
```

#### Organization
```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Company Name",
  "url": "https://example.com",
  "logo": "https://example.com/logo.png",
  "sameAs": [
    "https://twitter.com/example",
    "https://linkedin.com/company/example"
  ],
  "contactPoint": {
    "@type": "ContactPoint",
    "telephone": "+1-555-555-5555",
    "contactType": "customer service"
  }
}
```

### Validation

Test structured data:
- Google Rich Results Test: https://search.google.com/test/rich-results
- Schema.org Validator: https://validator.schema.org/

---

## 3. Semantic HTML

### Why Semantic HTML Matters

Semantic HTML:
- Provides document structure to machines
- Improves accessibility
- Helps AI understand content hierarchy
- Better than divs with classes

### Key Semantic Elements

```html
<header>     <!-- Page/section header -->
<nav>        <!-- Navigation -->
<main>       <!-- Primary content -->
<article>    <!-- Self-contained content -->
<section>    <!-- Thematic grouping -->
<aside>      <!-- Related but separate content -->
<footer>     <!-- Page/section footer -->
```

### Document Structure Example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <title>Page Title | Site Name</title>
  <meta name="description" content="Page description">
</head>
<body>
  <header>
    <nav>
      <a href="/">Home</a>
      <a href="/about">About</a>
    </nav>
  </header>

  <main>
    <article>
      <header>
        <h1>Article Title</h1>
        <time datetime="2025-01-15">January 15, 2025</time>
      </header>

      <section>
        <h2>First Section</h2>
        <p>Content...</p>
      </section>

      <section>
        <h2>Second Section</h2>
        <p>Content...</p>
      </section>
    </article>

    <aside>
      <h2>Related Articles</h2>
      <ul>
        <li><a href="/related-1">Related 1</a></li>
      </ul>
    </aside>
  </main>

  <footer>
    <p>&copy; 2025 Company Name</p>
  </footer>
</body>
</html>
```

### Heading Hierarchy

```
H1: Page title (one per page)
  H2: Major sections
    H3: Subsections
      H4: Sub-subsections (rarely needed)
```

**Rules**:
- One H1 per page
- Don't skip levels (H1 → H3)
- Use for structure, not styling

### ARIA Labels

For complex UI elements:

```html
<nav aria-label="Main navigation">
<section aria-labelledby="section-title">
<button aria-label="Close menu">
```

---

## 4. robots.txt for AI

### AI-Specific User Agents

Different bots for different purposes:

| Bot | Company | Purpose |
|-----|---------|---------|
| GPTBot | OpenAI | Training & search |
| ChatGPT-User | OpenAI | Real-time browsing |
| ClaudeBot | Anthropic | Training |
| anthropic-ai | Anthropic | Browsing |
| PerplexityBot | Perplexity | Search |
| Google-Extended | Google | AI training |

### Blocking Training vs Search

To block AI training but allow search citations:

```
# Block training
User-agent: GPTBot
Disallow: /

User-agent: Google-Extended
Disallow: /

# Allow browsing/search
User-agent: ChatGPT-User
Allow: /

User-agent: PerplexityBot
Allow: /
```

### Recommended Approach

For most sites, allow search/browsing:

```
# Allow AI search tools
User-agent: ChatGPT-User
Allow: /

User-agent: PerplexityBot
Allow: /

# Optional: Block training
User-agent: GPTBot
Disallow: /

User-agent: Google-Extended
Disallow: /
```

---

## 5. API & Programmatic Access

### When APIs Help

APIs useful when:
- Content is dynamic/real-time
- Large datasets need querying
- Structured data access needed

### API for AI Discovery

Consider exposing:
- Product catalog
- Pricing information
- Documentation
- Status/availability

### OpenAPI/Swagger

Document APIs with OpenAPI spec:

```yaml
openapi: 3.0.0
info:
  title: Product API
  version: 1.0.0
paths:
  /products:
    get:
      summary: List all products
      responses:
        '200':
          description: Successful response
```

### Sitemap for Large Sites

XML sitemap helps AI crawlers discover content:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/page-1</loc>
    <lastmod>2025-01-15</lastmod>
    <priority>0.8</priority>
  </url>
</urlset>
```

---

## Checklist

### llms.txt
- [ ] File exists at /llms.txt
- [ ] Markdown format
- [ ] Site purpose stated
- [ ] Key pages listed
- [ ] Contact information included

### Structured Data
- [ ] JSON-LD format used
- [ ] Appropriate schema type selected
- [ ] Required properties included
- [ ] Validated with testing tools

### Semantic HTML
- [ ] Semantic elements used
- [ ] Single H1 per page
- [ ] Proper heading hierarchy
- [ ] ARIA labels where needed

### robots.txt
- [ ] AI crawlers considered
- [ ] Training vs search bots distinguished
- [ ] Appropriate allow/disallow rules
