<script lang="ts">
  import type { RedactedKey } from '$lib/console/api/cloud-types';

  let {
    keys,
    canManage,
    busy,
    oncreate,
    onrevoke
  }: {
    keys: RedactedKey[];
    canManage: boolean;
    busy: boolean;
    oncreate: (input: { name: string; role: string }) => void;
    onrevoke: (keyId: string) => void;
  } = $props();

  let name = $state('');
  let role = $state('member');
  let confirming = $state<string | null>(null);

  function submit(e: SubmitEvent) {
    e.preventDefault();
    oncreate({ name: name.trim() || 'unnamed key', role });
    name = '';
  }
</script>

<div class="kt glass hud">
  <div class="ph"><h3>API keys</h3><span class="hint">{keys.filter((k) => !k.revoked_at).length} active</span></div>

  <table>
    <thead><tr><th>Name</th><th>Key id</th><th>Role</th><th>Created</th><th></th></tr></thead>
    <tbody>
      {#each keys as k (k.key_id)}
        <tr class:revoked={!!k.revoked_at}>
          <td>{k.name ?? 'unnamed key'}</td>
          <td class="mono">{k.key_id}</td>
          <td><span class="st s-covered">{k.role}</span></td>
          <td class="mono">{k.created_at.slice(0, 19).replace('T', ' ')}</td>
          <td class="act">
            {#if k.revoked_at}
              <span class="st s-expired">revoked</span>
            {:else if canManage}
              {#if confirming === k.key_id}
                <button class="btn crit" type="button" disabled={busy} onclick={() => { onrevoke(k.key_id); confirming = null; }}>Confirm revoke</button>
                <button class="btn" type="button" onclick={() => (confirming = null)}>Keep</button>
              {:else}
                <button class="btn warn" type="button" disabled={busy} onclick={() => (confirming = k.key_id)}>Revoke</button>
              {/if}
            {/if}
          </td>
        </tr>
      {:else}
        <tr><td colspan="5" class="empty">No keys yet.</td></tr>
      {/each}
    </tbody>
  </table>

  {#if canManage}
    <form class="create" onsubmit={submit}>
      <input class="in" placeholder="Key name (laptop, CI, prod-agent)" bind:value={name} />
      <select class="in" bind:value={role}>
        <option value="owner">owner</option>
        <option value="admin">admin</option>
        <option value="member">member</option>
        <option value="viewer">viewer</option>
      </select>
      <button class="btn" type="submit" disabled={busy}>Create key</button>
    </form>
  {/if}
</div>

<style>
  .kt { padding: 20px 22px; display: flex; flex-direction: column; gap: 14px; }
  table { width: 100%; border-collapse: collapse; font-size: 12px; }
  th { text-align: left; font-family: var(--mono); font-size: 10px; letter-spacing: .12em; text-transform: uppercase; color: var(--ink); padding: 6px 8px; border-bottom: 1px solid var(--stroke); }
  td { padding: 9px 8px; border-bottom: 1px solid var(--hair); color: var(--ink); vertical-align: middle; }
  .mono { font-family: var(--mono); font-size: 11px; }
  .revoked td { text-decoration: line-through; }
  .revoked td.act { text-decoration: none; }
  .act { text-align: right; white-space: nowrap; display: flex; gap: 6px; justify-content: flex-end; }
  .empty { text-align: center; padding: 18px; }
  .create { display: grid; grid-template-columns: 1fr 140px auto; gap: 8px; }
  .in { font-family: var(--ui); font-size: 12px; padding: 7px 10px; border: 1px solid var(--stroke); background: rgba(0,0,0,.3); color: var(--ink); }
  @media (max-width: 720px) { .create { grid-template-columns: 1fr; } }
</style>
