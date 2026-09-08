<script lang="ts">
  // One run: verification and health at the top, the incident table in the
  // middle, the selected record on the side. Bodies are fetched separately
  // and paged so a long run never stalls the page.
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { cloud, cloudSession } from '$lib/console/stores/cloud';
  import type { RunDetail } from '$lib/console/api/cloud-types';
  import type { AgDRRecord } from '$lib/console/forensics/types';
  import RunTable from './runs/RunTable.svelte';
  import RecordPanel from './runs/RecordPanel.svelte';

  let { runId }: { runId: string } = $props();

  const PAGE = 100;
  let detail = $state<RunDetail | null>(null);
  let records = $state<Map<string, AgDRRecord>>(new Map());
  let total = $state(0);
  let selected = $state<string | null>(null);
  let error = $state<string | null>(null);
  let copied = $state(false);

  let selectedRecord = $derived(selected ? (records.get(selected) ?? null) : null);

  async function loadPage(offset: number) {
    const page = await cloud.getRunRecords(runId, { limit: PAGE, offset });
    total = page.count;
    const next = new Map(records);
    for (const r of page.records) next.set(r.step_id, r);
    records = next;
  }

  onMount(async () => {
    if (!$cloudSession) { void goto('/flightdeck/sign-in/'); return; }
    try {
      detail = await cloud.getRun(runId);
      await loadPage(0);
      selected = detail.timeline.entries[0]?.step_id ?? null;
    } catch (e) {
      error = e instanceof Error ? e.message : 'Could not load this run.';
    }
  });

  async function select(stepId: string) {
    selected = stepId;
    if (!records.has(stepId) && records.size < total) {
      const entry = detail?.timeline.entries.find((e) => e.step_id === stepId);
      if (entry) await loadPage(Math.floor(entry.ordinal / PAGE) * PAGE);
    }
  }

  function copyLink() {
    try { void navigator.clipboard?.writeText(detail?.console_url ?? location.href); } catch { /* clipboard unavailable */ }
    copied = true;
    setTimeout(() => (copied = false), 1800);
  }
  function levelClass(level: string): string {
    return level === 'ok' ? 's-covered' : level === 'warn' ? 's-uncovered' : 's-expired';
  }
</script>

<div class="rd reveal">
  <header class="rh">
    <div>
      <button class="crumb" type="button" onclick={() => goto('/flightdeck/runs')}>← Runs</button>
      <h1>{detail?.summary.user_intent ?? 'Run'}</h1>
      <div class="mono meta">{runId}</div>
    </div>
    <div class="actions">
      {#if detail}
        <span class="st {detail.verification.status === 'ok' ? 's-covered' : 's-uncovered'}">chain {detail.verification.status}</span>
        <span class="st {levelClass(detail.health.level)}">evidence {detail.health.level}</span>
        <span class="st {detail.findings.length ? 's-uncovered' : 's-covered'}">{detail.findings.length} finding{detail.findings.length === 1 ? '' : 's'}</span>
      {/if}
      <button class="btn" type="button" onclick={copyLink}>{copied ? 'Link copied' : 'Copy link'}</button>
    </div>
  </header>

  {#if error}<div class="err">{error}</div>{/if}

  {#if detail}
    {#if detail.timeline.gaps.length}
      <div class="gaps glass hud k">
        <div class="lab">Where the evidence is missing</div>
        <ul>{#each detail.timeline.gaps as g}<li>{g}</li>{/each}</ul>
      </div>
    {/if}

    <div class="body">
      <RunTable entries={detail.timeline.entries} {selected} onselect={select} />
      <RecordPanel record={selectedRecord} />
    </div>

    <div class="health glass hud">
      <div class="ph"><h3>Evidence health</h3><span class="hint">{detail.summary.records} record(s) · {detail.timeline.anchors} anchor(s)</span></div>
      <div class="checks">
        {#each detail.health.checks as c (c.key)}
          <div class="check"><span class="st {levelClass(c.level)}">{c.level}</span><span class="ct">{c.title}</span><span class="cd">{c.detail}</span></div>
        {/each}
      </div>
    </div>
  {/if}
</div>

<style>
  .rd { display: flex; flex-direction: column; gap: 18px; }
  .rh { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; }
  .crumb { background: none; border: 0; color: var(--ink); font-family: var(--mono); font-size: 11px; cursor: pointer; padding: 0; }
  h1 { font-family: var(--display); font-size: 20px; font-weight: 600; margin-top: 6px; color: var(--ink); }
  .meta { margin-top: 4px; }
  .mono { font-family: var(--mono); font-size: 11px; color: var(--ink); }
  .actions { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }
  .err { padding: 10px 14px; border: 1px solid rgba(230,57,70,.5); background: rgba(230,57,70,.12); color: var(--ink); font-size: 12px; }
  .gaps { padding: 14px 18px; }
  .gaps ul { margin: 8px 0 0 18px; font-size: 12px; line-height: 1.6; color: var(--ink); }
  .lab { font-family: var(--mono); font-size: 10px; letter-spacing: .16em; text-transform: uppercase; color: var(--ink); }
  .body { display: grid; grid-template-columns: minmax(0, 1.6fr) minmax(280px, 1fr); gap: 18px; align-items: start; }
  .health { padding: 18px 20px; }
  .checks { display: flex; flex-direction: column; gap: 8px; }
  .check { display: grid; grid-template-columns: 56px 180px 1fr; gap: 12px; align-items: baseline; font-size: 12px; color: var(--ink); }
  .ct { font-weight: 600; }
  @media (max-width: 980px) { .body { grid-template-columns: 1fr; } .check { grid-template-columns: 56px 1fr; } .cd { grid-column: 2; } }
</style>
