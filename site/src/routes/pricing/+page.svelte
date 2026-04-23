<script lang="ts">
  import vindicaraLogo from '$lib/assets/vindicara-logo.png';

  let mobileMenuOpen = $state(false);
</script>

<svelte:head>
  <title>Pricing | Vindicara AIR</title>
  <meta name="description" content="Vindicara AIR pricing. Open source forever under MIT license. Team at $1,499/mo for AIR Cloud, hosted incident response, SIEM export. Enterprise at $50K to $250K ACV for regulated industries." />
  <link rel="canonical" href="https://vindicara.io/pricing" />

  <meta property="og:type" content="website" />
  <meta property="og:url" content="https://vindicara.io/pricing" />
  <meta property="og:title" content="Pricing | Vindicara AIR" />
  <meta property="og:description" content="Open source forever. Team at $1,499/mo. Enterprise at $50K to $250K ACV. The air CLI and airsdk are free under MIT. AIR Cloud is coming soon." />
  <meta property="og:image:alt" content="Vindicara AIR pricing: three tiers from open source to enterprise." />

  <meta name="twitter:title" content="Pricing | Vindicara AIR" />
  <meta name="twitter:description" content="Open source forever. Team at $1,499/mo. Enterprise at $50K to $250K ACV. AIR Cloud is coming soon." />

  {@html `<script type="application/ld+json">${JSON.stringify({
    '@context': 'https://schema.org',
    '@type': 'Product',
    '@id': 'https://vindicara.io/pricing#product',
    name: 'Vindicara AIR',
    description: 'Forensic reconstruction and incident response for AI agents. Signed forensic evidence from agent traces.',
    brand: { '@type': 'Brand', name: 'Vindicara' },
    url: 'https://vindicara.io/pricing',
    offers: [
      {
        '@type': 'Offer',
        name: 'Open Source',
        price: '0',
        priceCurrency: 'USD',
        availability: 'https://schema.org/InStock',
        description: 'MIT-licensed air CLI, airsdk Python SDK with LangChain callback, signed AgDR evidence chain, community support.',
        url: 'https://github.com/get-sltr/vindicara-ai',
      },
      {
        '@type': 'Offer',
        name: 'Team',
        price: '1499',
        priceCurrency: 'USD',
        availability: 'https://schema.org/PreOrder',
        description: 'AIR Cloud for security and platform teams. Hosted incident dashboard up to 25 agents, SIEM export, workflows, alerting.',
        priceSpecification: {
          '@type': 'UnitPriceSpecification',
          price: '1499',
          priceCurrency: 'USD',
          billingIncrement: 1,
          unitText: 'MONTH',
        },
      },
      {
        '@type': 'Offer',
        name: 'Enterprise',
        availability: 'https://schema.org/PreOrder',
        description: 'SSO, SAML, RBAC. EU AI Act, SB 53, SOC 2 evidence exports. Insurance carrier integrations. SLA, dedicated IR contact, BAA.',
        priceSpecification: {
          '@type': 'PriceSpecification',
          minPrice: '50000',
          maxPrice: '250000',
          priceCurrency: 'USD',
        },
      },
    ],
  })}<\/script>`}

  {@html `<script type="application/ld+json">${JSON.stringify({
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: 'https://vindicara.io/' },
      { '@type': 'ListItem', position: 2, name: 'Pricing', item: 'https://vindicara.io/pricing' },
    ],
  })}<\/script>`}
</svelte:head>

