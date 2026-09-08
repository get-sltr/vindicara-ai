<script lang="ts">
  // Keys: the screen a new sign-in lands on. Workspace, the shown-once key,
  // the snippet to paste, and key management. Everything here is live data
  // from AIR Cloud; there is no mock.
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { cloud, cloudSession, freshApiKey, forgetFreshKey } from '$lib/console/stores/cloud';
  import type { RedactedKey } from '$lib/console/api/cloud-types';
  import KeyReveal from './keys/KeyReveal.svelte';
  import KeyTable from './keys/KeyTable.svelte';
  import SetupSnippets from './keys/SetupSnippets.svelte';

  let keys = $state<RedactedKey[]>([]);
  let error = $state<string | null>(null);
  let busy = $state(false);

  let session = $derived($cloudSession);
  let canManage = $derived(session?.role === 'owner' || session?.role === 'admin');
  let cloudUrl = $derived(session?.cloud_url ?? '');
  let consoleUrl = $derived(session?.console_url ?? `${typeof location === 'undefined' ? '' : location.origin}/flightdeck`);

  async function refresh() {
    try {
      keys = await cloud.listKeys();
      error = null;
    } catch (e) {
      error = e instanceof Error ? e.message : 'Could not load keys.';
    }
  }

  async function create(input: { name: string; role: string }) {
    busy = true;
    try {
      const issued = await cloud.issueKey(input);
      freshApiKey.set(issued.key);
      await refresh();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Could not create the key.';
    } finally {
      busy = false;
    }
  }

  async function revoke(keyId: string) {
    busy = true;
    try {
      await cloud.revokeKey(keyId);
      await refresh();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Could not revoke the key.';
    } finally {
      busy = false;
    }
  }

  onMount(() => {
    if (!session) { void goto('/flightdeck/sign-in/'); return; }
    void refresh();
  });
</script>

<div class="keys reveal">
  <header class="kh glass hud k">
    <div>
      <div class="eyebrow">Workspace</div>
      <h1>{session?.workspace.name ?? 'workspace'}</h1>
      <div class="meta mono">{session?.workspace.workspace_id ?? ''} · {session?.workspace.tier ?? 'free'} tier · you are {session?.role ?? 'signed out'}</div>
    </div>
    <div class="kh-right">
      <div class="lab">Cloud</div>
      <div class="mono">{cloudUrl || 'not connected'}</div>
      <button class="btn" type="button" onclick={() => goto('/flightdeck/runs')}>Runs →</button>
    </div>
  </header>

  {#if error}<div class="err">{error}</div>{/if}

  {#if $freshApiKey}
    <KeyReveal apiKey={$freshApiKey} ondismiss={forgetFreshKey} />
  {/if}

  <SetupSnippets apiKey={$freshApiKey} {cloudUrl} {consoleUrl} />

  <KeyTable {keys} {canManage} {busy} oncreate={create} onrevoke={revoke} />
</div>

<style>
  .keys { display: flex; flex-direction: column; gap: 18px; }
  .kh { padding: 22px 24px; display: flex; align-items: flex-start; justify-content: space-between; gap: 18px; }
  .eyebrow { font-family: var(--mono); font-size: 10px; letter-spacing: .18em; text-transform: uppercase; color: var(--ink); }
  h1 { font-family: var(--display); font-size: 22px; font-weight: 600; margin-top: 4px; color: var(--ink); }
  .meta { font-size: 11px; margin-top: 6px; color: var(--ink); }
  .kh-right { text-align: right; display: flex; flex-direction: column; gap: 6px; align-items: flex-end; }
  .lab { font-family: var(--mono); font-size: 10px; letter-spacing: .16em; text-transform: uppercase; color: var(--ink); }
  .mono { font-family: var(--mono); font-size: 11px; }
  .err { padding: 10px 14px; border: 1px solid rgba(230,57,70,.5); background: rgba(230,57,70,.12); color: var(--ink); font-size: 12px; }
  @media (max-width: 720px) { .kh { flex-direction: column; } .kh-right { align-items: flex-start; text-align: left; } }
</style>
