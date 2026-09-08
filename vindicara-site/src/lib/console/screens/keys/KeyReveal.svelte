<script lang="ts">
  // The one moment the secret is visible. Copy it, or dismiss it; either way
  // it leaves memory when this card closes and can never be fetched again.
  let { apiKey, ondismiss }: { apiKey: string; ondismiss: () => void } = $props();
  let copied = $state(false);

  function copy() {
    try { void navigator.clipboard?.writeText(apiKey); } catch { /* clipboard unavailable */ }
    copied = true;
    setTimeout(() => (copied = false), 1800);
  }
</script>

<div class="reveal-card glass hud k">
  <div class="rc-head">
    <span class="rc-dot"></span>
    <span class="rc-title">Your workspace API key</span>
    <span class="rc-once">shown once</span>
  </div>
  <p class="rc-body">Copy it now. <span class="air">AIR</span> Cloud stores only a hash, so this key cannot be shown again. If you lose it, issue a new one below and revoke this one.</p>
  <div class="rc-key">
    <code>{apiKey}</code>
    <button class="btn" type="button" onclick={copy}>{copied ? 'Copied' : 'Copy'}</button>
  </div>
  <div class="rc-actions">
    <button class="btn warn" type="button" onclick={ondismiss}>I saved it</button>
  </div>
</div>

<style>
  .reveal-card { padding: 20px 22px; display: flex; flex-direction: column; gap: 12px; border-color: rgba(230,57,70,.4); }
  .rc-head { display: flex; align-items: center; gap: 10px; }
  .rc-dot { width: 9px; height: 9px; background: var(--air); box-shadow: 0 0 12px var(--air); }
  .rc-title { font-family: var(--display); font-size: 13px; letter-spacing: .08em; text-transform: uppercase; color: var(--ink); }
  .rc-once { margin-left: auto; font-family: var(--mono); font-size: 10px; letter-spacing: .12em; text-transform: uppercase; color: #ffd49a; border: 1px solid rgba(255,180,84,.4); padding: 3px 8px; }
  .rc-body { font-size: 13px; line-height: 1.55; color: var(--ink); }
  .rc-body :global(.air), .air { color: var(--air); font-weight: 700; }
  .rc-key { display: flex; align-items: center; gap: 12px; padding: 12px 14px; border: 1px solid var(--stroke); background: rgba(0,0,0,.35); }
  .rc-key code { font-family: var(--mono); font-size: 13px; color: var(--ink); word-break: break-all; flex: 1; }
  .rc-actions { display: flex; justify-content: flex-end; }
</style>
