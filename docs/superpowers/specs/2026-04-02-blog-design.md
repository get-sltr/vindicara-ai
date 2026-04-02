# Blog Pages Design

**Date:** 2026-04-02
**Status:** Approved
**Approach:** Static Svelte pages, no markdown pipeline, full SEO + analytics + CTAs

## Objective

Launch a blog at vindicara.io/blog with 3 SEO-optimized posts targeting security engineers, compliance leads, and developers. Each post drives traffic to vindicara.io with UTM-tagged CTAs. Blog matches the existing dark design system.

## Routes and File Structure

```
site/src/routes/blog/
  +page.svelte                        # Blog index
  +layout.svelte                      # Shared blog layout (nav, footer, default meta)
  mcp-security-2026/
    +page.svelte                      # Post 1
  eu-ai-act-article-72-guide/
    +page.svelte                      # Post 2
  secure-ai-agents-5-minutes/
    +page.svelte                      # Post 3
```

Also modified:
- `site/src/routes/+page.svelte` (add Blog nav link)
- `site/static/sitemap.xml` (new file)
- `site/static/robots.txt` (update with sitemap reference)

## Blog Index (`/blog`)

- Dark design matching existing site (obsidian bg, glass panels, brand colors)
- Header: "Vindicara Blog" with subtitle "Security research, compliance guides, and engineering deep-dives for the agentic AI era."
- 3 post cards in a responsive grid (1-col mobile, 3-col desktop)
- Each card: category tag (colored pill), title, description (~2 lines), reading time, date
- Cards link to individual posts
- Reuses site nav and footer

## Blog Layout (`+layout.svelte`)

- Imports and reuses the main site navigation and footer
- Sets default meta tags (overridden by individual posts)
- Provides consistent article container styling: `max-w-3xl mx-auto` for readable line length

## Post Template (all 3 posts follow this)

### Head / SEO

Each post's `<svelte:head>` contains:
- `<title>` tag: "{Post Title} | Vindicara Blog"
- `<meta name="description">`: ~155 char summary targeting primary keywords
- `<link rel="canonical">`: `https://vindicara.io/blog/{slug}`
- Open Graph: `og:title`, `og:description`, `og:type=article`, `og:url`, `og:site_name=Vindicara`
- JSON-LD Article schema:
  ```json
  {
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "...",
    "datePublished": "2026-04-02",
    "author": {"@type": "Organization", "name": "Vindicara Security Research"},
    "publisher": {"@type": "Organization", "name": "Vindicara", "url": "https://vindicara.io"},
    "description": "..."
  }
  ```

### Article Structure

- Article header: category pill, `<h1>` title, subtitle, byline ("Vindicara Security Research"), date, reading time
- Article body: semantic HTML (`<article>`, `<section>`, `<h2>`, `<h3>`, `<p>`, `<pre>`, `<code>`)
- Mid-article CTA component (after ~60% of content)
- End-of-article CTA component
- "Related Posts" section at bottom linking to the other 2 posts

### CTA Component

Reusable pattern (inlined in each post, not a separate component file since there are only 3 posts):
- Glass-panel card with subtle gradient border
- Headline: "Secure your AI agents in minutes"
- Subtext: "pip install vindicara. Runtime protection in under 5 minutes."
- Two buttons:
  - "Start Building Free" linking to `https://vindicara.io/#get-started?utm_source=blog&utm_medium=cta&utm_campaign={post-slug}`
  - "View on GitHub" linking to `https://github.com/get-sltr/vindicara-ai?utm_source=blog&utm_medium=cta&utm_campaign={post-slug}`

### Article Styling

- Prose styling: `text-zinc-300` body text, `text-white` headings, `text-zinc-400` for secondary text
- Code blocks: same `code-block` class from main site
- Links: `text-brand-cyan hover:text-brand-cyan/80 underline`
- Section spacing: `mt-8` between sections, `mt-4` between paragraphs
- Images/diagrams: none needed (all content is text + code blocks)

## Post Content

### Post 1: "The State of MCP Security in 2026"

