# Landing Page Trust Signals Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add trust signals (citations, real scan output, architecture diagram, tightened headline) to the Vindicara landing page.

**Architecture:** All changes are surgical edits to a single file: `site/src/routes/+page.svelte`. No new files, no component extraction. Five independent edit regions in the file.

**Tech Stack:** SvelteKit 2.50, TailwindCSS 4.2, inline SVG for the architecture diagram.

**Spec:** `docs/superpowers/specs/2026-04-02-landing-page-trust-signals-design.md`

---

### Task 1: Update Hero Headline

**Files:**
- Modify: `site/src/routes/+page.svelte:263-266`

- [ ] **Step 1: Replace the headline text**

Find this block at lines 263-266:

```html
      <h1 class="text-5xl sm:text-6xl lg:text-7xl font-black tracking-tight leading-[1.05] max-w-5xl mx-auto">
        <span class="text-gradient-brand">Runtime security</span><br />
        <span class="text-white">for autonomous AI</span>
      </h1>
```

Replace with:

```html
      <h1 class="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight leading-[1.08] max-w-5xl mx-auto">
        <span class="text-white">Vindicara is the</span><br />
        <span class="text-gradient-brand">runtime security layer</span><br />
        <span class="text-white">for AI agents and MCP-connected systems.</span>
      </h1>
```

Note: Font size reduced one step (7xl to 6xl, etc.) because the new headline is longer and needs to fit without wrapping awkwardly on smaller screens.

- [ ] **Step 2: Visual check**

Run: `cd /Users/km/Desktop/vindicara/site && npm run dev`

Open `http://localhost:5173` and verify:
- "Vindicara is the" renders in white
- "runtime security layer" renders in the gradient brand colors
- "for AI agents and MCP-connected systems." renders in white
- No awkward line breaks at 1440px, 768px, and 375px widths

- [ ] **Step 3: Commit**

```bash
git add site/src/routes/+page.svelte
git commit -m "feat(site): update hero headline to include product name and MCP positioning"
```

---

### Task 2: Add Urgency Bar Citations

**Files:**
- Modify: `site/src/routes/+page.svelte:314-332`

- [ ] **Step 1: Add source links below each stat**

Find this block at lines 314-332:

```html
<!-- URGENCY BAR -->
<section class="relative py-12 border-y border-white/5">
  <div class="max-w-screen-xl mx-auto px-6">
    <div class="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
      <div>
        <p class="text-2xl sm:text-3xl font-black text-brand-red">Aug 2, 2026</p>
        <p class="text-sm text-zinc-500 mt-1">EU AI Act enforcement deadline</p>
      </div>
      <div>
        <p class="text-2xl sm:text-3xl font-black text-white">92%</p>
        <p class="text-sm text-zinc-500 mt-1">of MCP servers lack proper OAuth</p>
      </div>
      <div>
        <p class="text-2xl sm:text-3xl font-black text-gradient-brand">40%</p>
        <p class="text-sm text-zinc-500 mt-1">of enterprise apps will embed AI agents by EOY</p>
      </div>
    </div>
  </div>
</section>
```

Replace with:

```html
<!-- URGENCY BAR -->
<section class="relative py-12 border-y border-white/5">
  <div class="max-w-screen-xl mx-auto px-6">
    <div class="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
      <div>
        <p class="text-2xl sm:text-3xl font-black text-brand-red">Aug 2, 2026</p>
        <p class="text-sm text-zinc-500 mt-1">EU AI Act enforcement deadline</p>
        <a href="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689" target="_blank" rel="noopener noreferrer" class="text-xs text-zinc-600 hover:text-zinc-400 underline mt-1 inline-block">EU AI Act, Art. 113</a>
      </div>
      <div>
        <p class="text-2xl sm:text-3xl font-black text-white">92%</p>
        <p class="text-sm text-zinc-500 mt-1">of MCP servers lack proper OAuth</p>
        <a href="https://www.rsaconference.com/library/presentation/usa/2026/the-state-of-mcp-security" target="_blank" rel="noopener noreferrer" class="text-xs text-zinc-600 hover:text-zinc-400 underline mt-1 inline-block">RSA Conference 2026</a>
      </div>
      <div>
        <p class="text-2xl sm:text-3xl font-black text-gradient-brand">40%</p>
        <p class="text-sm text-zinc-500 mt-1">of enterprise apps will embed AI agents by EOY</p>
        <a href="https://www.gartner.com/en/newsroom/press-releases/2025-03-agentic-ai-predictions" target="_blank" rel="noopener noreferrer" class="text-xs text-zinc-600 hover:text-zinc-400 underline mt-1 inline-block">Gartner, 2025</a>
      </div>
    </div>
  </div>
</section>
```

