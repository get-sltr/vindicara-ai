<script lang="ts">
  // The incident columns per step: what executed, under whose authority,
  // where the evidence stands. Rows come from the server's timeline, the same
  // one `air incident` prints.
  import type { TimelineEntry } from '$lib/console/api/cloud-types';

  let { entries, selected, onselect }: { entries: TimelineEntry[]; selected: string | null; onselect: (stepId: string) => void } = $props();

  function clock(iso: string): string {
    return iso.length >= 19 ? iso.slice(11, 19) : iso;
  }
  function evidenceClass(e: TimelineEntry['evidence']): string {
    if (e === 'anchored') return 's-covered';
    if (e === 'signed') return 's-expired';
    return 's-uncovered';
  }
  function authorityLabel(a: TimelineEntry['authority']): string {
    return a.subject ? `${a.kind}: ${a.subject}` : a.kind;
  }
</script>

<div class="rt glass hud">
  <table>
    <thead><tr><th>#</th><th>Time</th><th>Step</th><th>What executed</th><th>Authority</th><th>Evidence</th><th>Findings</th></tr></thead>
    <tbody>
      {#each entries as e (e.step_id)}
        <tr class="row" class:on={selected === e.step_id} onclick={() => onselect(e.step_id)}>
          <td class="mono">{e.ordinal}</td>
          <td class="mono">{clock(e.timestamp)}</td>
          <td class="mono">{e.kind}</td>
          <td class="what" title={e.summary}>{e.summary}</td>
          <td class="auth" title={e.authority.detail}>{authorityLabel(e.authority)}</td>
          <td><span class="st {evidenceClass(e.evidence)}" title={e.evidence_detail}>{e.evidence}</span></td>
          <td class="mono">{e.findings.join(', ')}</td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>

<style>
  .rt { padding: 8px 10px; overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; font-size: 12px; }
  th { text-align: left; font-family: var(--mono); font-size: 10px; letter-spacing: .12em; text-transform: uppercase; color: var(--ink); padding: 8px; border-bottom: 1px solid var(--stroke); }
  td { padding: 9px 8px; border-bottom: 1px solid var(--hair); color: var(--ink); vertical-align: middle; }
  .row { cursor: pointer; }
  .row:hover td, .row.on td { background: rgba(255,255,255,.05); }
  .row.on td:first-child { box-shadow: inset 3px 0 0 var(--air); }
  .mono { font-family: var(--mono); font-size: 11px; white-space: nowrap; }
  .what { max-width: 360px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .auth { max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-family: var(--mono); font-size: 11px; }
</style>
