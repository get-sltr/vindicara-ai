<script lang="ts">
  import { SNIPPETS, runLinkHint, shellHeader } from './snippets';

  let { apiKey, cloudUrl, consoleUrl }: { apiKey: string | null; cloudUrl: string; consoleUrl: string } = $props();
  let active = $state(SNIPPETS[0].id);
  let copied = $state('');

  let snippet = $derived(SNIPPETS.find((s) => s.id === active) ?? SNIPPETS[0]);
  let header = $derived(shellHeader(apiKey, cloudUrl));

  function copy(text: string, key: string) {
    try { void navigator.clipboard?.writeText(text); } catch { /* clipboard unavailable */ }
    copied = key;
    setTimeout(() => { if (copied === key) copied = ''; }, 1800);
  }
</script>

<div class="ss glass hud">
  <div class="ph"><h3>Set up your agent</h3><span class="hint">two lines in the shell, one block in Python</span></div>

  <div class="tabs" role="tablist">
    {#each SNIPPETS as s (s.id)}
      <button class="tab" class:on={active === s.id} type="button" role="tab" aria-selected={active === s.id} onclick={() => (active = s.id)}>{s.name}</button>
    {/each}
  </div>

  <div class="block">
    <div class="bh"><span>Shell</span><button class="btn" type="button" onclick={() => copy(header, 'sh')}>{copied === 'sh' ? 'Copied' : 'Copy'}</button></div>
    <pre>{header}</pre>
  </div>

  <div class="block">
    <div class="bh"><span>Python</span><button class="btn" type="button" onclick={() => copy(snippet.code, 'py')}>{copied === 'py' ? 'Copied' : 'Copy'}</button></div>
    <pre>{snippet.code}</pre>
  </div>

  <p class="hint-line">{runLinkHint(consoleUrl)}</p>
  <p class="hint-line">The local chain stays on your disk. Payloads are mirrored to <span class="air">AIR</span> Cloud while the key is set; <code>AIRSDK_CLOUD=off</code> stops it.</p>
</div>

<style>
  .ss { padding: 20px 22px; display: flex; flex-direction: column; gap: 12px; }
  .tabs { display: flex; flex-wrap: wrap; gap: 6px; }
  .tab { font-family: var(--ui); font-size: 11px; padding: 5px 10px; border: 1px solid var(--hair); background: rgba(255,255,255,.03); color: var(--ink); cursor: pointer; }
  .tab.on { border-color: var(--air); color: var(--ink); background: rgba(230,57,70,.12); }
  .block { border: 1px solid var(--stroke); background: rgba(0,0,0,.35); }
  .bh { display: flex; align-items: center; justify-content: space-between; padding: 6px 10px; border-bottom: 1px solid var(--hair); font-family: var(--mono); font-size: 10px; letter-spacing: .12em; text-transform: uppercase; color: var(--ink); }
  pre { margin: 0; padding: 12px 14px; font-family: var(--mono); font-size: 12px; line-height: 1.55; color: var(--ink); overflow-x: auto; white-space: pre; }
  .hint-line { font-size: 12px; line-height: 1.5; color: var(--ink); }
  .hint-line code { font-family: var(--mono); }
  .hint-line :global(.air), .air { color: var(--air); font-weight: 700; }
</style>
