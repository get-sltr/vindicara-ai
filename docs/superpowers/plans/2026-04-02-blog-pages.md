# Blog Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Launch a blog at vindicara.io/blog with 3 SEO-optimized posts, full structured data, UTM-tagged CTAs, sitemap, and nav integration.

**Architecture:** Static Svelte pages under `site/src/routes/blog/`. Blog layout provides shared nav/footer/meta. Each post is a standalone `.svelte` file with full SEO head tags, JSON-LD, and inline CTA blocks. No markdown pipeline, no CMS.

**Tech Stack:** SvelteKit 2.50, TailwindCSS 4.2, JSON-LD structured data, GA4 (already installed).

**Spec:** `docs/superpowers/specs/2026-04-02-blog-design.md`

---

### Task 1: Blog Layout and SEO Infrastructure

**Files:**
- Create: `site/src/routes/blog/+layout.svelte`
- Create: `site/static/sitemap.xml`
- Modify: `site/static/robots.txt`

- [ ] **Step 1: Create the blog layout**

Create `site/src/routes/blog/+layout.svelte`:

```svelte
<script lang="ts">
  import '../../app.css';
  import favicon from '$lib/assets/favicon.svg';

  let { children } = $props();

  let mobileMenuOpen = $state(false);
</script>

<svelte:head>
  <link rel="icon" href={favicon} />
  <meta property="og:site_name" content="Vindicara" />
  <meta name="twitter:site" content="@vindicara" />
  <meta name="theme-color" content="#0a0a0f" />
</svelte:head>

<!-- NAV -->
<nav class="fixed top-0 w-full z-50 bg-obsidian/60 backdrop-blur-2xl border-b border-white/5">
  <div class="max-w-screen-2xl mx-auto px-6 flex items-center justify-between h-16">
    <a href="/" class="flex items-center gap-2">
      <div class="w-8 h-8 rounded-lg bg-brand-red flex items-center justify-center">
        <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
        </svg>
      </div>
      <span class="text-lg font-bold tracking-tight">Vindicara</span>
    </a>

    <div class="hidden md:flex items-center gap-8 text-sm text-zinc-400">
      <a href="/#platform" class="hover:text-white transition-colors">Platform</a>
      <a href="/#mcp-security" class="hover:text-white transition-colors">MCP Security</a>
      <a href="/blog" class="hover:text-white transition-colors text-white">Blog</a>
      <a href="/#pricing" class="hover:text-white transition-colors">Pricing</a>
    </div>

    <div class="hidden md:flex items-center gap-3">
      <a href="https://github.com/get-sltr/vindicara-ai" class="btn-secondary text-xs px-4 py-2">
        <svg class="w-4 h-4 mr-1.5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
        GitHub
      </a>
      <a href="https://d1xzz26fz4.execute-api.us-east-1.amazonaws.com/docs" class="btn-primary text-xs px-4 py-2">Get API Key</a>
    </div>

    <button
      class="md:hidden text-zinc-400 hover:text-white"
      onclick={() => mobileMenuOpen = !mobileMenuOpen}
    >
      <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        {#if mobileMenuOpen}
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
        {:else}
          <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
        {/if}
      </svg>
    </button>
  </div>

  {#if mobileMenuOpen}
    <div class="md:hidden border-t border-white/5 bg-obsidian/95 backdrop-blur-2xl px-6 py-4 space-y-3">
      <a href="/#platform" class="block text-sm text-zinc-400 hover:text-white">Platform</a>
      <a href="/#mcp-security" class="block text-sm text-zinc-400 hover:text-white">MCP Security</a>
      <a href="/blog" class="block text-sm text-white">Blog</a>
      <a href="/#pricing" class="block text-sm text-zinc-400 hover:text-white">Pricing</a>
      <div class="flex gap-3 pt-2">
        <a href="https://github.com/get-sltr/vindicara-ai" class="btn-secondary text-xs px-4 py-2">GitHub</a>
        <a href="https://d1xzz26fz4.execute-api.us-east-1.amazonaws.com/docs" class="btn-primary text-xs px-4 py-2">Get API Key</a>
      </div>
    </div>
  {/if}
</nav>

<!-- CONTENT -->
<main class="pt-16">
  {@render children()}
</main>

<!-- FOOTER -->
<footer class="w-full border-t border-white/5 bg-obsidian relative z-20">
  <div class="max-w-screen-xl mx-auto px-6 py-16">
    <div class="grid grid-cols-2 md:grid-cols-5 gap-8">
      <div class="col-span-2 md:col-span-1">
        <div class="flex items-center gap-2 mb-4">
          <div class="w-7 h-7 rounded-md bg-brand-red flex items-center justify-center">
            <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
            </svg>
          </div>
          <span class="font-bold">Vindicara</span>
        </div>
        <p class="text-sm text-zinc-500 leading-relaxed">
          Runtime security for autonomous AI. Model-agnostic. Developer-first. Independent.
        </p>
      </div>

      <div>
        <h4 class="text-sm font-semibold mb-4">Product</h4>
        <ul class="space-y-2 text-sm text-zinc-500">
          <li><a href="/#platform" class="hover:text-white transition-colors">Platform</a></li>
          <li><a href="/#mcp-security" class="hover:text-white transition-colors">MCP Security</a></li>
          <li><a href="/#pricing" class="hover:text-white transition-colors">Pricing</a></li>
          <li><a href="/blog" class="hover:text-white transition-colors">Blog</a></li>
        </ul>
      </div>

      <div>
        <h4 class="text-sm font-semibold mb-4">Company</h4>
        <ul class="space-y-2 text-sm text-zinc-500">
          <li><a href="mailto:hello@vindicara.io" class="hover:text-white transition-colors">Contact</a></li>
          <li><a href="https://github.com/get-sltr/vindicara-ai" class="hover:text-white transition-colors">GitHub</a></li>
          <li><a href="https://x.com/vindicara" class="hover:text-white transition-colors">Twitter / X</a></li>
        </ul>
      </div>

      <div>
        <h4 class="text-sm font-semibold mb-4">Legal</h4>
        <ul class="space-y-2 text-sm text-zinc-500">
          <li><a href="mailto:legal@vindicara.io?subject=Privacy%20Policy" class="hover:text-white transition-colors">Privacy Policy</a></li>
          <li><a href="mailto:legal@vindicara.io?subject=Terms%20of%20Service" class="hover:text-white transition-colors">Terms of Service</a></li>
          <li><a href="mailto:security@vindicara.io" class="hover:text-white transition-colors">Security</a></li>
          <li><a href="mailto:legal@vindicara.io" class="hover:text-white transition-colors">DPA</a></li>
        </ul>
      </div>

      <div>
        <h4 class="text-sm font-semibold mb-4">Sources</h4>
        <ul class="space-y-2 text-sm text-zinc-500">
          <li><a href="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689" target="_blank" rel="noopener noreferrer" class="hover:text-white transition-colors">EU AI Act (2024/1689)</a></li>
          <li><a href="https://www.rsaconference.com/library/presentation/usa/2026/the-state-of-mcp-security" target="_blank" rel="noopener noreferrer" class="hover:text-white transition-colors">RSA Conference 2026</a></li>
          <li><a href="https://www.gartner.com/en/newsroom/press-releases/2025-03-agentic-ai-predictions" target="_blank" rel="noopener noreferrer" class="hover:text-white transition-colors">Gartner Predicts 2025</a></li>
        </ul>
      </div>
    </div>

    <div class="mt-12 pt-8 border-t border-white/5 flex flex-col md:flex-row items-center justify-between gap-4">
      <p class="text-xs text-zinc-600">&copy; 2026 Vindicara, Inc. All rights reserved.</p>
      <div class="flex items-center gap-4">
        <a href="https://github.com/get-sltr/vindicara-ai" class="text-zinc-600 hover:text-white transition-colors">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
        </a>
        <a href="https://x.com/vindicara" class="text-zinc-600 hover:text-white transition-colors">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
        </a>
        <a href="https://linkedin.com/company/vindicara" class="text-zinc-600 hover:text-white transition-colors">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
        </a>
      </div>
    </div>
  </div>
</footer>
```

