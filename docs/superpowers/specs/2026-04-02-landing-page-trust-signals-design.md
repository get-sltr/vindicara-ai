# Landing Page Trust Signals and Credibility Improvements

**Date:** 2026-04-02
**Status:** Approved
**Approach:** Surgical edits to existing `site/src/routes/+page.svelte`

## Objective

Make the Vindicara landing page more attractive and trustworthy by adding citation links for every stat, showcasing real MCP scanner output, adding an architecture diagram, and tightening the headline. All changes are additive trust signals applied surgically to the existing page.

## Changes

### 1. Headline Update

**File:** `site/src/routes/+page.svelte`, hero section (~line 263)

**Current:**
```
Runtime security
for autonomous AI
```

**New:**
```
Vindicara is the
runtime security layer
for AI agents and MCP-connected systems.
```

- "Vindicara is the" in white
- "runtime security layer" in `text-gradient-brand`
- "for AI agents and MCP-connected systems." in white
- Subheadline unchanged

### 2. Urgency Bar Citations

**File:** `site/src/routes/+page.svelte`, urgency bar section (~line 315)

Add inline source links below each stat's description text. Style: `text-zinc-600 hover:text-zinc-400 text-xs underline`.

| Stat | Source Text | Link Target |
|------|-----------|-------------|
| Aug 2, 2026 | "EU AI Act, Art. 113" | `https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689` |
| 92% | "RSA Conference 2026" | `https://www.rsaconference.com/library/presentation/usa/2026/the-state-of-mcp-security` |
| 40% | "Gartner, 2025" | `https://www.gartner.com/en/newsroom/press-releases/2025-03-agentic-ai-predictions` |

Links open in new tab (`target="_blank" rel="noopener noreferrer"`).

### 3. Static MCP Scanner Showcase

**File:** `site/src/routes/+page.svelte`, MCP Security Deep Dive section (~line 497)

**What changes:** Replace the right-column Python code snippet (`mcp_scan.py` code block) with a styled rendering of a real scan result.

**Label:** Small badge above the output: "LIVE SCAN OUTPUT" with a green pulsing dot, matching the "Developer Preview" badge pattern.

**Content structure** (rendered as structured HTML, not raw JSON):

```
SCAN RESULT                          risk: 0.85 CRITICAL

Findings (5)
  CRITICAL  No authentication configured
            Server exposes tools without any auth mechanism
            CWE-306

  CRITICAL  Dangerous tool: shell_exec
            Tool allows arbitrary command execution on host
            CWE-78

  HIGH      Dangerous tool: delete_records
            Tool allows unrestricted database record deletion
            CWE-862

  HIGH      Dangerous tool: read_file
            Tool allows reading arbitrary files from disk
            CWE-22

  MEDIUM    No rate limiting detected
            No request throttling configured
            CWE-770

Remediation
  #1  Implement OAuth 2.0 with PKCE for all MCP connections
  #2  Remove or sandbox shell_exec tool
  #3  Add row-level access controls to delete_records
  #4  Restrict read_file to an allowlist of paths
  #5  Add server-side rate limiting (HTTP 429)

scan_id: 10c940b5    duration: 47ms    tools: 3
```

**Styling:**
- Same `glass-panel` + `glow-cyan` treatment as the current code block
- Risk level: color-coded badge (critical=brand-red)
- Finding severities: critical=brand-red, high=orange-400, medium=yellow-400
- CWE IDs: small monospace `text-zinc-600` tags
- Remediation priorities: `text-brand-cyan` numbered
- Footer line (scan_id, duration, tools): `text-zinc-600 text-[10px] font-mono`

### 4. Architecture Diagram

**File:** `site/src/routes/+page.svelte`, How It Works section (~line 584)

**Placement:** Between the section header ("Five minutes to runtime protection") and the existing 4-step grid.

**Layout:** Horizontal flow diagram (stacks vertically on mobile) with three nodes connected by animated dashed lines with arrow chevrons.

**Nodes:**

1. **Your App** (left)
   - Purple accent (`brand-purple`)
   - Code brackets icon
   - `glass-panel` box

2. **Vindicara SDK** (center, largest)
   - Red accent (`brand-red`)
   - Shield icon
   - `glass-panel` box, visually emphasized (slightly larger, glow-red)
   - Five small pills below: "Input Guard", "Output Guard", "MCP Inspector", "Agent IAM", "Drift Monitor"
   - Pills styled as `text-xs bg-white/5 border border-white/10 rounded-full px-2 py-0.5`

3. **AI Model / Tools / MCP** (right)
   - Cyan accent (`brand-cyan`)
   - Three sub-labels stacked: "LLM", "Tools", "MCP Servers"
   - `glass-panel` box

**Connecting lines:**
- Dashed borders with CSS animation (moving dash pattern via `stroke-dashoffset` animation)
- Small SVG chevron arrows at endpoints

**Responsive:**
- Desktop: horizontal layout, ~200px tall
- Mobile (`md:` breakpoint): vertical stack with downward arrows

### 5. Footer Sources Section

**File:** `site/src/routes/+page.svelte`, footer section (~line 1062)

Add a new column to the footer grid (expand from 4-col to include Sources, or replace one of the existing columns that has fewer items).

**Column title:** "Sources"

**Entries:**
1. "EU AI Act, Regulation (EU) 2024/1689" linking to EUR-Lex
2. "RSA Conference 2026, State of MCP Security" linking to RSA library
3. "Gartner Predicts 2025: Agentic AI" linking to Gartner press release

Style matches existing footer link style: `text-sm text-zinc-500 hover:text-white transition-colors`.

## Non-Goals

- No component extraction or file splitting
- No new Svelte components or files
- No changes to the interactive demo section
- No changes to pricing, CTA, or other sections not listed
- No changes to `app.css` (all styling uses existing utility classes)

## Testing

- Visual inspection at desktop (1440px), tablet (768px), and mobile (375px) breakpoints
- Verify all external links open in new tabs and resolve correctly
- Verify architecture diagram stacks vertically on mobile
- Verify existing interactive demo still functions after changes
