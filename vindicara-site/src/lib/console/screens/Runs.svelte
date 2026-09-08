<script lang="ts">
  // Runs: every recorder session that reached AIR Cloud, newest first. Polls
  // while the tab is visible so a first run appears within seconds of landing.
  import { onDestroy, onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { cloud, cloudSession } from '$lib/console/stores/cloud';
  import type { RunSummary } from '$lib/console/api/cloud-types';
  import { SNIPPETS } from './keys/snippets';

  const POLL_MS = 3000;
  let runs = $state<RunSummary[]>([]);
  let count = $state(0);
  let error = $state<string | null>(null);
  let loaded = $state(false);
  let timer: ReturnType<typeof setInterval> | undefined;

  async function refresh() {
    if (typeof document !== 'undefined' && document.visibilityState !== 'visible') return;
    try {
      const page = await cloud.listRuns({ limit: 50 });
      runs = page.runs;
      count = page.count;
      error = null;
    } catch (e) {
      error = e instanceof Error ? e.message : 'Could not load runs.';
    } finally {
      loaded = true;
    }
  }

  onMount(() => {
    if (!$cloudSession) { void goto('/flightdeck/sign-in/'); return; }
    void refresh();
    timer = setInterval(() => void refresh(), POLL_MS);
  });
  onDestroy(() => { if (timer) clearInterval(timer); });

  function when(iso: string): string {
    return iso.slice(0, 19).replace('T', ' ');
  }
  function kinds(k: Record<string, number>): string {
    return Object.entries(k).map(([name, n]) => `${n} ${name.replace('_', ' ')}`).join(', ');
  }
  function verifyClass(v: RunSummary['verification']): string {
    if (v === 'ok') return 's-covered';
    if (v === null) return 's-expired';
    return 's-uncovered';
  }
</script>

<div class="runs reveal">
  <header class="rh">
    <div>
      <div class="eyebrow">Runs</div>
      <h1>{count} run{count === 1 ? '' : 's'} in {$cloudSession?.workspace.name ?? 'your workspace'}</h1>
    </div>
    <button class="btn" type="button" onclick={() => goto('/flightdeck/keys')}>Keys and setup →</button>
  </header>

  {#if error}<div class="err">{error}</div>{/if}

  {#if loaded && runs.length === 0}
    <div class="empty glass hud k">
      <div class="lab">Waiting for your first run</div>
      <p>Set <code>AIRSDK_CLOUD_API_KEY</code> in the shell your agent runs in, then run it. This page refreshes every {POLL_MS / 1000} seconds.</p>
      <pre>{SNIPPETS[SNIPPETS.length - 1].code}</pre>
      <button class="btn" type="button" onclick={() => goto('/flightdeck/keys')}>Get your key</button>
    </div>
  {:else if runs.length > 0}
    <div class="table glass hud">
      <table>
        <thead><tr><th>Started</th><th>Last</th><th>Records</th><th>What the user asked</th><th>Kinds</th><th>Verification</th><th>Findings</th></tr></thead>
        <tbody>
          {#each runs as r (r.run_id)}
            <tr class="row" onclick={() => goto(`/flightdeck/runs/${r.run_id}`)}>
              <td class="mono">{when(r.first_at)}</td>
              <td class="mono">{when(r.last_at)}</td>
              <td class="mono">{r.records}</td>
              <td class="intent">{r.user_intent ?? '(no intent recorded)'}</td>
              <td class="kinds">{kinds(r.kinds)}</td>
              <td><span class="st {verifyClass(r.verification)}">{r.verification ?? 'open to assess'}</span></td>
              <td>
                {#if r.findings === null}<span class="mono">–</span>
                {:else if r.findings === 0}<span class="st s-covered">0</span>
                {:else}<span class="st s-uncovered">{r.findings} · {r.max_severity}</span>{/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>

<style>
  .runs { display: flex; flex-direction: column; gap: 18px; }
  .rh { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; }
  .eyebrow, .lab { font-family: var(--mono); font-size: 10px; letter-spacing: .18em; text-transform: uppercase; color: var(--ink); }
  h1 { font-family: var(--display); font-size: 22px; font-weight: 600; margin-top: 4px; color: var(--ink); }
  .err { padding: 10px 14px; border: 1px solid rgba(230,57,70,.5); background: rgba(230,57,70,.12); color: var(--ink); font-size: 12px; }
  .empty { padding: 24px; display: flex; flex-direction: column; gap: 12px; }
  .empty p { font-size: 13px; line-height: 1.55; color: var(--ink); }
  .empty code { font-family: var(--mono); }
  .empty pre { margin: 0; padding: 12px 14px; border: 1px solid var(--stroke); background: rgba(0,0,0,.35); font-family: var(--mono); font-size: 12px; color: var(--ink); overflow-x: auto; }
  .table { padding: 8px 10px; overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; font-size: 12px; }
  th { text-align: left; font-family: var(--mono); font-size: 10px; letter-spacing: .12em; text-transform: uppercase; color: var(--ink); padding: 8px; border-bottom: 1px solid var(--stroke); }
  td { padding: 10px 8px; border-bottom: 1px solid var(--hair); color: var(--ink); vertical-align: middle; }
  .row { cursor: pointer; }
  .row:hover td { background: rgba(255,255,255,.04); }
  .mono { font-family: var(--mono); font-size: 11px; }
  .intent { max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .kinds { font-size: 11px; }
</style>