- [ ] **Step 2: Create sitemap.xml**

Create `site/static/sitemap.xml`:

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

- [ ] **Step 3: Update robots.txt**

Replace the contents of `site/static/robots.txt` with:

```
User-agent: *
Disallow:

Sitemap: https://vindicara.io/sitemap.xml
```

- [ ] **Step 4: Commit**

```bash
git add site/src/routes/blog/+layout.svelte site/static/sitemap.xml site/static/robots.txt
git commit -m "feat(blog): add blog layout, sitemap, and robots.txt"
```

---

### Task 2: Blog Index Page

**Files:**
- Create: `site/src/routes/blog/+page.svelte`

- [ ] **Step 1: Create the blog index page**

Create `site/src/routes/blog/+page.svelte`:

```svelte
<svelte:head>
  <title>Blog | Vindicara</title>
  <meta name="description" content="Security research, compliance guides, and engineering deep-dives for the agentic AI era. From the team building the runtime security layer for AI agents." />
  <link rel="canonical" href="https://vindicara.io/blog" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="https://vindicara.io/blog" />
  <meta property="og:title" content="Blog | Vindicara" />
  <meta property="og:description" content="Security research, compliance guides, and engineering deep-dives for the agentic AI era." />
  <meta name="twitter:card" content="summary" />
  <meta name="twitter:title" content="Blog | Vindicara" />
  <meta name="twitter:description" content="Security research, compliance guides, and engineering deep-dives for the agentic AI era." />
</svelte:head>

<section class="py-24">
  <div class="max-w-screen-xl mx-auto px-6">
    <div class="text-center mb-16">
      <p class="text-brand-red text-sm font-semibold uppercase tracking-wider mb-3">Blog</p>
      <h1 class="text-4xl sm:text-5xl font-bold tracking-tight">Vindicara Blog</h1>
      <p class="mt-4 text-zinc-400 text-lg max-w-2xl mx-auto">
        Security research, compliance guides, and engineering deep-dives for the agentic AI era.
      </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
      <!-- Post 1: MCP Security -->
      <a href="/blog/mcp-security-2026" class="glass-panel rounded-xl p-6 hover:border-brand-cyan/30 transition-colors group block">
        <div class="flex items-center gap-2 mb-4">
          <span class="text-[10px] font-bold uppercase tracking-wider bg-brand-cyan/10 text-brand-cyan border border-brand-cyan/20 rounded-full px-2.5 py-0.5">Research</span>
          <span class="text-[10px] text-zinc-600">6 min read</span>
        </div>
        <h2 class="text-lg font-semibold mb-2 group-hover:text-brand-cyan transition-colors">The State of MCP Security in 2026</h2>
        <p class="text-sm text-zinc-400 leading-relaxed">92% of MCP servers lack proper OAuth. We scanned real configurations and found critical vulnerabilities. Here is what we found.</p>
        <p class="text-xs text-zinc-600 mt-4">April 2, 2026</p>
      </a>

      <!-- Post 2: EU AI Act -->
      <a href="/blog/eu-ai-act-article-72-guide" class="glass-panel rounded-xl p-6 hover:border-green-500/30 transition-colors group block">
        <div class="flex items-center gap-2 mb-4">
          <span class="text-[10px] font-bold uppercase tracking-wider bg-green-500/10 text-green-500 border border-green-500/20 rounded-full px-2.5 py-0.5">Compliance</span>
          <span class="text-[10px] text-zinc-600">5 min read</span>
        </div>
        <h2 class="text-lg font-semibold mb-2 group-hover:text-green-400 transition-colors">EU AI Act Article 72: A Developer's Guide</h2>
        <p class="text-sm text-zinc-400 leading-relaxed">The enforcement deadline is August 2, 2026. Article 72 requires post-market monitoring for high-risk AI systems. Here is what developers need to know.</p>
        <p class="text-xs text-zinc-600 mt-4">April 2, 2026</p>
      </a>

      <!-- Post 3: Quickstart -->
      <a href="/blog/secure-ai-agents-5-minutes" class="glass-panel rounded-xl p-6 hover:border-brand-purple/30 transition-colors group block">
        <div class="flex items-center gap-2 mb-4">
          <span class="text-[10px] font-bold uppercase tracking-wider bg-brand-purple/10 text-brand-purple border border-brand-purple/20 rounded-full px-2.5 py-0.5">Tutorial</span>
          <span class="text-[10px] text-zinc-600">4 min read</span>
        </div>
        <h2 class="text-lg font-semibold mb-2 group-hover:text-brand-purple transition-colors">How to Secure Your AI Agents in 5 Minutes</h2>
        <p class="text-sm text-zinc-400 leading-relaxed">From pip install to runtime protection. Guard inputs and outputs, scan MCP servers, and enforce per-agent permissions.</p>
        <p class="text-xs text-zinc-600 mt-4">April 2, 2026</p>
      </a>
    </div>
  </div>
</section>
```

