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
      <!-- Post 0: Trustworthy Agents (Perspective, founder essay) -->
      <a href="/blog/trustworthy-agents-forensic-evidence" class="glass-panel rounded-xl p-6 hover:border-brand-red/30 transition-colors group block">
        <div class="flex items-center gap-2 mb-4">
          <span class="text-[10px] font-bold uppercase tracking-wider bg-brand-red/10 text-brand-red border border-brand-red/20 rounded-full px-2.5 py-0.5">Perspective</span>
          <span class="text-[10px] text-zinc-600">6 min read</span>
        </div>
        <h2 class="text-lg font-semibold mb-2 group-hover:text-brand-red transition-colors">Implementing Trustworthy Agents: A Forensic Evidence Layer for Production</h2>
        <p class="text-sm text-zinc-400 leading-relaxed">Anthropic's April 9 paper names three ecosystem gaps. Project AIR is our answer to evidence sharing and open standards.</p>
        <p class="text-xs text-zinc-600 mt-4">April 24, 2026</p>
      </a>

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
          <span class="text-[10px] font-bold uppercase tracking-wider bg-brand-purple/10 text-brand-purple border border-brand-purple/20 rounded-full px-2.5 py-0.5">Quickstart</span>
          <span class="text-[10px] text-zinc-600">5 min read</span>
        </div>
        <h2 class="text-lg font-semibold mb-2 group-hover:text-brand-purple transition-colors">Run your first <code class="font-mono">air trace</code> in 5 minutes</h2>
        <p class="text-sm text-zinc-400 leading-relaxed">From <code class="font-mono text-brand-purple">pip install projectair</code> to a signed forensic timeline of your LangChain agent. The <code class="font-mono text-brand-purple">air</code> CLI and <code class="font-mono text-brand-purple">airsdk</code> are open source today.</p>
        <p class="text-xs text-zinc-600 mt-4">April 18, 2026</p>
      </a>
    </div>
  </div>
</section>