- **Slug:** `mcp-security-2026`
- **Category:** Research (brand-cyan pill)
- **Reading time:** 6 min
- **SEO targets:** "MCP security", "MCP OAuth", "MCP vulnerabilities", "Model Context Protocol security", "MCP server security audit"
- **Meta description:** "92% of MCP servers lack proper OAuth. We scanned real MCP server configurations and found critical vulnerabilities. Here is what we found and how to fix it."
- **Content outline (~1200 words):**
  1. The MCP adoption explosion: every major AI platform shipping MCP connectors
  2. The 92% OAuth gap: RSA Conference 2026 findings (cited with link)
  3. What we found: real Vindicara MCP scanner output showing a vulnerable server config (the actual JSON from tonight's scan with risk_score 0.85, 5 findings, CWE references)
  4. Common vulnerability patterns: no auth (CWE-306), dangerous tools (CWE-78), missing rate limits (CWE-770), overprivileged access (CWE-862), path traversal (CWE-22)
  5. What teams should do: 5 remediation steps matching the scanner output
  6. How Vindicara fills the gap: `pip install vindicara`, scan in seconds, enforce in production
- **Real data included:** MCP scan result JSON, remediation output

### Post 2: "EU AI Act Article 72: A Developer's Guide to Post-Market Monitoring"

- **Slug:** `eu-ai-act-article-72-guide`
- **Category:** Compliance (green-500 pill)
- **Reading time:** 5 min
- **SEO targets:** "EU AI Act Article 72", "AI compliance developer", "post-market monitoring AI", "EU AI Act enforcement 2026", "AI Act compliance automation"
- **Meta description:** "The EU AI Act enforcement deadline is August 2, 2026. Article 72 requires post-market monitoring for high-risk AI systems. Here is what developers need to know."
- **Content outline (~1000 words):**
  1. The deadline: August 2, 2026 (cited with EUR-Lex link), penalties up to 7% global revenue
  2. What Article 72 requires: post-market monitoring, real-world performance tracking, incident reporting, technical documentation
  3. What this means for engineering teams: you need audit trails, runtime monitoring, automated reporting
  4. The compliance frameworks landscape: EU AI Act, NIST AI RMF, SOC 2 (show real compliance/frameworks API response)
  5. Automating compliance evidence: how Vindicara turns runtime data into regulatory artifacts
  6. Getting started: `vc.compliance.generate(framework="eu-ai-act-article-72")` code example
- **Real data included:** Compliance frameworks API response JSON

### Post 3: "How to Secure Your AI Agents in 5 Minutes with Vindicara"

- **Slug:** `secure-ai-agents-5-minutes`
- **Category:** Tutorial (brand-purple pill)
- **Reading time:** 4 min
- **SEO targets:** "AI agent security tutorial", "AI guardrails quickstart", "secure AI agents", "AI runtime security Python", "vindicara quickstart"
- **Meta description:** "From pip install to runtime protection in under 5 minutes. Guard AI agent inputs and outputs, scan MCP servers, and enforce per-agent permissions with Vindicara."
- **Content outline (~800 words):**
  1. The problem: AI agents are autonomous, security is an afterthought
  2. Step 1 - Install: `pip install vindicara`
  3. Step 2 - Guard: real guard() call blocking PII (show actual API response with verdict: blocked, pii-detect rule)
  4. Step 3 - Scan MCP: real scan result showing risk assessment
  5. Step 4 - Agent IAM: register an agent with scoped permissions, show unauthorized tool being blocked (real API response with allowed: false)
  6. Step 5 - Monitor: drift detection endpoint, circuit breakers
  7. What is next: compliance reporting, behavioral baselines
- **Real data included:** Guard API response, MCP scan response, agent registration response, agent check response (all from tonight's tests)

## SEO Infrastructure

### sitemap.xml (new file: `site/static/sitemap.xml`)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://vindicara.io/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>
  <url><loc>https://vindicara.io/blog</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>
  <url><loc>https://vindicara.io/blog/mcp-security-2026</loc><changefreq>monthly</changefreq><priority>0.9</priority></url>
  <url><loc>https://vindicara.io/blog/eu-ai-act-article-72-guide</loc><changefreq>monthly</changefreq><priority>0.9</priority></url>
  <url><loc>https://vindicara.io/blog/secure-ai-agents-5-minutes</loc><changefreq>monthly</changefreq><priority>0.9</priority></url>
</urlset>
```

### robots.txt update

Add `Sitemap: https://vindicara.io/sitemap.xml` to existing robots.txt.

### Heading hierarchy

Every page: one `<h1>` (post title or "Vindicara Blog"), `<h2>` for sections, `<h3>` for subsections. No skipped levels.

### Internal linking

- Each post links to vindicara.io homepage sections using descriptive anchor text ("runtime security platform", "MCP security scanner", "compliance engine")
- Each post links to the other 2 posts in "Related Posts"
- Blog index links to all 3 posts
- Main site nav links to /blog

## Analytics

- GA4 (G-FXDPWWZ8F1) already installed globally in `app.html`, tracks all page views automatically
- CTA buttons use UTM parameters for campaign tracking:
  - `utm_source=blog`
  - `utm_medium=cta`
  - `utm_campaign={post-slug}` (e.g., `mcp-security-2026`)
- In GA4: Acquisition > Traffic acquisition > filter by campaign to see which post converts

## Navigation Update

Add "Blog" link to the main site nav in `site/src/routes/+page.svelte`:
- Desktop nav: add between "Pricing" and "Live Demo"
- Mobile nav: add in same position
- Style: same as other nav links (`text-zinc-400 hover:text-white transition-colors`)
- Links to `/blog`

## Non-Goals

- No markdown pipeline (mdsvex), no CMS
- No comments, no newsletter signup (just CTA to product)
- No social sharing buttons
- No blog-specific images or illustrations
- No pagination (only 3 posts)
- No RSS feed (can add later)
- No separate component files for blog elements (inline everything, only 3 posts)
