<script lang="ts">
  import vindicaraLogo from '$lib/assets/vindicara-logo.png';
  import ChainExplorer from '$lib/components/admissibility/ChainExplorer.svelte';
  import CertificationGenerator from '$lib/components/admissibility/CertificationGenerator.svelte';
  import FrameworkTabs from '$lib/components/admissibility/FrameworkTabs.svelte';

  let mobileMenuOpen = $state(false);

  function scrollTo(id: string) {
    mobileMenuOpen = false;
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  }

  // Hero terminal animation: cycling chain verification
  type TermLine = { text: string; color: string };
  const TERM_LINES: TermLine[] = [
    { text: '$ air trace prod-agent.log --verify', color: 'text-zinc-200' },
    { text: '[AIR v0.2.4] Loading forensic chain...', color: 'text-zinc-500' },
    { text: '  247 records | signer 7c3d9a1e4b8c2f5d...', color: 'text-zinc-500' },
    { text: '', color: '' },
    { text: '  [ok] step 000  agent_start     BLAKE3 + Ed25519 verified', color: 'text-green-400' },
    { text: '  [ok] step 001  llm_start       BLAKE3 + Ed25519 verified', color: 'text-green-400' },
    { text: '  [ok] step 002  tool_start      BLAKE3 + Ed25519 verified', color: 'text-green-400' },
    { text: '  ...', color: 'text-zinc-500' },
    { text: '  [ok] step 246  agent_finish    BLAKE3 + Ed25519 verified', color: 'text-green-400' },
    { text: '', color: '' },
    { text: '[chain intact] 247 of 247 records verified | 0 findings', color: 'text-green-400' },
    { text: '[written]     forensic-report.json (FRE 902(13) self-authenticating)', color: 'text-cyan-400' },
    { text: '[written]     exhibit-A.txt       (verification output)', color: 'text-cyan-400' },
    { text: '[written]     certification.md    (custodian declaration template)', color: 'text-cyan-400' },
  ];
  let termLineIndex = $state(0);
  $effect(() => {
    const interval = setInterval(() => {
      termLineIndex = (termLineIndex + 1) % (TERM_LINES.length + 18);
    }, 260);
    return () => clearInterval(interval);
  });

  type Bar = { label: string; short: string; airLine: string; operatorLine: string };
  const FOUR_BARS: Bar[] = [
    {
      label: 'Authenticity',
      short: 'Is the record what you claim it is?',
      airLine:
        'Ed25519 signature and embedded public key on every record. Verifiable offline against RFC 8032.',
      operatorLine: 'Document the key holder. Attest to the system.',
    },
    {
      label: 'Integrity',
      short: 'Has anything been altered since it was written?',
      airLine:
        'BLAKE3 content hashes forward-chained through every record. Any alteration breaks verification deterministically.',
      operatorLine: 'Preserve the log file. Write to append-only storage.',
    },
    {
      label: 'Attribution',
      short: 'Which system and which key produced this?',
      airLine:
        'Each record carries the signer\'s Ed25519 public key. Chain links prove ordering, timing, and identity.',
      operatorLine: 'Hold the private key under sole control. Document rotation.',
    },
    {
      label: 'Procedural admissibility',
      short: 'Does the process meet the formal requirements a court will apply?',
      airLine:
        'Deterministic, documented, and reproducible. Clears FRE 902(13), FRE 803(6), and eIDAS Articles 25-26.',
      operatorLine: 'Deploy continuously in production. Retain per policy.',
    },
  ];

  type CryptoPrim = { primitive: string; spec: string; url: string; security: string };
  const CRYPTO_PRIMITIVES: CryptoPrim[] = [
    {
      primitive: 'Ed25519 (EdDSA)',
      spec: 'RFC 8032',
      url: 'https://www.rfc-editor.org/rfc/rfc8032',
      security:
        '~128 bits. Deterministic signatures, batch verification, wide deployment: SSH, TLS 1.3, Signal, Git.',
    },
    {
      primitive: 'BLAKE3',
      spec: 'BLAKE3 reference spec',
      url: 'https://github.com/BLAKE3-team/BLAKE3-specs',
      security: '128-bit collision resistance, 256-bit preimage resistance. Default 256-bit output.',
    },
    {
      primitive: 'Canonical JSON',
      spec: 'RFC 8785 (JCS-compatible)',
      url: 'https://www.rfc-editor.org/rfc/rfc8785',
      security:
        'Deterministic encoding: sorted keys, no extraneous whitespace, UTF-8. Reproducible hash inputs.',
    },
    {
      primitive: 'UUIDv7',
      spec: 'RFC 9562',
      url: 'https://www.rfc-editor.org/rfc/rfc9562',
      security: '48-bit millisecond Unix timestamp prefix, random tail. Timestamp-sortable and unique.',
    },
  ];
