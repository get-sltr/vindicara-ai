<svelte:head>
  <title>Run your first `air trace` in 5 minutes | Vindicara Blog</title>
  <meta name="description" content="From pip install projectair to a signed forensic timeline of your LangChain agent in under five minutes. The air CLI and airsdk are MIT-licensed and open source today." />
  <link rel="canonical" href="https://vindicara.io/blog/secure-ai-agents-5-minutes" />
  <meta property="og:type" content="article" />
  <meta property="og:url" content="https://vindicara.io/blog/secure-ai-agents-5-minutes" />
  <meta property="og:title" content="Run your first `air trace` in 5 minutes" />
  <meta property="og:description" content="From pip install projectair to a signed forensic timeline of your LangChain agent in under five minutes. The air CLI and airsdk are MIT-licensed and open source today." />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="Run your first `air trace` in 5 minutes" />
  <meta name="twitter:description" content="From pip install projectair to a signed forensic timeline of your LangChain agent in under five minutes." />
  {@html `<script type="application/ld+json">${JSON.stringify({
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "Run your first `air trace` in 5 minutes",
    "description": "From pip install projectair to a signed forensic timeline of your LangChain agent in under five minutes. The air CLI and airsdk are MIT-licensed and open source today.",
    "datePublished": "2026-04-02",
    "dateModified": "2026-04-18",
    "author": {
      "@type": "Organization",
      "name": "Vindicara Security Research",
      "url": "https://vindicara.io"
    },
    "publisher": {
      "@type": "Organization",
      "name": "Vindicara",
      "url": "https://vindicara.io"
    },
    "mainEntityOfPage": "https://vindicara.io/blog/secure-ai-agents-5-minutes"
  })}</script>`}
</svelte:head>