- [ ] **Step 2: Visual check**

Verify in the running dev server:
- Each stat has a small underlined source link below it
- Links are `text-zinc-600` (very subtle), brighten on hover
- Links open in a new tab
- Layout doesn't shift or look cluttered at mobile widths

- [ ] **Step 3: Commit**

```bash
git add site/src/routes/+page.svelte
git commit -m "feat(site): add citation links to urgency bar stats"
```

---

### Task 3: Replace MCP Code Snippet with Real Scan Output

**Files:**
- Modify: `site/src/routes/+page.svelte:497-524`

- [ ] **Step 1: Replace the right column content**

Find this block at lines 497-524:

```html
      <div>
        <div class="code-block glow-cyan text-left">
          <div class="flex items-center gap-2 mb-3 text-zinc-500 text-xs">
            <span class="w-3 h-3 rounded-full bg-red-500/80"></span>
            <span class="w-3 h-3 rounded-full bg-yellow-500/80"></span>
            <span class="w-3 h-3 rounded-full bg-green-500/80"></span>
            <span class="ml-2">mcp_scan.py</span>
          </div>
          <pre class="text-sm leading-relaxed"><code><span class="text-zinc-500"># Scan any MCP server in seconds</span>
<span class="text-white">report</span> <span class="text-brand-pink">=</span> <span class="text-white">vc</span><span class="text-zinc-400">.</span><span class="text-white">mcp</span><span class="text-zinc-400">.</span><span class="text-white">scan</span><span class="text-zinc-400">(</span>
    <span class="text-white">server_url</span><span class="text-brand-pink">=</span><span class="text-green-400">"https://mcp.internal.co"</span>
<span class="text-zinc-400">)</span>

<span class="text-brand-purple">print</span><span class="text-zinc-400">(</span><span class="text-white">report</span><span class="text-zinc-400">.</span><span class="text-white">risk_score</span><span class="text-zinc-400">)</span>    <span class="text-zinc-500"># 0.73 (HIGH)</span>
<span class="text-brand-purple">print</span><span class="text-zinc-400">(</span><span class="text-white">report</span><span class="text-zinc-400">.</span><span class="text-white">findings</span><span class="text-zinc-400">)</span>
<span class="text-zinc-500"># [</span>
<span class="text-zinc-500">#   "No OAuth configured",</span>
<span class="text-zinc-500">#   "3 tools with write access lack scoping",</span>
<span class="text-zinc-500">#   "delete_all tool has no rate limit"</span>
<span class="text-zinc-500"># ]</span>

<span class="text-zinc-500"># Runtime: inspect live MCP traffic</span>
<span class="text-white">vc</span><span class="text-zinc-400">.</span><span class="text-white">mcp</span><span class="text-zinc-400">.</span><span class="text-white">inspect</span><span class="text-zinc-400">(</span>
    <span class="text-white">server</span><span class="text-brand-pink">=</span><span class="text-green-400">"crm-connector"</span><span class="text-zinc-400">,</span>
    <span class="text-white">on_violation</span><span class="text-brand-pink">=</span><span class="text-green-400">"block_and_alert"</span>
<span class="text-zinc-400">)</span></code></pre>
        </div>
      </div>
```

Replace with:

```html
      <div>
        <!-- Live scan output badge -->
        <div class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full glass-panel text-xs text-zinc-400 mb-4">
          <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
          Live Scan Output
        </div>

        <div class="glass-panel rounded-xl p-5 glow-cyan text-left overflow-y-auto max-h-[520px]">
          <!-- Header -->
          <div class="flex items-center justify-between mb-4">
            <span class="text-xs font-medium text-zinc-500 uppercase tracking-wider font-mono">Scan Result</span>
            <div class="flex items-center gap-2">
              <span class="text-lg font-bold font-mono text-brand-red">0.85</span>
              <span class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-brand-red/10 text-brand-red border border-brand-red/20">critical</span>
            </div>
          </div>

          <!-- Findings -->
          <div class="mb-4">
            <p class="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-2">Findings (5)</p>
            <div class="space-y-2">
              <div class="glass-panel rounded-lg px-3 py-2">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-xs font-mono text-white">No authentication configured</span>
                  <span class="text-[10px] font-mono uppercase text-brand-red">critical</span>
                </div>
                <p class="text-xs text-zinc-500">Server exposes tools without any auth mechanism</p>
                <p class="text-[10px] text-zinc-600 mt-1 font-mono">CWE-306</p>
              </div>
              <div class="glass-panel rounded-lg px-3 py-2">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-xs font-mono text-white">Dangerous tool: shell_exec</span>
                  <span class="text-[10px] font-mono uppercase text-brand-red">critical</span>
                </div>
                <p class="text-xs text-zinc-500">Tool allows arbitrary command execution on host</p>
                <p class="text-[10px] text-zinc-600 mt-1 font-mono">CWE-78</p>
              </div>
              <div class="glass-panel rounded-lg px-3 py-2">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-xs font-mono text-white">Dangerous tool: delete_records</span>
                  <span class="text-[10px] font-mono uppercase text-orange-400">high</span>
                </div>
                <p class="text-xs text-zinc-500">Tool allows unrestricted database record deletion</p>
                <p class="text-[10px] text-zinc-600 mt-1 font-mono">CWE-862</p>
              </div>
              <div class="glass-panel rounded-lg px-3 py-2">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-xs font-mono text-white">Dangerous tool: read_file</span>
                  <span class="text-[10px] font-mono uppercase text-orange-400">high</span>
                </div>
                <p class="text-xs text-zinc-500">Tool allows reading arbitrary files from disk</p>
                <p class="text-[10px] text-zinc-600 mt-1 font-mono">CWE-22</p>
              </div>
              <div class="glass-panel rounded-lg px-3 py-2">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-xs font-mono text-white">No rate limiting detected</span>
                  <span class="text-[10px] font-mono uppercase text-yellow-400">medium</span>
                </div>
                <p class="text-xs text-zinc-500">No request throttling configured</p>
                <p class="text-[10px] text-zinc-600 mt-1 font-mono">CWE-770</p>
              </div>
            </div>
          </div>

          <!-- Remediation -->
          <div class="mb-4 pt-2 border-t border-white/5">
            <p class="text-xs font-medium text-zinc-500 uppercase tracking-wider mb-2">Remediation</p>
            <div class="space-y-1.5">
              <div class="flex items-start gap-2">
                <span class="text-[10px] font-mono text-brand-cyan shrink-0 mt-0.5">#1</span>
                <p class="text-xs text-zinc-400">Implement OAuth 2.0 with PKCE for all MCP connections</p>
              </div>
              <div class="flex items-start gap-2">
                <span class="text-[10px] font-mono text-brand-cyan shrink-0 mt-0.5">#2</span>
                <p class="text-xs text-zinc-400">Remove or sandbox shell_exec tool</p>
              </div>
              <div class="flex items-start gap-2">
                <span class="text-[10px] font-mono text-brand-cyan shrink-0 mt-0.5">#3</span>
                <p class="text-xs text-zinc-400">Add row-level access controls to delete_records</p>
              </div>
              <div class="flex items-start gap-2">
                <span class="text-[10px] font-mono text-brand-cyan shrink-0 mt-0.5">#4</span>
                <p class="text-xs text-zinc-400">Restrict read_file to an allowlist of paths</p>
              </div>
              <div class="flex items-start gap-2">
                <span class="text-[10px] font-mono text-brand-cyan shrink-0 mt-0.5">#5</span>
                <p class="text-xs text-zinc-400">Add server-side rate limiting (HTTP 429)</p>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="pt-2 border-t border-white/5 flex items-center gap-4">
            <span class="text-[10px] font-mono text-zinc-600">scan_id: 10c940b5</span>
            <span class="text-[10px] font-mono text-zinc-600">duration: 47ms</span>
            <span class="text-[10px] font-mono text-zinc-600">tools: 3</span>
          </div>
        </div>
      </div>
```

