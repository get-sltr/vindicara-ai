<script lang="ts">
  import vindicaraLogo from '$lib/assets/vindicara-logo.png';

  let { children } = $props();

  let mobileMenuOpen = $state(false);
</script>

<!-- NAV -->
<nav class="fixed top-0 w-full z-50 bg-obsidian/60 backdrop-blur-2xl border-b border-white/5">
  <div class="max-w-screen-2xl mx-auto px-6 flex items-center justify-between h-16">
    <a href="/" class="flex items-center gap-1">
      <img src={vindicaraLogo} alt="Vindicara" class="h-10 w-auto mix-blend-screen" />
      <span class="font-mono text-[10px] tracking-[0.18em] uppercase text-white border border-white/30 px-1.5 py-0.5 shadow-[0_0_10px_rgba(255,255,255,0.25)]">Project AIR™</span>
    </a>

    <div class="hidden md:flex items-center gap-8 text-sm text-zinc-400">
      <a href="/#how-it-works" class="hover:text-white transition-colors">Platform</a>
      <a href="/#standards" class="hover:text-white transition-colors">Standards</a>
      <a href="/blog" class="hover:text-white transition-colors text-white">Blog</a>
      <a href="/pricing" class="hover:text-white transition-colors">Pricing</a>
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
      <a href="/#how-it-works" class="block text-sm text-zinc-400 hover:text-white">Platform</a>
      <a href="/#standards" class="block text-sm text-zinc-400 hover:text-white">Standards</a>
      <a href="/blog" class="block text-sm text-white">Blog</a>
      <a href="/pricing" class="block text-sm text-zinc-400 hover:text-white">Pricing</a>
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
        <div class="flex items-center gap-1 mb-4">
          <img src={vindicaraLogo} alt="Vindicara" class="h-8 w-auto mix-blend-screen" />
          <span class="font-mono text-[10px] tracking-[0.18em] uppercase text-white border border-white/30 px-1.5 py-0.5 shadow-[0_0_10px_rgba(255,255,255,0.25)]">Project AIR™</span>
        </div>
        <p class="text-sm text-zinc-500 leading-relaxed">
          AI Incident Response. Forensic reconstruction, signed evidence, and containment for autonomous agents.
        </p>
      </div>

      <div>
        <h4 class="text-sm font-semibold mb-4">Product</h4>
        <ul class="space-y-2 text-sm text-zinc-500">
          <li><a href="/#how-it-works" class="hover:text-white transition-colors">Platform</a></li>
          <li><a href="/#standards" class="hover:text-white transition-colors">Standards</a></li>
          <li><a href="/pricing" class="hover:text-white transition-colors">Pricing</a></li>
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