- [ ] **Step 2: Commit**

```bash
git add site/src/routes/blog/+page.svelte
git commit -m "feat(blog): add blog index page with 3 post cards"
```

---

### Task 3: Post 1 - The State of MCP Security in 2026

**Files:**
- Create: `site/src/routes/blog/mcp-security-2026/+page.svelte`

- [ ] **Step 1: Create the post**

Create `site/src/routes/blog/mcp-security-2026/+page.svelte` with the full content. This is the longest file in the plan. The post content covers: MCP adoption, the 92% OAuth gap, real scan output, common vulnerability patterns, remediation guidance, and how Vindicara fills the gap.

The file must contain:
- `<svelte:head>` with title, meta description, canonical, OG tags, and JSON-LD Article schema
- Article header with category pill, h1, subtitle, byline, date, reading time
- Article body with semantic HTML sections
- Mid-article CTA
- End-of-article CTA
- Related posts section

Due to the length, the subagent implementing this task should write the complete file. Here is the exact structure and content:

**SEO Head:**
- Title: "The State of MCP Security in 2026 | Vindicara Blog"
- Meta description: "92% of MCP servers lack proper OAuth. We scanned real MCP server configurations and found critical vulnerabilities including missing authentication, dangerous tools, and no rate limiting."
- Canonical: `https://vindicara.io/blog/mcp-security-2026`
- JSON-LD type: Article, datePublished: 2026-04-02, author: Vindicara Security Research