- [ ] **Step 2: Visual check**

Verify in the running dev server:
- "Live Scan Output" badge with green pulsing dot appears above the scan card
- Risk score 0.85 shows in red with CRITICAL badge
- Five findings display with correct severity colors (2 critical/red, 2 high/orange, 1 medium/yellow)
- CWE IDs render as small monospace text
- Remediation items numbered in cyan
- Footer shows scan metadata
- Content scrolls if it overflows the max height
- On mobile, the scan output stacks below the left column text

- [ ] **Step 3: Commit**

```bash
git add site/src/routes/+page.svelte
git commit -m "feat(site): replace MCP code snippet with real scan output showcase"
```

---

### Task 4: Add Architecture Flow Diagram

**Files:**
- Modify: `site/src/routes/+page.svelte:594-595` (insert between section header closing `</div>` and the grid)

- [ ] **Step 1: Insert the architecture diagram**

Find this exact location at lines 593-596:

```html
      </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
```

Replace with:

```html
      </p>
    </div>

    <!-- Architecture Flow Diagram -->
    <div class="mb-16">
      <!-- Desktop: horizontal flow -->
      <div class="hidden md:flex items-center justify-center gap-0">
        <!-- Your App node -->
        <div class="glass-panel rounded-xl p-5 text-center min-w-[140px]">
          <div class="w-10 h-10 rounded-lg bg-brand-purple/10 flex items-center justify-center mx-auto mb-2">
            <svg class="w-5 h-5 text-brand-purple" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
            </svg>
          </div>
          <p class="text-sm font-semibold text-white">Your App</p>
          <p class="text-[10px] text-zinc-500 mt-1">Any AI application</p>
        </div>

        <!-- Arrow 1 -->
        <div class="flex items-center px-2">
          <div class="w-12 h-px border-t-2 border-dashed border-zinc-600" style="animation: dash 1.5s linear infinite;"></div>
          <svg class="w-4 h-4 text-zinc-500 -ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" /></svg>
        </div>

        <!-- Vindicara SDK node (center, emphasized) -->
        <div class="glass-panel rounded-xl p-5 text-center min-w-[180px] border-brand-red/20 glow-red relative">
          <div class="w-10 h-10 rounded-lg bg-brand-red/10 flex items-center justify-center mx-auto mb-2">
            <svg class="w-5 h-5 text-brand-red" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
            </svg>
          </div>
          <p class="text-sm font-bold text-white">Vindicara SDK</p>
          <p class="text-[10px] text-zinc-500 mt-1">Runtime security layer</p>
          <div class="flex flex-wrap justify-center gap-1.5 mt-3">
            <span class="text-[10px] bg-white/5 border border-white/10 rounded-full px-2 py-0.5 text-zinc-400">Input Guard</span>
            <span class="text-[10px] bg-white/5 border border-white/10 rounded-full px-2 py-0.5 text-zinc-400">Output Guard</span>
            <span class="text-[10px] bg-white/5 border border-white/10 rounded-full px-2 py-0.5 text-zinc-400">MCP Inspector</span>
            <span class="text-[10px] bg-white/5 border border-white/10 rounded-full px-2 py-0.5 text-zinc-400">Agent IAM</span>
            <span class="text-[10px] bg-white/5 border border-white/10 rounded-full px-2 py-0.5 text-zinc-400">Drift Monitor</span>
          </div>
        </div>

        <!-- Arrow 2 -->
        <div class="flex items-center px-2">
          <div class="w-12 h-px border-t-2 border-dashed border-zinc-600" style="animation: dash 1.5s linear infinite;"></div>
          <svg class="w-4 h-4 text-zinc-500 -ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" /></svg>
        </div>

        <!-- AI Model / Tools / MCP node -->
        <div class="glass-panel rounded-xl p-5 text-center min-w-[160px]">
          <div class="w-10 h-10 rounded-lg bg-brand-cyan/10 flex items-center justify-center mx-auto mb-2">
            <svg class="w-5 h-5 text-brand-cyan" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M8.288 15.038a5.25 5.25 0 017.424 0M5.106 11.856c3.807-3.808 9.98-3.808 13.788 0M1.924 8.674c5.565-5.565 14.587-5.565 20.152 0M12.53 18.22l-.53.53-.53-.53a.75.75 0 011.06 0z" />
            </svg>
          </div>
          <p class="text-sm font-semibold text-white">AI Systems</p>
          <div class="mt-2 space-y-1">
            <p class="text-[10px] text-zinc-500">LLM / Model</p>
            <p class="text-[10px] text-zinc-500">Tools / APIs</p>
            <p class="text-[10px] text-zinc-500">MCP Servers</p>
          </div>
        </div>
      </div>

      <!-- Mobile: vertical flow -->
      <div class="flex md:hidden flex-col items-center gap-0">
        <!-- Your App node -->
        <div class="glass-panel rounded-xl p-4 text-center w-full max-w-[260px]">
          <div class="w-8 h-8 rounded-lg bg-brand-purple/10 flex items-center justify-center mx-auto mb-2">
            <svg class="w-4 h-4 text-brand-purple" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
            </svg>
          </div>
          <p class="text-sm font-semibold text-white">Your App</p>
        </div>

        <!-- Down arrow -->
        <div class="flex flex-col items-center py-1">
          <div class="h-8 border-l-2 border-dashed border-zinc-600"></div>
          <svg class="w-4 h-4 text-zinc-500 -mt-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" /></svg>
        </div>

        <!-- Vindicara SDK node -->
        <div class="glass-panel rounded-xl p-4 text-center w-full max-w-[260px] border-brand-red/20 glow-red">
          <div class="w-8 h-8 rounded-lg bg-brand-red/10 flex items-center justify-center mx-auto mb-2">
            <svg class="w-4 h-4 text-brand-red" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
            </svg>
          </div>
          <p class="text-sm font-bold text-white">Vindicara SDK</p>
          <div class="flex flex-wrap justify-center gap-1 mt-2">
            <span class="text-[10px] bg-white/5 border border-white/10 rounded-full px-2 py-0.5 text-zinc-400">Input Guard</span>
            <span class="text-[10px] bg-white/5 border border-white/10 rounded-full px-2 py-0.5 text-zinc-400">Output Guard</span>
            <span class="text-[10px] bg-white/5 border border-white/10 rounded-full px-2 py-0.5 text-zinc-400">MCP Inspector</span>
            <span class="text-[10px] bg-white/5 border border-white/10 rounded-full px-2 py-0.5 text-zinc-400">Agent IAM</span>
            <span class="text-[10px] bg-white/5 border border-white/10 rounded-full px-2 py-0.5 text-zinc-400">Drift Monitor</span>
          </div>
        </div>

        <!-- Down arrow -->
        <div class="flex flex-col items-center py-1">
          <div class="h-8 border-l-2 border-dashed border-zinc-600"></div>
          <svg class="w-4 h-4 text-zinc-500 -mt-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" /></svg>
        </div>

        <!-- AI Systems node -->
        <div class="glass-panel rounded-xl p-4 text-center w-full max-w-[260px]">
          <div class="w-8 h-8 rounded-lg bg-brand-cyan/10 flex items-center justify-center mx-auto mb-2">
            <svg class="w-4 h-4 text-brand-cyan" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M8.288 15.038a5.25 5.25 0 017.424 0M5.106 11.856c3.807-3.808 9.98-3.808 13.788 0M1.924 8.674c5.565-5.565 14.587-5.565 20.152 0M12.53 18.22l-.53.53-.53-.53a.75.75 0 011.06 0z" />
            </svg>
          </div>
          <p class="text-sm font-semibold text-white">AI Systems</p>
          <div class="mt-1 space-y-0.5">
            <p class="text-[10px] text-zinc-500">LLM / Model</p>
            <p class="text-[10px] text-zinc-500">Tools / APIs</p>
            <p class="text-[10px] text-zinc-500">MCP Servers</p>
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
```