<!-- NAV -->
<nav class="fixed top-0 w-full z-50 bg-obsidian/60 backdrop-blur-2xl border-b border-white/5">
  <div class="max-w-screen-2xl mx-auto px-6 flex items-center justify-between h-16">
    <a href="/" class="flex items-center gap-1">
      <img src={vindicaraLogo} alt="Vindicara" class="h-10 w-auto mix-blend-screen" />
      <span class="font-mono text-[10px] tracking-[0.18em] uppercase text-white border border-white/30 px-1.5 py-0.5 shadow-[0_0_10px_rgba(255,255,255,0.25)]">Project AIR™</span>
    </a>

    <div class="hidden md:flex items-center gap-8 text-sm text-zinc-400">
      <a href="/#how-it-works" class="hover:text-white transition-colors">How It Works</a>
      <a href="/#standards" class="hover:text-white transition-colors">Standards</a>
      <a href="/blog" class="hover:text-white transition-colors">Blog</a>
      <a href="/pricing" class="text-white">Pricing</a>
    </div>

    <div class="hidden md:flex items-center gap-3">
      <a href="https://github.com/get-sltr/vindicara-ai#readme" class="btn-secondary text-xs px-4 py-2">Docs</a>
      <a href="https://github.com/get-sltr/vindicara-ai" class="btn-primary text-xs px-4 py-2">
        <svg class="w-4 h-4 mr-1.5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
        GitHub
      </a>
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
      <a href="/#how-it-works" class="block text-sm text-zinc-400 hover:text-white">How It Works</a>
      <a href="/#standards" class="block text-sm text-zinc-400 hover:text-white">Standards</a>
      <a href="/blog" class="block text-sm text-zinc-400 hover:text-white">Blog</a>
      <a href="/pricing" class="block text-sm text-white">Pricing</a>
      <div class="flex gap-3 pt-2">
        <a href="https://github.com/get-sltr/vindicara-ai#readme" class="btn-secondary text-xs px-4 py-2">Docs</a>
        <a href="https://github.com/get-sltr/vindicara-ai" class="btn-primary text-xs px-4 py-2">GitHub</a>
      </div>
    </div>
  {/if}
</nav>