<article class="max-w-3xl mx-auto px-6 py-16">
  <!-- Article Header -->
  <header class="mb-12">
    <div class="flex items-center gap-3 mb-6">
      <span class="text-[10px] font-bold uppercase tracking-wider bg-brand-purple/10 text-brand-purple border border-brand-purple/20 rounded-full px-2.5 py-0.5">Quickstart</span>
      <span class="text-[10px] text-zinc-600">5 min read</span>
    </div>
    <h1 class="text-4xl sm:text-5xl font-bold tracking-tight leading-tight">Run your first <code class="font-mono text-brand-purple">air trace</code> in 5 minutes</h1>
    <p class="text-lg text-zinc-400 mt-4">From <code class="text-brand-purple bg-brand-purple/10 px-1.5 py-0.5 rounded text-sm">pip install projectair</code> to a signed forensic timeline of your LangChain agent. The <code class="text-brand-purple bg-brand-purple/10 px-1.5 py-0.5 rounded text-sm">air</code> CLI and <code class="text-brand-purple bg-brand-purple/10 px-1.5 py-0.5 rounded text-sm">airsdk</code> are MIT-licensed and open source today.</p>
    <div class="flex items-center gap-3 mt-6 text-sm text-zinc-500">
      <span>Vindicara Security Research</span>
      <span class="text-zinc-700">|</span>
      <span>April 18, 2026</span>
    </div>
  </header>

  <!-- Section 1: Why run air before you have an incident -->
  <h2 class="text-2xl font-bold mt-12 mb-4">Why run <code class="font-mono text-brand-purple">air</code> before you have an incident</h2>

  <p class="text-zinc-300 leading-relaxed mt-4">
    Most teams reach for forensics after something breaks. By then, the trace is incomplete, the reasoning is gone, and the on-call engineer is stitching together logs from five systems at 2am. The teams that recover fast are the ones that were already writing a signed record of every agent decision before the incident.
  </p>

  <p class="text-zinc-300 leading-relaxed mt-4">
    Project AIR™ is the forensic reconstruction layer for AI agents. The <code class="text-brand-purple bg-brand-purple/10 px-1.5 py-0.5 rounded text-sm">air</code> CLI ingests an agent trace, runs detectors across two public OWASP taxonomies (all 10 OWASP Top 10 for Agentic Applications categories from ASI01 through ASI10; plus 3 OWASP Top 10 for LLM Applications categories: LLM01, LLM04, LLM06), plus 1 AIR-native forensic-chain-integrity check, and outputs a timeline you can hand to security, legal, or insurance. The <code class="text-brand-purple bg-brand-purple/10 px-1.5 py-0.5 rounded text-sm">airsdk</code> Python package is what writes the trace in the first place, as a chain of AgDR (AI Decision Record) entries, each with a BLAKE3 content hash and an Ed25519 signature.
  </p>

  <p class="text-zinc-300 leading-relaxed mt-4">
    This guide walks through five steps that take roughly one minute each. The prerequisite is one LangChain agent you can run once. That is it.
  </p>

  <!-- Section 2: Step 1 - Install -->
  <h2 class="text-2xl font-bold mt-12 mb-4">Step 1: Install</h2>

  <div class="code-block text-left my-6"><pre class="text-sm leading-relaxed overflow-x-auto"><code>pip install projectair</code></pre></div>

  <p class="text-zinc-300 leading-relaxed mt-4">
    One package installs both the <code class="text-brand-purple bg-brand-purple/10 px-1.5 py-0.5 rounded text-sm">air</code> CLI and the <code class="text-brand-purple bg-brand-purple/10 px-1.5 py-0.5 rounded text-sm">airsdk</code> Python library. No torch, no heavy model downloads, no GPU. The CLI works on any trace file the SDK emits, and the SDK is a standard LangChain callback handler. If your agent runs today, this installs clean alongside it.
  </p>

  <!-- Section 3: Step 2 - Wire the callback -->
  <h2 class="text-2xl font-bold mt-12 mb-4">Step 2: Wire the AgDR callback into your agent</h2>

  <p class="text-zinc-300 leading-relaxed mt-4">
    Add the callback handler to your LangChain <code class="text-brand-purple bg-brand-purple/10 px-1.5 py-0.5 rounded text-sm">AgentExecutor</code>. Every tool call, every model response, every intermediate reasoning step becomes an AgDR entry, signed and chained to the previous one:
  </p>

  <div class="code-block text-left my-6"><pre class="text-sm leading-relaxed overflow-x-auto"><code>{`from airsdk import AIRCallbackHandler
from langchain.agents import AgentExecutor

handler = AIRCallbackHandler(key="...")
agent = AgentExecutor(callbacks=[handler], ...)`}</code></pre></div>

  <p class="text-zinc-300 leading-relaxed mt-4">
    The handler is drop-in. You do not need to restructure your agent, your prompts, or your tool definitions. The signing key can be a local Ed25519 key pair you generate once, or a key ID that points at a cloud KMS if you already have one. Your existing LangChain agent behavior does not change. What changes is that every step now has a cryptographic receipt.
  </p>

  <!-- Section 4: Step 3 - Run your agent -->
  <h2 class="text-2xl font-bold mt-12 mb-4">Step 3: Run your agent once</h2>

  <p class="text-zinc-300 leading-relaxed mt-4">
    Run your agent the way you always do. A single conversation, a scripted test, a short session, any of it is enough to produce a trace file. The handler writes AgDR entries as the run progresses, so if the agent crashes mid-run you still get a partial, valid chain up to the point of failure. Partial evidence is still evidence.
  </p>

  <p class="text-zinc-300 leading-relaxed mt-4">
    The output is a structured log file, by default named after the run. We will use <code class="text-brand-purple bg-brand-purple/10 px-1.5 py-0.5 rounded text-sm">my-app.log</code> in the next step.
  </p>

  <!-- Mid-article CTA -->
  <div class="glass-panel rounded-xl p-8 my-12 text-center border-brand-red/20">
    <h3 class="text-xl font-bold mb-2">Start the forensic record before the incident</h3>
    <p class="text-sm text-zinc-400 mb-6"><code class="font-mono text-zinc-200">air</code> and <code class="font-mono text-zinc-200">airsdk</code> are MIT-licensed and open source. One <code class="font-mono text-zinc-200">pip install</code> and you have a signed chain.</p>
    <div class="flex flex-col sm:flex-row items-center justify-center gap-3">
      <a href="https://github.com/vindicara-inc/projectair?utm_source=blog&utm_medium=cta&utm_campaign=secure-ai-agents-5-minutes" class="btn-primary text-sm px-6 py-3">View on GitHub</a>
      <a href="https://vindicara.io/#how-it-works?utm_source=blog&utm_medium=cta&utm_campaign=secure-ai-agents-5-minutes" class="btn-secondary text-sm px-6 py-3">How AIR works</a>
    </div>
  </div>

  <!-- Section 5: Step 4 - Run air trace -->
  <h2 class="text-2xl font-bold mt-12 mb-4">Step 4: Run <code class="font-mono text-brand-purple">air trace</code></h2>

  <div class="code-block text-left my-6"><pre class="text-sm leading-relaxed overflow-x-auto"><code>air trace my-app.log</code></pre></div>

  <p class="text-zinc-300 leading-relaxed mt-4">
    The CLI walks the signed chain, verifies each hash and signature, and runs the trace against the OWASP Top 10 for Agentic Applications detection set. You get a console report that looks like this:
  </p>

  <div class="code-block text-left my-6"><pre class="text-sm leading-relaxed overflow-x-auto"><code>{`[AIR v0.1] Analyzing 247 agent steps across 3 conversations...

  ASI01 Agent Goal Hijack detected at step 47
  ASI02 Tool Misuse detected at step 51

[Export] forensic-report.json | forensic-report.pdf | forensic-report.siem`}</code></pre></div>

  <p class="text-zinc-300 leading-relaxed mt-4">
    Each finding ties back to a specific step in the signed chain. ASI01 (Agent Goal Hijack) flags steps where the agent's behavior drifted from the task it was given. ASI02 (Tool Misuse) flags steps where the agent invoked a tool in a way the threat model says it should not. The mapping is to the OWASP Top 10 for Agentic Applications 2026, the same taxonomy your security team is already standardizing on.
  </p>

  <p class="text-zinc-300 leading-relaxed mt-4">
    If nothing triggers, the run is clean. You still have a signed record that says so, timestamped, reproducible, and auditable.
  </p>

  <!-- Section 6: Step 5 - Export -->
  <h2 class="text-2xl font-bold mt-12 mb-4">Step 5: Export the forensic report</h2>

  <p class="text-zinc-300 leading-relaxed mt-4">
    The same scan emits three export formats out of the box:
  </p>

  <p class="text-zinc-300 leading-relaxed mt-4">
    <strong class="text-white"><code class="text-brand-purple bg-brand-purple/10 px-1.5 py-0.5 rounded text-sm">forensic-report.json</code></strong>. The full decision chain with every AgDR entry, every hash, every signature, and every detection. This is the canonical evidence artifact. Any downstream tool can consume it.
  </p>

  <p class="text-zinc-300 leading-relaxed mt-4">
    <strong class="text-white"><code class="text-brand-purple bg-brand-purple/10 px-1.5 py-0.5 rounded text-sm">forensic-report.pdf</code></strong>. A human-readable incident summary with the timeline, detections, and verification status. This is what legal, insurance, and executive stakeholders actually read.
  </p>

  <p class="text-zinc-300 leading-relaxed mt-4">
    <strong class="text-white"><code class="text-brand-purple bg-brand-purple/10 px-1.5 py-0.5 rounded text-sm">forensic-report.siem</code></strong>. A normalized event stream ready for ingestion by your SIEM. Findings become alerts, the decision chain becomes queryable events, and your SOC analysts see agent incidents alongside the rest of your security telemetry.
  </p>

  <p class="text-zinc-300 leading-relaxed mt-4">
    Five minutes in, you have a signed forensic record, ASI detections against OWASP Top 10 for Agentic Applications, and three export formats that plug into the tools security, legal, and the SOC already use. None of that existed before you installed <code class="text-brand-purple bg-brand-purple/10 px-1.5 py-0.5 rounded text-sm">projectair</code>.
  </p>

  <!-- Section 7: What comes next -->
  <h2 class="text-2xl font-bold mt-12 mb-4">What comes next</h2>

  <p class="text-zinc-300 leading-relaxed mt-4">
    The OSS path is enough to get a signed record of every agent run, detect ASI violations, and export evidence packs. That is the floor. The ceiling is AIR Cloud: the hosted incident response layer where the forensic record streams into a real-time dashboard, incident workflows and alerting fire on detection, and the compliance engine projects the same chain into <a href="/blog/eu-ai-act-article-72-guide" class="text-brand-purple hover:text-brand-purple/80 underline">EU AI Act Article 72</a> exports, California SB 53 incident reports, SOC 2 evidence, and insurance carrier formats.
  </p>

  <p class="text-zinc-300 leading-relaxed mt-4">
    Before any of that, the question is the record. If your agent ran today and something went wrong tomorrow, could you prove what happened? Five minutes from now, the answer is yes.
  </p>

  <!-- End-of-article CTA -->
  <div class="glass-panel rounded-xl p-8 my-12 text-center border-brand-red/20">
    <h3 class="text-xl font-bold mb-2">Your next incident is already on its way.</h3>
    <p class="text-sm text-zinc-400 mb-6">Make sure you can prove what happened. <code class="font-mono text-zinc-200">pip install projectair</code> and the record starts now.</p>
    <div class="flex flex-col sm:flex-row items-center justify-center gap-3">
      <a href="https://github.com/vindicara-inc/projectair?utm_source=blog&utm_medium=cta&utm_campaign=secure-ai-agents-5-minutes" class="btn-primary text-sm px-6 py-3">View on GitHub</a>
      <a href="https://vindicara.io/#how-it-works?utm_source=blog&utm_medium=cta&utm_campaign=secure-ai-agents-5-minutes" class="btn-secondary text-sm px-6 py-3">How AIR works</a>
    </div>
  </div>

  <!-- Related Posts -->
  <div class="mt-16 pt-8 border-t border-white/5">
    <h2 class="text-lg font-semibold mb-6">Related Posts</h2>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
      <a href="/blog/mcp-security-2026" class="glass-panel rounded-lg p-4 hover:border-brand-cyan/30 transition-colors block">
        <span class="text-[10px] font-bold uppercase tracking-wider text-brand-cyan">Research</span>
        <p class="text-sm font-medium mt-1">The State of MCP Security in 2026</p>
      </a>
      <a href="/blog/eu-ai-act-article-72-guide" class="glass-panel rounded-lg p-4 hover:border-green-500/30 transition-colors block">
        <span class="text-[10px] font-bold uppercase tracking-wider text-green-500">Compliance</span>
        <p class="text-sm font-medium mt-1">EU AI Act Article 72: A Developer's Guide</p>
      </a>
    </div>
  </div>
</article>
