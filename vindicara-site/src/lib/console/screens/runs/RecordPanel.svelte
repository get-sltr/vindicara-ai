<script lang="ts">
  // One record, in full: the bodies the timeline row summarizes, plus the
  // hashes that make it evidence.
  import type { AgDRRecord } from '$lib/console/forensics/types';

  let { record }: { record: AgDRRecord | null } = $props();

  const bodyFields: Array<keyof AgDRRecord['payload']> = ['prompt', 'response', 'tool_name', 'tool_args', 'tool_output', 'final_output', 'user_intent'];

  function show(value: unknown): string {
    if (value === null || value === undefined) return '';
    return typeof value === 'string' ? value : JSON.stringify(value, null, 2);
  }
  function rest(payload: AgDRRecord['payload']): Array<[string, unknown]> {
    return Object.entries(payload).filter(([k, v]) => !bodyFields.includes(k as keyof AgDRRecord['payload']) && v !== null && v !== undefined);
  }
</script>

<div class="rp glass hud">
  {#if !record}
    <div class="lab">Select a step</div>
    <p>Click a row to see the prompt, response, tool arguments and output, and the hashes behind it.</p>
  {:else}
    <div class="ph"><h3>{record.kind}</h3><span class="hint mono">{record.timestamp}</span></div>
    {#each bodyFields as f}
      {#if record.payload[f] !== null && record.payload[f] !== undefined}
        <div class="field">
          <div class="lab">{String(f).replace('_', ' ')}</div>
          <pre>{show(record.payload[f])}</pre>
        </div>
      {/if}
    {/each}
    {#if rest(record.payload).length}
      <div class="field">
        <div class="lab">metadata</div>
        <pre>{show(Object.fromEntries(rest(record.payload)))}</pre>
      </div>
    {/if}
    <div class="hashes">
      <div><span class="lab">step id</span><code>{record.step_id}</code></div>
      <div><span class="lab">content hash</span><code>{record.content_hash}</code></div>
      <div><span class="lab">prev hash</span><code>{record.prev_hash}</code></div>
      <div><span class="lab">signer</span><code>{record.signer_key}</code></div>
      <div><span class="lab">signature</span><code>{record.signature_algorithm ?? 'ed25519'} · {record.signature.slice(0, 24)}…</code></div>
    </div>
  {/if}
</div>

<style>
  .rp { padding: 18px 20px; display: flex; flex-direction: column; gap: 12px; min-height: 240px; }
  .rp p { font-size: 13px; line-height: 1.5; color: var(--ink); }
  .lab { font-family: var(--mono); font-size: 10px; letter-spacing: .16em; text-transform: uppercase; color: var(--ink); }
  .field { display: flex; flex-direction: column; gap: 4px; }
  pre { margin: 0; padding: 10px 12px; border: 1px solid var(--stroke); background: rgba(0,0,0,.35); font-family: var(--mono); font-size: 12px; line-height: 1.5; color: var(--ink); white-space: pre-wrap; word-break: break-word; max-height: 320px; overflow: auto; }
  .hashes { display: grid; gap: 6px; padding-top: 8px; border-top: 1px solid var(--hair); }
  .hashes div { display: grid; grid-template-columns: 110px 1fr; gap: 10px; align-items: baseline; }
  .hashes code { font-family: var(--mono); font-size: 11px; color: var(--ink); word-break: break-all; }
  .mono { font-family: var(--mono); font-size: 11px; }
</style>