<main class="pt-16">
  <!-- HEADER -->
  <section class="py-20 relative">
    <div class="absolute inset-0">
      <img src="/hero-mesh.png" alt="" class="w-full h-full object-cover opacity-20" />
      <div class="absolute inset-0 bg-gradient-to-b from-obsidian via-obsidian/90 to-obsidian"></div>
    </div>
    <div class="relative max-w-screen-xl mx-auto px-6 text-center">
      <p class="text-brand-red text-sm font-semibold uppercase tracking-wider mb-4 font-mono">Pricing</p>
      <h1 class="text-4xl sm:text-5xl font-bold tracking-tight max-w-3xl mx-auto">Open source today. Cloud soon.</h1>
      <p class="mt-5 text-lg text-zinc-400 max-w-2xl mx-auto leading-relaxed">
        The <code class="font-mono text-zinc-200">air</code> CLI and <code class="font-mono text-zinc-200">airsdk</code> Python SDK are MIT-licensed and free forever. AIR Cloud adds hosted incident response, SIEM export, and compliance evidence workflows for teams that need them.
      </p>
    </div>
  </section>

  <!-- TIER CARDS -->
  <section class="pb-20">
    <div class="max-w-screen-xl mx-auto px-6">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-0 border border-white/10 max-w-5xl mx-auto">
        <!-- Open Source -->
        <div class="p-8 border-b lg:border-b-0 lg:border-r border-white/10">
          <div class="flex items-center justify-between mb-2">
            <h2 class="text-sm font-mono uppercase tracking-wider text-zinc-400">Open Source</h2>
            <span class="font-mono text-[10px] text-green-400 border border-green-400/30 bg-green-400/5 px-2 py-0.5 uppercase tracking-wider">Available</span>
          </div>
          <p class="text-4xl font-black mt-4">Free</p>
          <p class="text-sm text-zinc-500 mt-1">Forever. MIT license.</p>
          <ul class="mt-8 space-y-3 text-sm text-zinc-400">
            <li class="flex items-start gap-2"><span class="text-brand-red mt-0.5 font-mono">›</span><span><span class="font-mono text-zinc-200">air</span> CLI: trace ingest, ASI detection, forensic export</span></li>
            <li class="flex items-start gap-2"><span class="text-brand-red mt-0.5 font-mono">›</span><span><span class="font-mono text-zinc-200">airsdk</span> with LangChain, OpenAI, Anthropic instrumentation</span></li>
            <li class="flex items-start gap-2"><span class="text-brand-red mt-0.5 font-mono">›</span><span>10 OWASP Agentic detectors + 3 LLM + 1 AIR-native</span></li>
            <li class="flex items-start gap-2"><span class="text-brand-red mt-0.5 font-mono">›</span><span>Signed Intent Capsule chain, local-only</span></li>
            <li class="flex items-start gap-2"><span class="text-brand-red mt-0.5 font-mono">›</span><span>JSON, PDF, SIEM, and Article 72 template export</span></li>
            <li class="flex items-start gap-2"><span class="text-brand-red mt-0.5 font-mono">›</span><span>Community support</span></li>
          </ul>
          <a href="https://github.com/get-sltr/vindicara-ai" class="btn-secondary w-full mt-8 text-sm">View on GitHub</a>
        </div>

        <!-- Team -->
        <div class="p-8 border-b lg:border-b-0 lg:border-r border-white/10 bg-white/[0.015]">
          <div class="flex items-center justify-between mb-2">
            <h2 class="text-sm font-mono uppercase tracking-wider text-zinc-400">Team</h2>
            <span class="font-mono text-[10px] text-brand-red border border-brand-red/30 bg-brand-red/5 px-2 py-0.5 uppercase tracking-wider">Coming Soon</span>
          </div>
          <p class="text-4xl font-black mt-4">$1,499<span class="text-base font-normal text-zinc-500">/mo</span></p>
          <p class="text-sm text-zinc-500 mt-1">AIR Cloud for security and platform teams.</p>
          <ul class="mt-8 space-y-3 text-sm text-zinc-400">
            <li class="flex items-start gap-2"><span class="text-brand-red mt-0.5 font-mono">›</span><span>Everything in Open Source</span></li>
            <li class="flex items-start gap-2"><span class="text-brand-red mt-0.5 font-mono">›</span><span>Hosted incident dashboard, up to 25 agents</span></li>
            <li class="flex items-start gap-2"><span class="text-brand-red mt-0.5 font-mono">›</span><span>SIEM export: Datadog, Splunk, Sumo</span></li>
            <li class="flex items-start gap-2"><span class="text-brand-red mt-0.5 font-mono">›</span><span>Incident workflows and alerting</span></li>
            <li class="flex items-start gap-2"><span class="text-brand-red mt-0.5 font-mono">›</span><span>Email and Slack support</span></li>
          </ul>
          <a href="mailto:Kevin.Minn@vindicara.io?subject=AIR%20Team%20early%20access" class="btn-secondary w-full mt-8 text-sm">Request Early Access</a>
        </div>

        <!-- Enterprise -->
        <div class="p-8">
          <div class="flex items-center justify-between mb-2">
            <h2 class="text-sm font-mono uppercase tracking-wider text-zinc-400">Enterprise</h2>
            <span class="font-mono text-[10px] text-brand-red border border-brand-red/30 bg-brand-red/5 px-2 py-0.5 uppercase tracking-wider">Coming Soon</span>
          </div>
          <p class="text-4xl font-black mt-4">$50K<span class="text-base font-normal text-zinc-500">–$250K ACV</span></p>
          <p class="text-sm text-zinc-500 mt-1">For regulated industries and insurance.</p>
          <ul class="mt-8 space-y-3 text-sm text-zinc-400">
            <li class="flex items-start gap-2"><span class="text-brand-red mt-0.5 font-mono">›</span><span>Everything in Team</span></li>
            <li class="flex items-start gap-2"><span class="text-brand-red mt-0.5 font-mono">›</span><span>SSO, SAML, RBAC, audit-grade access controls</span></li>
            <li class="flex items-start gap-2"><span class="text-brand-red mt-0.5 font-mono">›</span><span>EU AI Act, SB 53, SOC 2 evidence exports</span></li>
            <li class="flex items-start gap-2"><span class="text-brand-red mt-0.5 font-mono">›</span><span>Insurance carrier integrations</span></li>
            <li class="flex items-start gap-2"><span class="text-brand-red mt-0.5 font-mono">›</span><span>SLA, dedicated IR contact, BAA</span></li>
          </ul>
          <a href="mailto:Kevin.Minn@vindicara.io?subject=AIR%20Enterprise" class="btn-secondary w-full mt-8 text-sm">Contact Us</a>
        </div>
      </div>
    </div>
  </section>

  <!-- FEATURE COMPARISON -->
  <section class="py-20 border-t border-white/5">
    <div class="max-w-screen-xl mx-auto px-6">
      <div class="text-center mb-14">
        <p class="text-brand-red text-sm font-semibold uppercase tracking-wider mb-3 font-mono">Compare</p>
        <h2 class="text-3xl sm:text-4xl font-bold tracking-tight">What you get at each tier</h2>
      </div>

      <div class="max-w-5xl mx-auto overflow-x-auto">
        <table class="w-full text-sm border border-white/10">
          <thead>
            <tr class="bg-white/[0.02] text-zinc-400">
              <th class="text-left p-4 font-mono text-xs uppercase tracking-wider font-semibold border-b border-white/10">Capability</th>
              <th class="text-center p-4 font-mono text-xs uppercase tracking-wider font-semibold border-b border-white/10">Open Source</th>
              <th class="text-center p-4 font-mono text-xs uppercase tracking-wider font-semibold border-b border-white/10 bg-white/[0.015]">Team</th>
              <th class="text-center p-4 font-mono text-xs uppercase tracking-wider font-semibold border-b border-white/10">Enterprise</th>
            </tr>
          </thead>
          <tbody class="text-zinc-300">
            <tr class="border-b border-white/5">
              <td class="p-4"><span class="font-mono text-zinc-200">air</span> CLI and <span class="font-mono text-zinc-200">airsdk</span></td>
              <td class="p-4 text-center text-green-400">✓</td>
              <td class="p-4 text-center text-green-400 bg-white/[0.015]">✓</td>
              <td class="p-4 text-center text-green-400">✓</td>
            </tr>
            <tr class="border-b border-white/5">
              <td class="p-4">Signed AgDR evidence chain</td>
              <td class="p-4 text-center text-green-400">✓</td>
              <td class="p-4 text-center text-green-400 bg-white/[0.015]">✓</td>
              <td class="p-4 text-center text-green-400">✓</td>
            </tr>
            <tr class="border-b border-white/5">
              <td class="p-4">OWASP detection: 10 Agentic ASIs + 3 LLM Top 10 + 1 AIR-native</td>
              <td class="p-4 text-center text-green-400">✓</td>
              <td class="p-4 text-center text-green-400 bg-white/[0.015]">✓</td>
              <td class="p-4 text-center text-green-400">✓</td>
            </tr>
            <tr class="border-b border-white/5">
              <td class="p-4">Hosted incident dashboard</td>
              <td class="p-4 text-center text-zinc-600">–</td>
              <td class="p-4 text-center text-green-400 bg-white/[0.015]">Up to 25 agents</td>
              <td class="p-4 text-center text-green-400">Unlimited</td>
            </tr>
            <tr class="border-b border-white/5">
              <td class="p-4">SIEM export (Datadog, Splunk, Sumo)</td>
              <td class="p-4 text-center text-zinc-600">–</td>
              <td class="p-4 text-center text-green-400 bg-white/[0.015]">✓</td>
              <td class="p-4 text-center text-green-400">✓</td>
            </tr>
            <tr class="border-b border-white/5">
              <td class="p-4">Incident workflows and alerting</td>
              <td class="p-4 text-center text-zinc-600">–</td>
              <td class="p-4 text-center text-green-400 bg-white/[0.015]">✓</td>
              <td class="p-4 text-center text-green-400">✓</td>
            </tr>
            <tr class="border-b border-white/5">
              <td class="p-4">Compliance evidence exports (EU AI Act Article 72, SB 53, SOC 2, NIST AI RMF)</td>
              <td class="p-4 text-center text-zinc-300">Article 72 template</td>
              <td class="p-4 text-center text-zinc-300 bg-white/[0.015]">Article 72 template</td>
              <td class="p-4 text-center text-green-400">Branded PDF, multi-system</td>
            </tr>
            <tr class="border-b border-white/5">
              <td class="p-4">Insurance carrier integrations</td>
              <td class="p-4 text-center text-zinc-600">–</td>
              <td class="p-4 text-center text-zinc-600 bg-white/[0.015]">–</td>
              <td class="p-4 text-center text-green-400">✓</td>
            </tr>
            <tr class="border-b border-white/5">
              <td class="p-4">SSO, SAML, RBAC</td>
              <td class="p-4 text-center text-zinc-600">–</td>
              <td class="p-4 text-center text-zinc-600 bg-white/[0.015]">–</td>
              <td class="p-4 text-center text-green-400">✓</td>
            </tr>
            <tr class="border-b border-white/5">
              <td class="p-4">SLA and dedicated IR contact</td>
              <td class="p-4 text-center text-zinc-600">–</td>
              <td class="p-4 text-center text-zinc-600 bg-white/[0.015]">–</td>
              <td class="p-4 text-center text-green-400">✓</td>
            </tr>
            <tr>
              <td class="p-4">Support</td>
              <td class="p-4 text-center text-zinc-400">Community</td>
              <td class="p-4 text-center text-zinc-300 bg-white/[0.015]">Email and Slack</td>
              <td class="p-4 text-center text-zinc-300">24/7 with SLA</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>

  <!-- FAQ -->
  <section class="py-20 border-t border-white/5">
    <div class="max-w-screen-xl mx-auto px-6">
      <div class="text-center mb-14">
        <p class="text-brand-red text-sm font-semibold uppercase tracking-wider mb-3 font-mono">Questions</p>
        <h2 class="text-3xl sm:text-4xl font-bold tracking-tight">Before you ask</h2>
      </div>

      <div class="max-w-3xl mx-auto space-y-8">
        <div>
          <h3 class="text-lg font-semibold text-white mb-2">What stays free forever?</h3>
          <p class="text-sm text-zinc-400 leading-relaxed">
            The <code class="font-mono text-zinc-200">air</code> CLI, the <code class="font-mono text-zinc-200">airsdk</code> Python SDK, the signed AgDR evidence chain, and seven detectors spanning OWASP Top 10 for Agentic Applications (ASI01, ASI02, ASI04 partial) + OWASP Top 10 for LLM Applications (LLM01, LLM04, LLM06) + one AIR-native forensic-chain-integrity check. JSON, PDF, and SIEM (ArcSight CEF) export formats included. All of it MIT-licensed and self-hosted. No seat limits, no trace limits, no feature gates that flip when a timer runs out.
          </p>
        </div>

        <div>
          <h3 class="text-lg font-semibold text-white mb-2">Why is Team listed as coming soon?</h3>
          <p class="text-sm text-zinc-400 leading-relaxed">
            AIR Cloud is in closed beta with design partners. We are working through hosted incident dashboards, SIEM export, and alerting with real IR teams before we open it up. If your team wants early access, email <a href="mailto:Kevin.Minn@vindicara.io?subject=AIR%20Team%20early%20access" class="text-brand-red hover:text-brand-red/80 underline">Kevin.Minn@vindicara.io</a> and we will get you in the next cohort.
          </p>
        </div>

        <div>
          <h3 class="text-lg font-semibold text-white mb-2">When does Team not cover it, and Enterprise does?</h3>
          <p class="text-sm text-zinc-400 leading-relaxed">
            Team is the right fit if you run a platform or security team that wants hosted incident response, SIEM integration, and alerting. Enterprise is the right fit if you also need regulatory evidence exports (EU AI Act Article 72, California SB 53, SOC 2), insurance carrier integrations, SSO/SAML, BAA, or an SLA with a dedicated IR contact. The short version: if your auditor or your carrier is a stakeholder, you want Enterprise.
          </p>
        </div>

        <div>
          <h3 class="text-lg font-semibold text-white mb-2">Does the forensic record work offline?</h3>
          <p class="text-sm text-zinc-400 leading-relaxed">
            Yes. The OSS tier is local-only by design. AgDR entries are signed and chained on the machine running the agent, with no cloud dependency. AIR Cloud is opt-in and adds hosted storage, dashboards, and integrations, but the forensic chain itself is portable: you can export it and hand it to any downstream system or auditor.
          </p>
        </div>

        <div>
          <h3 class="text-lg font-semibold text-white mb-2">How does the Enterprise range work?</h3>
          <p class="text-sm text-zinc-400 leading-relaxed">
            Enterprise ACV depends on agent volume, the compliance frameworks in scope, and whether you need insurance integrations or a BAA. Most regulated-industry deployments land in the middle of the range. We put a published range here instead of a "Contact Us" black box because procurement teams deserve honest numbers.
          </p>
        </div>

        <div>
          <h3 class="text-lg font-semibold text-white mb-2">Is there a free trial of AIR Cloud?</h3>
          <p class="text-sm text-zinc-400 leading-relaxed">
            Not yet. Early access to AIR Cloud is hands-on: we work directly with design partners to wire up their stack, and that is the best version of a trial we can offer right now. The OSS tier is available today and covers the entire forensic record path end to end, so you can evaluate AIR's detections and evidence chain before any Cloud conversation.
          </p>
        </div>
      </div>
    </div>
  </section>

  <!-- CTA -->
  <section class="py-20 relative overflow-hidden border-t border-white/5">
    <div class="absolute inset-0">
      <img src="/hero-mesh.png" alt="" class="w-full h-full object-cover opacity-25" />
      <div class="absolute inset-0 bg-gradient-to-t from-obsidian via-obsidian/95 to-obsidian"></div>
    </div>
    <div class="relative max-w-screen-xl mx-auto px-6 text-center">
      <h2 class="text-3xl sm:text-4xl font-bold tracking-tight max-w-3xl mx-auto">
        Start the forensic record today.<br />
        <span class="text-gradient-brand">Upgrade when your team needs the dashboard.</span>
      </h2>
      <div class="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
        <a href="https://github.com/get-sltr/vindicara-ai" class="btn-primary text-base px-8 py-4">
          <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
          View on GitHub
        </a>
        <a href="mailto:Kevin.Minn@vindicara.io" class="btn-secondary text-base px-8 py-4">Talk to us</a>
      </div>
      <div class="mt-8">
        <div class="inline-block bg-obsidian-lighter border border-white/10 px-4 py-2 font-mono text-sm text-zinc-300">
          <span class="text-zinc-500">$</span> pip install projectair
        </div>
      </div>
    </div>
  </section>
