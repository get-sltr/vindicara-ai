<script lang="ts">
  import { marked } from 'marked';
  import vindicaraLogo from '$lib/assets/vindicara-logo.png';

  interface Props {
    raw: string;
  }

  let { raw }: Props = $props();

  let mobileMenuOpen = $state(false);

  marked.setOptions({ gfm: true, breaks: false });

  // Strip YAML frontmatter delimited by --- ... --- at the top of the file.
  const withoutFrontmatter = $derived(raw.replace(/^---\n[\s\S]*?\n---\n/, ''));
  const html = $derived(marked.parse(withoutFrontmatter) as string);
</script>

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
      <a href="/pricing" class="hover:text-white transition-colors">Pricing</a>
    </div>

    <div class="hidden md:flex items-center gap-3">
      <a href="https://github.com/vindicara-inc/projectair#readme" class="btn-secondary text-xs px-4 py-2">Docs</a>
      <a href="https://github.com/vindicara-inc/projectair" class="btn-primary text-xs px-4 py-2">
        <svg class="w-4 h-4 mr-1.5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
        GitHub
      </a>
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
      <a href="/#how-it-works" class="block text-sm text-zinc-400 hover:text-white">How It Works</a>
      <a href="/#standards" class="block text-sm text-zinc-400 hover:text-white">Standards</a>
      <a href="/blog" class="block text-sm text-zinc-400 hover:text-white">Blog</a>
      <a href="/pricing" class="block text-sm text-zinc-400 hover:text-white">Pricing</a>
      <div class="flex gap-3 pt-2">
        <a href="https://github.com/vindicara-inc/projectair#readme" class="btn-secondary text-xs px-4 py-2">Docs</a>
        <a href="https://github.com/vindicara-inc/projectair" class="btn-primary text-xs px-4 py-2">GitHub</a>
      </div>
    </div>
  {/if}
</nav>

<main class="pt-24 pb-20 px-6">
  <article class="max-w-3xl mx-auto legal-content text-zinc-300 leading-relaxed">
    {@html html}
  </article>
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
          <li><a href="https://github.com/vindicara-inc/projectair#readme" class="hover:text-white transition-colors">Docs</a></li>
        </ul>
      </div>

      <div>
        <h3 class="text-sm font-semibold mb-4">Company</h3>
        <ul class="space-y-2 text-sm text-zinc-500">
          <li><a href="mailto:Kevin.Minn@vindicara.io" class="hover:text-white transition-colors">Kevin.Minn@vindicara.io</a></li>
          <li><a href="/blog" class="hover:text-white transition-colors">Blog</a></li>
          <li><a href="https://github.com/vindicara-inc/projectair" class="hover:text-white transition-colors">GitHub</a></li>
        </ul>
      </div>

      <div>
        <h3 class="text-sm font-semibold mb-4">Legal</h3>
        <ul class="space-y-2 text-sm text-zinc-500">
          <li><a href="/terms" class="hover:text-white transition-colors">Terms of Service</a></li>
          <li><a href="/privacy" class="hover:text-white transition-colors">Privacy Policy</a></li>
          <li><a href="/acceptable-use" class="hover:text-white transition-colors">Acceptable Use</a></li>
          <li><a href="/security" class="hover:text-white transition-colors">Security Disclosure</a></li>
        </ul>
      </div>
    </div>

    <div class="mt-12 pt-8 border-t border-white/5 flex flex-col md:flex-row items-center justify-between gap-4">
      <p class="text-xs text-zinc-600">&copy; 2026 Vindicara, Inc. · AI Incident Response.</p>
      <div class="flex items-center gap-4">
        <a href="https://github.com/vindicara-inc/projectair" class="text-zinc-600 hover:text-white transition-colors">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
        </a>
      </div>
    </div>
  </div>
</footer>

<style>
  .legal-content :global(h1) {
    font-size: 2.5rem;
    font-weight: 700;
    letter-spacing: -0.025em;
    color: white;
    margin-top: 0;
    margin-bottom: 1.25rem;
    line-height: 1.1;
  }
  .legal-content :global(h2) {
    font-size: 1.5rem;
    font-weight: 700;
    color: white;
    margin-top: 2.75rem;
    margin-bottom: 1rem;
    letter-spacing: -0.015em;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }
  .legal-content :global(h3) {
    font-size: 1.15rem;
    font-weight: 600;
    color: rgb(228, 228, 231);
    margin-top: 2rem;
    margin-bottom: 0.75rem;
  }
  .legal-content :global(h4) {
    font-size: 1rem;
    font-weight: 600;
    color: rgb(212, 212, 216);
    margin-top: 1.5rem;
    margin-bottom: 0.5rem;
  }
  .legal-content :global(p) {
    margin: 0 0 1rem 0;
    color: rgb(212, 212, 216);
  }
  .legal-content :global(a) {
    color: #dc2626;
    text-decoration: underline;
    text-decoration-color: rgba(220, 38, 38, 0.3);
    text-underline-offset: 3px;
    transition: color 0.15s, text-decoration-color 0.15s;
  }
  .legal-content :global(a:hover) {
    color: #ef4444;
    text-decoration-color: rgba(239, 68, 68, 0.6);
  }
  .legal-content :global(strong) {
    color: white;
    font-weight: 600;
  }
  .legal-content :global(ul),
  .legal-content :global(ol) {
    margin: 0 0 1rem 0;
    padding-left: 1.5rem;
  }
  .legal-content :global(li) {
    margin-bottom: 0.5rem;
    color: rgb(212, 212, 216);
  }
  .legal-content :global(li > ul),
  .legal-content :global(li > ol) {
    margin-top: 0.5rem;
    margin-bottom: 0.5rem;
  }
  .legal-content :global(blockquote) {
    margin: 1.5rem 0;
    padding: 1rem 1.25rem;
    border-left: 3px solid #dc2626;
    background: rgba(220, 38, 38, 0.06);
    color: rgb(228, 228, 231);
    font-size: 0.95rem;
  }
  .legal-content :global(blockquote > p) {
    margin-bottom: 0;
  }
  .legal-content :global(blockquote > p + p) {
    margin-top: 0.75rem;
  }
  .legal-content :global(code) {
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 0.875em;
    background: rgba(255, 255, 255, 0.05);
    color: #f4f4f5;
    padding: 0.15rem 0.4rem;
    border-radius: 0.25rem;
    border: 1px solid rgba(255, 255, 255, 0.08);
  }
  .legal-content :global(pre) {
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 0.85rem;
    background: #12121a;
    color: #e4e4e7;
    padding: 1rem 1.25rem;
    border-radius: 0.5rem;
    border: 1px solid rgba(255, 255, 255, 0.08);
    overflow-x: auto;
    margin: 1.25rem 0;
  }
  .legal-content :global(pre code) {
    background: transparent;
    border: none;
    padding: 0;
    font-size: inherit;
  }
  .legal-content :global(hr) {
    border: none;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    margin: 2.5rem 0;
  }
  .legal-content :global(table) {
    width: 100%;
    border-collapse: collapse;
    margin: 1.5rem 0;
    font-size: 0.9rem;
  }
  .legal-content :global(th),
  .legal-content :global(td) {
    padding: 0.625rem 0.75rem;
    text-align: left;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
  .legal-content :global(th) {
    background: rgba(255, 255, 255, 0.04);
    color: white;
    font-weight: 600;
  }
  .legal-content :global(td) {
    color: rgb(212, 212, 216);
  }
</style>