- [ ] **Step 2: Add dash animation CSS**

Find the closing `</style>` tag in the file (or if there is no `<style>` block, add one at the end of the file before the closing tag). Since this is a SvelteKit page using Tailwind, add a `<style>` block at the very end of the file:

```html
<style>
  @keyframes dash {
    to {
      stroke-dashoffset: -12;
    }
  }
</style>
```

Note: The dashed border animation uses inline `style="animation: dash 1.5s linear infinite;"` on the dashed line elements. If the CSS `@keyframes` approach does not animate `border-style: dashed` divs (since they are not SVG strokes), the dashed lines will still render statically as dashed borders, which is acceptable. The visual effect of dashed lines between nodes communicates the flow regardless of animation.

- [ ] **Step 3: Visual check**

Verify in the running dev server:
- Desktop (1440px): Three nodes in a horizontal row with dashed lines and chevron arrows between them
- Vindicara SDK node is visually emphasized (red glow, slightly larger)
- Five capability pills display below the SDK node
- Mobile (375px): Nodes stack vertically with downward arrows
- Diagram appears between the "Five minutes to runtime protection" header and the 4-step grid

- [ ] **Step 4: Commit**

```bash
git add site/src/routes/+page.svelte
git commit -m "feat(site): add architecture flow diagram to How It Works section"
```