</main>

<!-- FOOTER -->
<footer class="w-full border-t border-white/5 bg-obsidian relative z-20">
  <div class="max-w-screen-xl mx-auto px-6 py-14">
    <div class="grid grid-cols-2 md:grid-cols-4 gap-8">
      <div class="col-span-2 md:col-span-1">
        <div class="flex items-center gap-1 mb-4">
          <img src={vindicaraLogo} alt="Vindicara" class="h-8 w-auto mix-blend-screen" />
          <span class="font-mono text-[10px] tracking-[0.18em] uppercase text-white border border-white/30 px-1.5 py-0.5 shadow-[0_0_10px_rgba(255,255,255,0.25)]">Project AIR™</span>
        </div>
        <p class="text-sm text-zinc-500 leading-relaxed">
          AI Incident Response. Forensic reconstruction, signed evidence, and containment for autonomous agents.
        </p>
      </div>

      <div>
        <h3 class="text-sm font-semibold mb-4">Product</h3>
        <ul class="space-y-2 text-sm text-zinc-500">
          <li><a href="/#how-it-works" class="hover:text-white transition-colors">How It Works</a></li>
          <li><a href="/#standards" class="hover:text-white transition-colors">Standards</a></li>
          <li><a href="/pricing" class="hover:text-white transition-colors">Pricing</a></li>
          <li><a href="https://github.com/get-sltr/vindicara-ai#readme" class="hover:text-white transition-colors">Docs</a></li>
        </ul>
      </div>

      <div>
        <h3 class="text-sm font-semibold mb-4">Company</h3>
        <ul class="space-y-2 text-sm text-zinc-500">
          <li><a href="mailto:Kevin.Minn@vindicara.io" class="hover:text-white transition-colors">Kevin.Minn@vindicara.io</a></li>
          <li><a href="/blog" class="hover:text-white transition-colors">Blog</a></li>
          <li><a href="https://github.com/get-sltr/vindicara-ai" class="hover:text-white transition-colors">GitHub</a></li>
        </ul>
      </div>

      <div>
        <h3 class="text-sm font-semibold mb-4">Legal</h3>
        <ul class="space-y-2 text-sm text-zinc-500">
          <li><a href="mailto:legal@vindicara.io?subject=Privacy" class="hover:text-white transition-colors">Privacy</a></li>
          <li><a href="mailto:legal@vindicara.io?subject=Terms" class="hover:text-white transition-colors">Terms</a></li>
          <li><a href="mailto:security@vindicara.io" class="hover:text-white transition-colors">Security</a></li>
        </ul>
      </div>
    </div>

    <div class="mt-12 pt-8 border-t border-white/5 flex flex-col md:flex-row items-center justify-between gap-4">
      <p class="text-xs text-zinc-600">&copy; 2026 Vindicara, Inc. · AI Incident Response.</p>
      <div class="flex items-center gap-4">
        <a href="https://github.com/get-sltr/vindicara-ai" class="text-zinc-600 hover:text-white transition-colors">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
        </a>
      </div>
    </div>
  </div>
</footer>