**Article content sections (use `<h2>` for each):**

1. **"The MCP adoption explosion"** - Every major AI platform (Microsoft, Google, Anthropic, OpenAI, Salesforce) is shipping MCP connectors. MCP servers act as bridges between AI agents and enterprise infrastructure: databases, CRMs, file systems, APIs. Gartner projects 40% of enterprise apps will embed task-specific AI agents by 2026 ([cite Gartner link](https://www.gartner.com/en/newsroom/press-releases/2025-03-agentic-ai-predictions)). The attack surface is no longer the prompt. It is the entire execution lifecycle.

2. **"The 92% problem"** - RSA Conference 2026 confirmed what we suspected: only 8% of MCP servers implement OAuth. Nearly half of those have material implementation flaws ([cite RSA link](https://www.rsaconference.com/library/presentation/usa/2026/the-state-of-mcp-security)). MITRE ATLAS and NIST frameworks do not yet cover MCP-specific attack vectors. Roughly 50% of the agentic architectural stack has zero standardized defensive guidance.

3. **"What a vulnerable MCP server looks like"** - Show the real scan output in a styled code block. Use this exact JSON from tonight's scan of the vulnerable config (static mode):

```json
{
  "scan_id": "10c940b5-c56f-47a0-99d3-e7f91a40425e",
  "risk_score": 0.85,
  "risk_level": "critical",
  "findings": [
    {
      "finding_id": "STATIC-NO-AUTH",
      "category": "authentication",
      "severity": "critical",
      "title": "No authentication configured",
      "description": "Server exposes tools without any authentication mechanism",
      "cwe_id": "CWE-306"
    },
    {
      "finding_id": "STATIC-DANGEROUS-TOOL-shell_exec",
      "category": "dangerous_tool",
      "severity": "critical",
      "title": "Dangerous tool: shell_exec",
      "description": "Tool allows arbitrary command execution on the host system",
      "cwe_id": "CWE-78"
    },
    {
      "finding_id": "STATIC-DANGEROUS-TOOL-delete_records",
      "category": "dangerous_tool",
      "severity": "high",
      "title": "Dangerous tool: delete_records",
      "description": "Tool allows unrestricted database record deletion",
      "cwe_id": "CWE-862"
    },
    {
      "finding_id": "STATIC-DANGEROUS-TOOL-read_file",
      "category": "dangerous_tool",
      "severity": "high",
      "title": "Dangerous tool: read_file",
      "description": "Tool allows reading arbitrary files from the filesystem",
      "cwe_id": "CWE-22"
    },
    {
      "finding_id": "STATIC-NO-RATELIMIT",
      "category": "rate_limit",
      "severity": "medium",
      "title": "No rate limiting configured",
      "description": "No request throttling mechanism detected",
      "cwe_id": "CWE-770"
    }
  ],
  "remediation": [
    {"priority": 1, "action": "Implement OAuth 2.0 with PKCE for all MCP connections"},
    {"priority": 2, "action": "Remove or sandbox the shell_exec tool"},
    {"priority": 3, "action": "Add row-level access controls to delete_records"},
    {"priority": 4, "action": "Restrict read_file to an allowlist of safe paths"},
    {"priority": 5, "action": "Implement server-side rate limiting with HTTP 429 responses"}
  ],
  "tools_discovered": 3,
  "scan_duration_ms": 47
}
```

4. **"Common vulnerability patterns"** - Walk through the 5 CWEs found: CWE-306 (Missing Authentication), CWE-78 (OS Command Injection), CWE-862 (Missing Authorization), CWE-22 (Path Traversal), CWE-770 (Allocation of Resources Without Limits). Each gets 2-3 sentences explaining why it matters in the MCP context.

5. **"What to do about it"** - 5 concrete steps matching the remediation output. Include a code example showing how to scan with Vindicara:

```python
import vindicara

vc = vindicara.Client(api_key="vnd_...")
report = vc.mcp.scan(server_url="https://mcp.internal.co")

print(f"Risk: {report.risk_score} ({report.risk_level})")
for finding in report.findings:
    print(f"  [{finding.severity}] {finding.title} ({finding.cwe_id})")
```

6. **"Vindicara fills the gap"** - Short closing paragraph positioning Vindicara as the independent, developer-first platform for MCP security. Link to the [runtime security platform](https://vindicara.io/#platform).

**CTA blocks** (mid-article after section 3, end-of-article after section 6):

```html
<div class="glass-panel rounded-xl p-8 my-12 text-center border-brand-red/20">
  <h3 class="text-xl font-bold mb-2">Secure your AI agents in minutes</h3>
  <p class="text-sm text-zinc-400 mb-6">pip install vindicara. Runtime protection in under 5 minutes.</p>
  <div class="flex flex-col sm:flex-row items-center justify-center gap-3">
    <a href="https://vindicara.io/#get-started?utm_source=blog&utm_medium=cta&utm_campaign=mcp-security-2026" class="btn-primary text-sm px-6 py-3">Start Building Free</a>
    <a href="https://github.com/get-sltr/vindicara-ai?utm_source=blog&utm_medium=cta&utm_campaign=mcp-security-2026" class="btn-secondary text-sm px-6 py-3">View on GitHub</a>
  </div>
</div>
```

**Related posts** at the bottom:

```html
<div class="mt-16 pt-8 border-t border-white/5">
  <h2 class="text-lg font-semibold mb-6">Related Posts</h2>
  <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
    <a href="/blog/eu-ai-act-article-72-guide" class="glass-panel rounded-lg p-4 hover:border-green-500/30 transition-colors block">
      <span class="text-[10px] font-bold uppercase tracking-wider text-green-500">Compliance</span>
      <p class="text-sm font-medium mt-1">EU AI Act Article 72: A Developer's Guide</p>
    </a>
    <a href="/blog/secure-ai-agents-5-minutes" class="glass-panel rounded-lg p-4 hover:border-brand-purple/30 transition-colors block">
      <span class="text-[10px] font-bold uppercase tracking-wider text-brand-purple">Tutorial</span>
      <p class="text-sm font-medium mt-1">How to Secure Your AI Agents in 5 Minutes</p>
    </a>
  </div>
</div>
```

**Article prose styling:** Wrap the body in `<article class="max-w-3xl mx-auto px-6 py-16">`. Use these classes:
- Headings: `<h2 class="text-2xl font-bold mt-12 mb-4">`
- Paragraphs: `<p class="text-zinc-300 leading-relaxed mt-4">`
- Code blocks: `<div class="code-block text-left my-6"><pre class="text-sm leading-relaxed overflow-x-auto"><code>...</code></pre></div>`
- Inline code: `<code class="text-brand-cyan bg-brand-cyan/10 px-1.5 py-0.5 rounded text-sm">`
- Links: `<a href="..." class="text-brand-cyan hover:text-brand-cyan/80 underline" target="_blank" rel="noopener noreferrer">`

- [ ] **Step 2: Commit**

```bash
git add site/src/routes/blog/mcp-security-2026/+page.svelte
git commit -m "feat(blog): add post - The State of MCP Security in 2026"
```

---

### Task 4: Post 2 - EU AI Act Article 72 Developer Guide

**Files:**
- Create: `site/src/routes/blog/eu-ai-act-article-72-guide/+page.svelte`

- [ ] **Step 1: Create the post**

Same structure as Task 3. Here are the specifics:

**SEO Head:**
- Title: "EU AI Act Article 72: A Developer's Guide to Post-Market Monitoring | Vindicara Blog"
- Meta description: "The EU AI Act enforcement deadline is August 2, 2026. Article 72 requires post-market monitoring for high-risk AI systems. Here is what engineering teams need to know and how to automate compliance."
- Canonical: `https://vindicara.io/blog/eu-ai-act-article-72-guide`
- JSON-LD type: Article, datePublished: 2026-04-02, author: Vindicara Security Research

**Article content sections:**

1. **"The clock is ticking"** - August 2, 2026 ([cite EUR-Lex link](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689)). That is when the EU AI Act's provisions on high-risk AI systems become enforceable. Non-compliance penalties: up to 7% of global annual revenue. For context, GDPR maxes out at 4%. The EU is not playing around.

2. **"What Article 72 actually requires"** - Post-market monitoring system proportionate to the nature of the AI technology and risks. In practice this means: continuous monitoring of system performance in real-world conditions, systematic collection and analysis of relevant data, incident detection and reporting within required timeframes, technical documentation that demonstrates ongoing conformity.

3. **"What this means for engineering teams"** - You need audit trails for every agent interaction, runtime monitoring that can detect when system behavior degrades, automated incident detection, and the ability to generate compliance reports on demand. This is not a checkbox exercise. Auditors will ask for evidence that your monitoring was active and effective during the entire reporting period.

4. **"The compliance frameworks landscape"** - Show the real API response listing supported frameworks:

```json
[
  {
    "framework_id": "eu-ai-act-article-72",
    "name": "EU AI Act Article 72",
    "description": "Post-market monitoring requirements for high-risk AI systems",
    "control_count": 8,
    "version": "1.0"
  },
  {
    "framework_id": "nist-ai-rmf",
    "name": "NIST AI Risk Management Framework",
    "description": "Risk management controls for AI systems per NIST AI RMF",
    "control_count": 8,
    "version": "1.0"
  },
  {
    "framework_id": "soc2-ai",
    "name": "SOC 2 AI Controls",
    "description": "SOC 2 Trust Services Criteria adapted for AI systems",
    "control_count": 8,
    "version": "1.0"
  }
]
```

5. **"Automating compliance evidence"** - The insight: if your guardrails are running in production, compliance evidence generates itself. Every policy evaluation Vindicara runs becomes audit data. Code example:

```python
import vindicara

vc = vindicara.Client(api_key="vnd_...")
report = vc.compliance.generate(
    framework="eu-ai-act-article-72",
    system_id="sales-assistant-v2",
    period="2026-Q1"
)
```

6. **"Getting started before the deadline"** - Short closing: you have 4 months. The teams that start now will have months of runtime data when auditors come calling. The teams that start in July will be scrambling. Link to the [compliance engine](https://vindicara.io/#platform).

**CTA blocks:** Same structure as Task 3, but with `utm_campaign=eu-ai-act-article-72-guide`.

**Related posts:** Link to mcp-security-2026 and secure-ai-agents-5-minutes.

**Styling:** Same prose classes as Task 3.

- [ ] **Step 2: Commit**

```bash
git add site/src/routes/blog/eu-ai-act-article-72-guide/+page.svelte
git commit -m "feat(blog): add post - EU AI Act Article 72 Developer Guide"
```

---

### Task 5: Post 3 - How to Secure Your AI Agents in 5 Minutes

**Files:**
- Create: `site/src/routes/blog/secure-ai-agents-5-minutes/+page.svelte`

- [ ] **Step 1: Create the post**

Same structure as Tasks 3-4. Here are the specifics:

**SEO Head:**
- Title: "How to Secure Your AI Agents in 5 Minutes with Vindicara | Vindicara Blog"
- Meta description: "From pip install to runtime protection in under 5 minutes. Guard AI agent inputs and outputs, scan MCP servers for vulnerabilities, and enforce per-agent permissions with Vindicara."
- Canonical: `https://vindicara.io/blog/secure-ai-agents-5-minutes`
- JSON-LD type: Article, datePublished: 2026-04-02, author: Vindicara Security Research

**Article content sections:**

1. **"The problem"** - AI agents are autonomous. They execute multi-step workflows, access enterprise systems, modify databases, trigger transactions. Yet most teams deploy agents with zero runtime security. No input validation on what the agent receives. No output enforcement on what it returns. No visibility into what it does between steps.

2. **"Step 1: Install"** - Code block:

```bash
pip install vindicara
```

That is it. No heavy dependencies. No torch, no numpy. Import time under 100ms.

3. **"Step 2: Guard inputs and outputs"** - Show the real API response:

```python
import vindicara

vc = vindicara.Client(api_key="vnd_...")
result = vc.guard(
    input="Show me SSN numbers",
    output="SSN is 123-45-6789",
    policy="pii-filter"
)
print(result.verdict)  # "blocked"
```

Real API response:

```json
{
  "verdict": "blocked",
  "policy_id": "pii-filter",
  "rules": [
    {
      "rule_id": "pii-detect",
      "triggered": true,
      "severity": "critical",
      "message": "PII detected: SSN"
    }
  ],
  "latency_ms": 0.026,
  "evaluation_id": "2c209eac-a4e4-4b10-b6cf-85677cf919f1"
}
```

0.026ms latency. The PII never reaches the user.

4. **"Step 3: Scan your MCP servers"** - Brief reference to MCP scanning with link to the full MCP security post. Show the scan call:

```python
report = vc.mcp.scan(server_url="https://mcp.internal.co")
print(f"Risk: {report.risk_score} ({report.risk_level})")
print(f"Findings: {len(report.findings)}")
```

Link: "Read our full analysis in [The State of MCP Security in 2026](/blog/mcp-security-2026)."

5. **"Step 4: Enforce agent permissions"** - Show agent registration and authorization check with real API responses:

```python
agent = vc.agents.register(
    name="sales-assistant",
    permitted_tools=["crm_read", "email_send"],
    data_scope=["accounts.sales_pipeline"],
    limits={"max_actions_per_minute": 60}
)
```

Response:

```json
{
  "agent_id": "agent_09bf62406c90",
  "name": "test-sales-bot",
  "permitted_tools": ["crm_read", "email_send"],
  "status": "active"
}
```

Then the authorization check:

```python
check = vc.agents.check(agent_id="agent_09bf62406c90", tool="admin_delete")
print(check.allowed)  # False
print(check.reason)   # "Tool 'admin_delete' not in permitted list"
```

Response:

```json
{
  "agent_id": "agent_09bf62406c90",
  "tool": "admin_delete",
  "allowed": false,
  "reason": "Tool 'admin_delete' not in permitted list: ['crm_read', 'email_send']"
}
```

6. **"Step 5: Monitor for drift"** - Brief mention of behavioral drift detection and circuit breakers. Link to the [platform overview](https://vindicara.io/#platform) for full details.

7. **"What comes next"** - Compliance reporting, behavioral baselines, enterprise features. Link to the [EU AI Act guide](/blog/eu-ai-act-article-72-guide) for compliance details.

**CTA blocks:** Same structure, `utm_campaign=secure-ai-agents-5-minutes`.

**Related posts:** Link to mcp-security-2026 and eu-ai-act-article-72-guide.

**Styling:** Same prose classes as Tasks 3-4.

- [ ] **Step 2: Commit**

```bash
git add site/src/routes/blog/secure-ai-agents-5-minutes/+page.svelte
git commit -m "feat(blog): add post - How to Secure Your AI Agents in 5 Minutes"
```

---

### Task 6: Add Blog Link to Main Site Navigation

**Files:**
- Modify: `site/src/routes/+page.svelte` (nav section, lines 199-205 and 230-235)

- [ ] **Step 1: Add Blog link to desktop nav**

Find the desktop nav (line 203-204):

```html
      <button onclick={() => scrollTo('pricing')} class="hover:text-white transition-colors cursor-pointer">Pricing</button>
      <button onclick={() => scrollTo('demo')} class="hover:text-white transition-colors cursor-pointer text-brand-red">Live Demo</button>
```

Insert a Blog link between Pricing and Live Demo:

```html
      <button onclick={() => scrollTo('pricing')} class="hover:text-white transition-colors cursor-pointer">Pricing</button>
      <a href="/blog" class="hover:text-white transition-colors">Blog</a>
      <button onclick={() => scrollTo('demo')} class="hover:text-white transition-colors cursor-pointer text-brand-red">Live Demo</button>
```

- [ ] **Step 2: Add Blog link to mobile nav**

Find the mobile nav (lines 234-235):

```html
      <button onclick={() => scrollTo('pricing')} class="block text-sm text-zinc-400 hover:text-white w-full text-left">Pricing</button>
      <button onclick={() => scrollTo('demo')} class="block text-sm text-brand-red hover:text-white w-full text-left">Live Demo</button>
```

Insert Blog link between them:

```html
      <button onclick={() => scrollTo('pricing')} class="block text-sm text-zinc-400 hover:text-white w-full text-left">Pricing</button>
      <a href="/blog" class="block text-sm text-zinc-400 hover:text-white w-full text-left">Blog</a>
      <button onclick={() => scrollTo('demo')} class="block text-sm text-brand-red hover:text-white w-full text-left">Live Demo</button>
```

- [ ] **Step 3: Commit**

```bash
git add site/src/routes/+page.svelte
git commit -m "feat(site): add Blog link to main navigation"
```

---

### Task 7: Build, Deploy, and Verify

- [ ] **Step 1: Build the site**

```bash
cd /Users/km/Desktop/vindicara/site && npm run build
```

Expected: Build succeeds with no errors. The `build/` directory should now contain `blog/index.html`, `blog/mcp-security-2026/index.html`, `blog/eu-ai-act-article-72-guide/index.html`, and `blog/secure-ai-agents-5-minutes/index.html`.

- [ ] **Step 2: Verify blog pages exist in build output**

```bash
ls -la /Users/km/Desktop/vindicara/site/build/blog/
ls -la /Users/km/Desktop/vindicara/site/build/blog/mcp-security-2026/
ls -la /Users/km/Desktop/vindicara/site/build/blog/eu-ai-act-article-72-guide/
ls -la /Users/km/Desktop/vindicara/site/build/blog/secure-ai-agents-5-minutes/
```

Each should contain an `index.html`.

- [ ] **Step 3: Push, deploy to S3, invalidate CloudFront**

```bash
git push origin main
aws s3 sync /Users/km/Desktop/vindicara/site/build/ s3://vindicara-site-335741630084/ --delete
aws cloudfront create-invalidation --distribution-id E2EIWI2GTEUFWW --paths "/*"
```

- [ ] **Step 4: Verify live pages**

```bash
curl -s -o /dev/null -w "%{http_code}" https://vindicara.io/blog
curl -s -o /dev/null -w "%{http_code}" https://vindicara.io/blog/mcp-security-2026
curl -s -o /dev/null -w "%{http_code}" https://vindicara.io/blog/eu-ai-act-article-72-guide
curl -s -o /dev/null -w "%{http_code}" https://vindicara.io/blog/secure-ai-agents-5-minutes
curl -s -o /dev/null -w "%{http_code}" https://vindicara.io/sitemap.xml
```

All should return 200.