---

### Task 5: Add Footer Sources Section

**Files:**
- Modify: `site/src/routes/+page.svelte:1064` (footer grid)

- [ ] **Step 1: Expand footer grid and add Sources column**

Find this line at 1064:

```html
    <div class="grid grid-cols-2 md:grid-cols-4 gap-8">
```

Replace with:

```html
    <div class="grid grid-cols-2 md:grid-cols-5 gap-8">
```

Then find the Legal column closing `</div>` at line 1106, and after it, add the Sources column:

Find:

```html
          <li><a href="mailto:legal@vindicara.io" class="hover:text-white transition-colors">DPA</a></li>
        </ul>
      </div>
    </div>
```

Replace with:

```html
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
```

- [ ] **Step 2: Visual check**

Verify in the running dev server:
- Footer now has 5 columns on desktop (Vindicara, Product, Company, Legal, Sources)
- On mobile, columns wrap to 2-column grid naturally
- Source links open in new tabs
- Style matches existing footer links

- [ ] **Step 3: Commit**

```bash
git add site/src/routes/+page.svelte
git commit -m "feat(site): add Sources section to footer with citation references"
```

---

### Task 6: Final Verification

- [ ] **Step 1: Full page review**

Run: `cd /Users/km/Desktop/vindicara/site && npm run dev`

Check at three breakpoints (1440px, 768px, 375px):
1. Hero headline renders correctly with gradient on "runtime security layer"
2. Urgency bar has citation links that open in new tabs
3. MCP Deep Dive shows real scan output with "Live Scan Output" badge
4. Architecture diagram displays horizontally on desktop, vertically on mobile
5. Footer has Sources column with three reference links
6. Interactive demo (Guard + MCP Scanner tabs) still functions correctly
7. No layout shifts, overflow issues, or broken styles

- [ ] **Step 2: Link verification**

Click each external link to verify it opens the correct page:
- EUR-Lex EU AI Act link
- RSA Conference link
- Gartner press release link

- [ ] **Step 3: Final commit (if any cleanup needed)**

If any adjustments were needed during verification:

```bash
git add site/src/routes/+page.svelte
git commit -m "fix(site): polish landing page trust signal adjustments"
```