</script>

<svelte:head>
  <title>Admissibility by Design: Court-Admissible AI Agent Forensics | Project AIR™</title>
  <meta
    name="description"
    content="Every Project AIR record is a Signed Intent Capsule: BLAKE3-hashed, Ed25519-signed, forward-chained. Mapped to US Federal Rules of Evidence 901/902/803, EU eIDAS Articles 25-26, EU AI Act Article 72, GDPR Article 30. Live chain verification and an FRE 902(13) certification generator included."
  />
  <meta
    name="keywords"
    content="AI agent evidence, AI forensic admissibility, FRE 902(13), FRE 803(6), FRE 901, eIDAS advanced electronic signature, EU AI Act Article 72, EU AI Act Article 12, GDPR Article 30, chain of custody, BLAKE3, Ed25519, Signed Intent Capsule, AgDR format, Project AIR, AI incident response"
  />
  <link rel="canonical" href="https://vindicara.io/admissibility" />
  <meta property="og:type" content="article" />
  <meta property="og:url" content="https://vindicara.io/admissibility" />
  <meta
    property="og:title"
    content="Admissibility by Design: Court-Admissible AI Agent Forensics"
  />
  <meta
    property="og:description"
    content="Signed Intent Capsules, forward-chained hashes, Ed25519 signatures. Mapped to FRE, eIDAS, EU AI Act, and GDPR. With a live chain explorer and an FRE 902(13) certification generator."
  />
  <meta name="twitter:card" content="summary_large_image" />
  <meta
    name="twitter:title"
    content="Admissibility by Design: Court-Admissible AI Agent Forensics"
  />
  <meta
    name="twitter:description"
    content="Project AIR's forensic chain mapped to FRE, eIDAS, EU AI Act, and GDPR. Live demo and certification generator included."
  />
  {@html `<script type="application/ld+json">${JSON.stringify({
    '@context': 'https://schema.org',
    '@type': 'TechArticle',
    headline: 'Admissibility by Design: Court-Admissible AI Agent Forensics',
    description:
      "How Project AIR's signed forensic chain maps to US Federal Rules of Evidence, EU eIDAS, EU AI Act Article 72, and GDPR Article 30.",
    about: [
      { '@type': 'Legislation', name: 'Federal Rules of Evidence 902(13)' },
      { '@type': 'Legislation', name: 'Federal Rules of Evidence 803(6)' },
      { '@type': 'Legislation', name: 'eIDAS Regulation (EU) No 910/2014' },
      { '@type': 'Legislation', name: 'Regulation (EU) 2024/1689 (AI Act)' },
      { '@type': 'Legislation', name: 'Regulation (EU) 2016/679 (GDPR)' },
    ],
    datePublished: '2026-04-21',
    dateModified: '2026-04-21',
    author: { '@type': 'Organization', name: 'Vindicara', url: 'https://vindicara.io' },
    publisher: { '@type': 'Organization', name: 'Vindicara', url: 'https://vindicara.io' },
    mainEntityOfPage: 'https://vindicara.io/admissibility',
    proficiencyLevel: 'Expert',
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
      <button onclick={() => scrollTo('four-bars')} class="hover:text-white transition-colors cursor-pointer">The four bars</button>
      <button onclick={() => scrollTo('chain')} class="hover:text-white transition-colors cursor-pointer">Chain explorer</button>
      <button onclick={() => scrollTo('frameworks')} class="hover:text-white transition-colors cursor-pointer">Frameworks</button>
      <button onclick={() => scrollTo('certification')} class="hover:text-white transition-colors cursor-pointer">Certification</button>
      <a href="/pricing" class="hover:text-white transition-colors">Pricing</a>
      <a href="/blog" class="hover:text-white transition-colors">Blog</a>
    </div>
    <div class="hidden md:flex items-center gap-3">
      <a href="https://github.com/get-sltr/vindicara-ai#readme" class="btn-secondary text-xs px-4 py-2">Docs</a>
      <a href="#certification" onclick={(e) => { e.preventDefault(); scrollTo('certification'); }} class="btn-primary text-xs px-4 py-2">Generate certification</a>
    </div>
    <button class="md:hidden text-zinc-400 hover:text-white" onclick={() => (mobileMenuOpen = !mobileMenuOpen)}>
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
      <button onclick={() => scrollTo('four-bars')} class="block text-sm text-zinc-400 hover:text-white w-full text-left">The four bars</button>
      <button onclick={() => scrollTo('chain')} class="block text-sm text-zinc-400 hover:text-white w-full text-left">Chain explorer</button>
      <button onclick={() => scrollTo('frameworks')} class="block text-sm text-zinc-400 hover:text-white w-full text-left">Frameworks</button>
      <button onclick={() => scrollTo('certification')} class="block text-sm text-zinc-400 hover:text-white w-full text-left">Certification</button>
      <a href="/pricing" class="block text-sm text-zinc-400 hover:text-white w-full text-left">Pricing</a>
      <a href="/blog" class="block text-sm text-zinc-400 hover:text-white w-full text-left">Blog</a>
    </div>
  {/if}
</nav>

<!-- HERO -->
<section class="pt-32 pb-20 px-6 relative overflow-hidden">
  <div class="absolute inset-0 bg-gradient-to-b from-brand-red/5 via-transparent to-transparent pointer-events-none"></div>
  <div class="max-w-screen-xl mx-auto relative">
    <div class="grid lg:grid-cols-[1.1fr_1fr] gap-12 items-center">
      <div>
        <div class="inline-flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.22em] text-brand-red mb-6 border border-brand-red/30 rounded px-3 py-1 bg-brand-red/5">
          <span class="w-1.5 h-1.5 rounded-full bg-brand-red animate-pulse"></span>
          Admissibility by design
        </div>
        <h1 class="text-4xl sm:text-5xl lg:text-6xl font-bold leading-[1.05] tracking-tight">
          <span class="text-gradient-subtle">Forensic incident response for agentic AI.</span>
          <br />
          <span class="text-gradient-brand">Admissible by design.</span>
        </h1>
        <p class="text-lg text-zinc-400 mt-6 leading-relaxed max-w-2xl">
          Your agent took an action. Something went wrong. Prevention tools tell you you tried to stop it. Project AIR tells you what happened, proves the record is untampered, and gets the proof accepted as evidence.
        </p>
        <div class="flex flex-col sm:flex-row gap-3 mt-8">
          <button type="button" onclick={() => scrollTo('certification')} class="btn-primary">
            Generate your FRE 902(13) certification
            <svg class="w-4 h-4 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <button type="button" onclick={() => scrollTo('chain')} class="btn-secondary">See the chain verify itself</button>
        </div>
        <div class="mt-6 text-xs text-zinc-500 leading-relaxed max-w-xl border-l-2 border-white/10 pl-4">
          Technical documentation, not legal advice. Admissibility is decided by the court hearing the matter. Consult qualified counsel before relying on Project AIR records in any legal proceeding.
        </div>
      </div>

      <!-- Hero terminal -->
      <div class="glass-panel rounded-xl overflow-hidden glow-red">
        <div class="flex items-center gap-2 px-4 py-3 border-b border-white/10 bg-black/40">
          <span class="w-3 h-3 rounded-full bg-brand-red/80"></span>
          <span class="w-3 h-3 rounded-full bg-amber-500/60"></span>
          <span class="w-3 h-3 rounded-full bg-green-500/60"></span>
          <span class="ml-3 font-mono text-[10px] tracking-[0.18em] uppercase text-zinc-500">air trace</span>
        </div>
        <div class="p-5 font-mono text-[12px] leading-relaxed min-h-[360px]">
          {#each TERM_LINES.slice(0, Math.min(termLineIndex + 1, TERM_LINES.length)) as line}
            <div class={line.color || 'text-zinc-400'}>{line.text || ' '}</div>
          {/each}
          {#if termLineIndex < TERM_LINES.length}
            <span class="inline-block w-2 h-4 bg-green-400 animate-pulse-glow"></span>
          {/if}
        </div>
      </div>
    </div>
  </div>
</section>

<!-- THE FOUR BARS -->
<section id="four-bars" class="py-20 px-6 border-t border-white/5">
  <div class="max-w-screen-xl mx-auto">
    <div class="max-w-3xl mb-12">
      <div class="font-mono text-[10px] uppercase tracking-[0.22em] text-brand-red mb-3">The framework</div>
      <h2 class="text-3xl sm:text-4xl font-bold leading-tight">
        Four bars. Evidence clears all four, or it is not evidence.
      </h2>
      <p class="text-zinc-400 mt-4 leading-relaxed">
        A court, a regulator, an auditor, an insurance loss adjuster. Every party that looks at your logs asks the same four questions. Project AIR answers the cryptographic ones by construction. You handle the procedural one. The line is explicit, not implied.
      </p>
    </div>

    <div class="grid md:grid-cols-2 gap-4">
      {#each FOUR_BARS as bar, i}
        <div class="glass-panel rounded-lg p-6 relative overflow-hidden">
          <div class="absolute top-0 right-0 font-mono text-[120px] leading-none text-white/[0.02] pointer-events-none select-none">
            0{i + 1}
          </div>
          <div class="relative">
            <div class="font-mono text-[10px] uppercase tracking-[0.18em] text-brand-red mb-2">
              Bar {i + 1}
            </div>
            <h3 class="text-xl font-bold text-white mb-1">{bar.label}</h3>
            <p class="text-sm text-zinc-500 italic mb-5">{bar.short}</p>
            <div class="space-y-3 text-sm">
              <div>
                <span class="inline-block font-mono text-[10px] uppercase tracking-wider text-green-400 border border-green-500/30 bg-green-500/5 rounded px-1.5 py-0.5 mr-2">
                  AIR
                </span>
                <span class="text-zinc-200 leading-relaxed">{bar.airLine}</span>
              </div>
              <div>
                <span class="inline-block font-mono text-[10px] uppercase tracking-wider text-amber-400 border border-amber-500/30 bg-amber-500/5 rounded px-1.5 py-0.5 mr-2">
                  You
                </span>
                <span class="text-zinc-400 leading-relaxed">{bar.operatorLine}</span>
              </div>
            </div>
          </div>
        </div>
      {/each}
    </div>
  </div>
</section>

<!-- CHAIN EXPLORER -->
<section id="chain" class="py-20 px-6 border-t border-white/5 bg-gradient-to-b from-transparent via-brand-red/[0.02] to-transparent">
  <div class="max-w-screen-xl mx-auto">
    <div class="max-w-3xl mb-10">
      <div class="font-mono text-[10px] uppercase tracking-[0.22em] text-brand-red mb-3">Integrity, live</div>
      <h2 class="text-3xl sm:text-4xl font-bold leading-tight">
        Tamper with the chain. Watch verification break at the exact step.
      </h2>
      <p class="text-zinc-400 mt-4 leading-relaxed">
        Every Project AIR record is a Signed Intent Capsule: BLAKE3 content hash, Ed25519 signature over the link to the previous record. Change any byte, anywhere, and the verifier reports the exact record where the chain snaps.
      </p>
    </div>

    <ChainExplorer />

    <div class="mt-6 grid sm:grid-cols-3 gap-3 text-xs font-mono text-zinc-500">
      <div class="glass-panel rounded p-3">
        <span class="text-green-400">[ok]</span> signature verifies, payload hash matches, chain intact upstream.
      </div>
      <div class="glass-panel rounded p-3">
        <span class="text-brand-red">[content mismatch]</span> the payload was altered after signing. Detected deterministically.
      </div>
      <div class="glass-panel rounded p-3">
        <span class="text-zinc-400">[unverifiable]</span> upstream break means downstream records cannot be trusted.
      </div>
    </div>
  </div>
</section>

<!-- THE RECORD -->
<section class="py-20 px-6 border-t border-white/5">
  <div class="max-w-screen-xl mx-auto grid lg:grid-cols-[1fr_1.2fr] gap-10 items-start">
    <div>
      <div class="font-mono text-[10px] uppercase tracking-[0.22em] text-brand-red mb-3">On-disk record shape (AgDR v0.2)</div>
      <h2 class="text-3xl sm:text-4xl font-bold leading-tight mb-5">
        Every record is a Signed Intent Capsule.
      </h2>
      <p class="text-zinc-400 leading-relaxed">
        OWASP's Agentic Security Initiative names "Signed Intent Capsule" as the emerging pattern for binding an agent's declared goal, constraints, and context to each execution cycle in a signed envelope. Project AIR writes that envelope for every agent step.
      </p>
      <p class="text-zinc-400 leading-relaxed mt-4">
        The format is AgDR-compatible: the same shape consumed by the open accountability.ai spec, so downstream verifiers, SIEMs, and custody chains work without proprietary tooling. Three primitives combine to produce the integrity guarantee.
      </p>
      <ul class="mt-6 space-y-3 text-sm text-zinc-300">
        <li class="flex gap-3">
          <span class="font-mono text-[10px] uppercase tracking-wider text-brand-red mt-1 shrink-0">01</span>
          <span><strong class="text-white">BLAKE3 content hashing.</strong> Canonicalised payload, 256-bit digest, reproducible offline.</span>
        </li>
        <li class="flex gap-3">
          <span class="font-mono text-[10px] uppercase tracking-wider text-brand-red mt-1 shrink-0">02</span>
          <span><strong class="text-white">Ed25519 digital signatures.</strong> RFC 8032. Deterministic, batch-verifiable, approx. 128 bits of security.</span>
        </li>
        <li class="flex gap-3">
          <span class="font-mono text-[10px] uppercase tracking-wider text-brand-red mt-1 shrink-0">03</span>
          <span><strong class="text-white">Forward-chained integrity.</strong> Each signature covers the previous record's hash. A single altered record invalidates every record downstream.</span>
        </li>
      </ul>
    </div>

    <div class="glass-panel rounded-lg p-5 overflow-hidden">
      <div class="flex items-center gap-2 mb-3">
        <span class="font-mono text-[10px] uppercase tracking-[0.18em] text-zinc-500">record.json</span>
      </div>
      <pre class="font-mono text-[11px] leading-relaxed overflow-auto"><span class="text-zinc-500">{'{'}</span>
  <span class="text-brand-cyan">"version"</span>:      <span class="text-green-400">"0.2"</span>,
  <span class="text-brand-cyan">"step_id"</span>:      <span class="text-green-400">"01962a7f-8c4e-7a00-b4a1-8d7e92f01234"</span>,
  <span class="text-brand-cyan">"timestamp"</span>:    <span class="text-green-400">"2026-04-21T14:32:01.248Z"</span>,
  <span class="text-brand-cyan">"kind"</span>:         <span class="text-green-400">"tool_start"</span>,
  <span class="text-brand-cyan">"payload"</span>: <span class="text-zinc-500">{'{'}</span>
    <span class="text-brand-cyan">"tool"</span>:       <span class="text-green-400">"send_email"</span>,
    <span class="text-brand-cyan">"args"</span>: <span class="text-zinc-500">{'{'}</span>
      <span class="text-brand-cyan">"to"</span>:       <span class="text-green-400">"customer@acme.co"</span>,
      <span class="text-brand-cyan">"subject"</span>:  <span class="text-green-400">"Refund processed"</span>
    <span class="text-zinc-500">{'},'}</span>
    <span class="text-brand-cyan">"user_intent"</span>: <span class="text-green-400">"refund order #8821"</span>
  <span class="text-zinc-500">{'},'}</span>
  <span class="text-brand-cyan">"prev_hash"</span>:    <span class="text-amber-400">"b2e5d9f3c8a4061f..."</span>,
  <span class="text-brand-cyan">"content_hash"</span>: <span class="text-amber-400">"c3f6e0a4d9b5172a..."</span>,
  <span class="text-brand-cyan">"signature"</span>:    <span class="text-brand-red">"9e5f1c3a6d0e4b7f..."</span>,
  <span class="text-brand-cyan">"signer_key"</span>:   <span class="text-brand-red">"7c3d9a1e4b8c2f5d..."</span>
<span class="text-zinc-500">{'}'}</span></pre>
    </div>
  </div>
</section>

<!-- FRAMEWORK TABS -->
<section id="frameworks" class="py-20 px-6 border-t border-white/5">
  <div class="max-w-screen-xl mx-auto">
    <div class="max-w-3xl mb-10">
      <div class="font-mono text-[10px] uppercase tracking-[0.22em] text-brand-red mb-3">Mapping to evidentiary frameworks</div>
      <h2 class="text-3xl sm:text-4xl font-bold leading-tight">
        The rules that will actually apply. And how Project AIR clears them.
      </h2>
      <p class="text-zinc-400 mt-4 leading-relaxed">
        Every claim on this page is grounded in published law. Click through the jurisdictions. Each rule gets a concrete citation and a specific statement of what Project AIR does to satisfy it.
      </p>
    </div>

    <FrameworkTabs />
  </div>
</section>

<!-- CERTIFICATION GENERATOR (primary CTA) -->
<section id="certification" class="py-24 px-6 border-t border-white/5 bg-gradient-to-b from-transparent via-brand-red/[0.04] to-transparent">
  <div class="max-w-screen-xl mx-auto">
    <div class="max-w-3xl mb-10">
      <div class="font-mono text-[10px] uppercase tracking-[0.22em] text-brand-red mb-3">The hook</div>
      <h2 class="text-3xl sm:text-5xl font-bold leading-tight">
        Generate your FRE 902(13) certification.
      </h2>
      <p class="text-zinc-400 mt-4 leading-relaxed text-lg">
        The declaration that turns a log file into self-authenticating evidence. Fill in the fields. Get a signed-ready template. Paste into Word, hand to counsel, file with your exhibit.
      </p>
    </div>

    <CertificationGenerator />

    <div class="mt-8 grid md:grid-cols-3 gap-4 text-sm">
      <div class="glass-panel rounded-lg p-5">
        <div class="font-mono text-[10px] uppercase tracking-[0.18em] text-brand-red mb-2">Template only</div>
        <p class="text-zinc-400 leading-relaxed">
          Adapted from the form contemplated by FRE 902(13) and 902(11). It is a starting point, not legal advice.
        </p>
      </div>
      <div class="glass-panel rounded-lg p-5">
        <div class="font-mono text-[10px] uppercase tracking-[0.18em] text-brand-red mb-2">Have counsel review</div>
        <p class="text-zinc-400 leading-relaxed">
          Procedural requirements vary by jurisdiction and case posture. Qualified counsel should review before you sign or file.
        </p>
      </div>
      <div class="glass-panel rounded-lg p-5">
        <div class="font-mono text-[10px] uppercase tracking-[0.18em] text-brand-red mb-2">Chain of custody</div>
        <p class="text-zinc-400 leading-relaxed">
          The certification describes the system. The operator still documents key management, log retention, and access controls.
        </p>
      </div>
    </div>
  </div>
</section>

<!-- WE PROVIDE / YOU PROVIDE -->
<section class="py-20 px-6 border-t border-white/5">
  <div class="max-w-screen-xl mx-auto">
    <div class="max-w-3xl mb-12">
      <div class="font-mono text-[10px] uppercase tracking-[0.22em] text-brand-red mb-3">Chain of custody</div>
      <h2 class="text-3xl sm:text-4xl font-bold leading-tight">
        What Project AIR provides. What you provide.
      </h2>
      <p class="text-zinc-400 mt-4 leading-relaxed">
        Cryptography prevents in-file tampering. It does not prevent whole-file substitution, key misuse, or retention failure. The line is explicit.
      </p>
    </div>

    <div class="grid lg:grid-cols-2 gap-6">
      <div class="glass-panel rounded-lg p-8">
        <div class="flex items-center gap-2 mb-6">
          <span class="font-mono text-[10px] uppercase tracking-[0.18em] text-green-400 border border-green-500/30 bg-green-500/5 rounded px-2 py-0.5">
            Project AIR
          </span>
          <span class="text-zinc-400 text-sm">provides</span>
        </div>
        <ul class="space-y-4 text-sm text-zinc-300">
          {#each [
            ['Integrity', 'Any alteration within a chain breaks verification. Detected deterministically by air trace.'],
            ['Authentication', 'Each record carries the signer\'s public key. Any party can verify offline.'],
            ['Chain linkage', 'Each record is cryptographically bound to its predecessor. Reordering or silent deletion is detectable.'],
            ['Forensic report', 'forensic-report.json is an auditor-readable artifact with verification status, findings, and record count.'],
            ['Open-source verifier', 'air trace and airsdk.verify_chain are MIT-licensed. No dependency on Project AIR infrastructure.'],
          ] as [label, body]}
            <li class="flex gap-3">
              <span class="text-green-400 shrink-0 font-mono">✓</span>
              <span>
                <strong class="text-white">{label}.</strong>
                <span class="text-zinc-400">{body}</span>
              </span>
            </li>
          {/each}
        </ul>
      </div>

      <div class="glass-panel rounded-lg p-8">
        <div class="flex items-center gap-2 mb-6">
          <span class="font-mono text-[10px] uppercase tracking-[0.18em] text-amber-400 border border-amber-500/30 bg-amber-500/5 rounded px-2 py-0.5">
            Operator
          </span>
          <span class="text-zinc-400 text-sm">provides</span>
        </div>
        <ul class="space-y-4 text-sm text-zinc-300">
          {#each [
            ['Key management', 'Who generates the signing key, where it is stored, who has access, rotation, revocation. Document in a key management policy.'],
            ['Log storage and preservation', 'Append-only storage (S3 Object Lock, GCS retention locks, WORM hardware). Retention policy documented.'],
            ['Access control', 'Who can read, write, delete logs. Segregation of duties matters.'],
            ['Timestamp verification', 'For strong timestamp admissibility, countersign chain checkpoints with an RFC 3161 trusted timestamp authority or an eIDAS Article 42 qualified timestamp service.'],
            ['Custodian identification', 'The qualified person under FRE 902(13) who signs the certification under oath.'],
            ['Deployment regularity', 'Continuous production deployment. One-off logging for litigation defeats the business-records exception.'],
          ] as [label, body]}
            <li class="flex gap-3">
              <span class="text-amber-400 shrink-0 font-mono">•</span>
              <span>
                <strong class="text-white">{label}.</strong>
                <span class="text-zinc-400">{body}</span>
              </span>
            </li>
          {/each}
        </ul>
      </div>
    </div>
  </div>
</section>

<!-- CRYPTOGRAPHIC PRIMITIVES -->
<section class="py-20 px-6 border-t border-white/5">
  <div class="max-w-screen-xl mx-auto">
    <div class="max-w-3xl mb-10">
      <div class="font-mono text-[10px] uppercase tracking-[0.22em] text-brand-red mb-3">Primitives</div>
      <h2 class="text-3xl sm:text-4xl font-bold leading-tight">
        Open standards, audited choices.
      </h2>
      <p class="text-zinc-400 mt-4 leading-relaxed">
        No pre-image attack, collision attack, or signature forgery is known against Ed25519 or BLAKE3 at the time of this writing. Both are conservative, audited, widely deployed choices.
      </p>
    </div>

    <div class="glass-panel rounded-lg overflow-hidden">
      <div class="hidden md:grid grid-cols-[1fr_1fr_2fr] px-6 py-3 border-b border-white/10 bg-black/30 font-mono text-[10px] uppercase tracking-[0.18em] text-zinc-500">
        <div>Primitive</div>
        <div>Specification</div>
        <div>Security note</div>
      </div>
      {#each CRYPTO_PRIMITIVES as prim, i}
        <div
          class="grid md:grid-cols-[1fr_1fr_2fr] gap-3 md:gap-6 px-6 py-5 text-sm {i <
          CRYPTO_PRIMITIVES.length - 1
            ? 'border-b border-white/5'
            : ''}"
        >
          <div class="font-mono text-white">{prim.primitive}</div>
          <div>
            <a
              href={prim.url}
              target="_blank"
              rel="noopener noreferrer"
              class="font-mono text-brand-cyan hover:text-white transition-colors inline-flex items-center gap-1"
            >
              {prim.spec}
              <span aria-hidden="true">↗</span>
            </a>
          </div>
          <div class="text-zinc-400 leading-relaxed">{prim.security}</div>
        </div>
      {/each}
    </div>
  </div>
</section>

<!-- LIMITATIONS -->
<section class="py-20 px-6 border-t border-white/5 bg-gradient-to-b from-transparent via-white/[0.02] to-transparent">
  <div class="max-w-screen-xl mx-auto">
    <div class="max-w-3xl mb-10">
      <div class="font-mono text-[10px] uppercase tracking-[0.22em] text-brand-red mb-3">Honest disclosures</div>
      <h2 class="text-3xl sm:text-4xl font-bold leading-tight">
        Limitations we own, out loud.
      </h2>
      <p class="text-zinc-400 mt-4 leading-relaxed">
        A security product that overclaims is worse than useless. Here is what Project AIR does not do.
      </p>
    </div>

    <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
      {#each [
        ['Admissibility is case-specific', 'No cryptographic architecture guarantees a record will be admitted in any given proceeding. Courts apply the rules to the facts.'],
        ['Timestamps are host-clock timestamps', 'For the strongest timestamp admissibility, countersign with a trusted timestamp authority (RFC 3161) or an eIDAS qualified timestamp service.'],
        ['Advanced, not qualified by default', 'AIR produces advanced electronic signatures under eIDAS. Qualified status requires a certificate from an EU-listed Qualified Trust Service Provider.'],
        ['Chain of custody is procedural', 'Cryptographic primitives are on us. Key management, log retention, and access control are on you.'],
        ['Jurisdictional variance', 'Strongest mapping is US FRE, EU eIDAS, EU AI Act, and GDPR. Other jurisdictions have analogous rules; local counsel handles the procedural fit.'],
        ['Key compromise is operational', 'Past signatures remain valid (the attacker cannot retroactively forge). Records produced between compromise and revocation are attacker-controlled. Standard opsec applies.'],
      ] as [label, body]}
        <div class="glass-panel rounded-lg p-5">
          <div class="font-mono text-[10px] uppercase tracking-wider text-zinc-500 mb-2">Disclosure</div>
          <h3 class="text-white font-semibold mb-2">{label}</h3>
          <p class="text-sm text-zinc-400 leading-relaxed">{body}</p>
        </div>
      {/each}
    </div>
  </div>
</section>

<!-- CTA -->
<section class="py-24 px-6 border-t border-white/5">
  <div class="max-w-screen-xl mx-auto">
    <div class="glass-panel rounded-xl p-8 sm:p-12 glow-red relative overflow-hidden">
      <div class="absolute inset-0 bg-gradient-to-br from-brand-red/10 via-transparent to-transparent pointer-events-none"></div>
      <div class="relative grid lg:grid-cols-[1.5fr_1fr] gap-10 items-center">
        <div>
          <div class="font-mono text-[10px] uppercase tracking-[0.22em] text-brand-red mb-3">Ship the proof</div>
          <h2 class="text-3xl sm:text-4xl font-bold leading-tight mb-4">
            Admissibility by design. Everything else is operations.
          </h2>
          <p class="text-zinc-400 leading-relaxed">
            Instrument your agent, write the chain, hand your custodian a pre-filled certification. Read the EU AI Act post-market monitoring playbook, or pick the pricing tier that covers your stack.
          </p>
        </div>
        <div class="flex flex-col gap-3">
          <button type="button" onclick={() => scrollTo('certification')} class="btn-primary w-full">
            Generate your certification
          </button>
          <a href="/blog/eu-ai-act-article-72-guide" class="btn-secondary w-full">
            EU AI Act Article 72 guide
          </a>
          <a
            href="https://github.com/get-sltr/vindicara-ai"
            target="_blank"
            rel="noopener noreferrer"
            class="text-center font-mono text-[11px] uppercase tracking-wider text-zinc-500 hover:text-white transition-colors pt-2"
          >
            Source: github.com/get-sltr/vindicara-ai ↗
          </a>
        </div>
      </div>

      <!-- pip install bar -->
      <div class="relative mt-8 pt-6 border-t border-white/10">
        <div class="font-mono text-[11px] text-zinc-500 mb-2">One line to instrument:</div>
        <div class="code-block flex items-center justify-between gap-3">
          <span class="text-zinc-300"><span class="text-brand-red">$</span> pip install projectair</span>
          <span class="font-mono text-[10px] uppercase tracking-wider text-zinc-600">v0.2.4 · MIT</span>
        </div>
      </div>
    </div>
  </div>
</section>

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
        <h4 class="text-sm font-semibold mb-4">Admissibility</h4>
        <ul class="space-y-2 text-sm text-zinc-500">
          <li><button onclick={() => scrollTo('four-bars')} class="hover:text-white transition-colors">The four bars</button></li>
          <li><button onclick={() => scrollTo('chain')} class="hover:text-white transition-colors">Chain explorer</button></li>
          <li><button onclick={() => scrollTo('frameworks')} class="hover:text-white transition-colors">Frameworks</button></li>
          <li><button onclick={() => scrollTo('certification')} class="hover:text-white transition-colors">FRE 902(13) template</button></li>
        </ul>
      </div>
      <div>
        <h4 class="text-sm font-semibold mb-4">Product</h4>
        <ul class="space-y-2 text-sm text-zinc-500">
          <li><a href="/" class="hover:text-white transition-colors">Home</a></li>
          <li><a href="/pricing" class="hover:text-white transition-colors">Pricing</a></li>
          <li><a href="/blog" class="hover:text-white transition-colors">Blog</a></li>
          <li><a href="https://github.com/get-sltr/vindicara-ai#readme" class="hover:text-white transition-colors">Docs</a></li>
        </ul>
      </div>
      <div>
        <h4 class="text-sm font-semibold mb-4">Company</h4>
        <ul class="space-y-2 text-sm text-zinc-500">
          <li><a href="mailto:Kevin.Minn@vindicara.io" class="hover:text-white transition-colors">Kevin.Minn@vindicara.io</a></li>
          <li><a href="mailto:legal@vindicara.io" class="hover:text-white transition-colors">legal@vindicara.io</a></li>
          <li><a href="mailto:security@vindicara.io" class="hover:text-white transition-colors">security@vindicara.io</a></li>
          <li><a href="https://github.com/get-sltr/vindicara-ai" class="hover:text-white transition-colors">GitHub</a></li>
        </ul>
      </div>
    </div>
    <div class="mt-12 pt-8 border-t border-white/5 flex flex-col md:flex-row items-center justify-between gap-4">
      <p class="text-xs text-zinc-600">&copy; 2026 Vindicara, Inc. · AI Incident Response.</p>
      <p class="text-xs text-zinc-600">Technical documentation. Not legal advice.</p>
    </div>
  </div>
</footer>
