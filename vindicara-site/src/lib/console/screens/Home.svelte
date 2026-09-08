<script lang="ts">
  // Home: the screen a sign-in lands on. Combines what used to be two screens,
  // the workspace/key setup and the landing, into one onboarding path: who you
  // are, the key, the snippet to paste, and a live wait for the first run.
  //
  // Shape follows the LangSmith home (identity, one hook line, OR-separated
  // paths, inline key issue, copyable snippet, "waiting for data"). Palette and
  // type are the console's own tokens, not the reference's.
  import { onMount, onDestroy } from 'svelte';
  import { goto } from '$app/navigation';
  import { cloud, cloudSession, freshApiKey, forgetFreshKey } from '$lib/console/stores/cloud';
  import KeyReveal from './keys/KeyReveal.svelte';
  import SetupSnippets from './keys/SetupSnippets.svelte';

  let error = $state<string | null>(null);
  let busy = $state(false);
  let runCount = $state<number | null>(null);
  let firstRunId = $state<string | null>(null);
  let poll: ReturnType<typeof setInterval> | null = null;

  let session = $derived($cloudSession);
  let canManage = $derived(session?.role === 'owner' || session?.role === 'admin');
  let cloudUrl = $derived(session?.cloud_url ?? '');
  let consoleUrl = $derived(
    session?.console_url ?? `${typeof location === 'undefined' ? '' : location.origin}/flightdeck`
  );

  async function checkRuns() {
    try {
      const page = await cloud.listRuns({ limit: 1 });
      runCount = page.runs.length;
      firstRunId = page.runs[0]?.run_id ?? null;
      // Nothing left to wait for once the first chain lands.
      if (runCount > 0 && poll) {
        clearInterval(poll);
        poll = null;
      }
    } catch {
      // A failed poll is not worth surfacing: the snippet is still correct and
      // the next tick retries. Errors that matter surface on key issue.
    }
  }

  async function issueKey() {
    busy = true;
    try {
      const issued = await cloud.issueKey({ name: 'agent key', role: 'owner' });
      freshApiKey.set(issued.key);
      error = null;
    } catch (e) {
      error = e instanceof Error ? e.message : 'Could not create the key.';
    } finally {
      busy = false;
    }
  }

  onMount(() => {
    if (!session) {
      void goto('/flightdeck/sign-in/');
      return;
    }
    void checkRuns();
    poll = setInterval(checkRuns, 6000);
  });

  onDestroy(() => {
    if (poll) clearInterval(poll);
  });
</script>

<div class="home reveal">
  <header class="ident">
    <div class="who">
      <span class="mark" aria-hidden="true"></span>
      <h1>{session?.workspace.name ?? 'workspace'}</h1>
      <span class="idchip mono">{session?.workspace.workspace_id ?? ''}</span>
    </div>
    <div class="acts">
      <span class="tier mono">{session?.workspace.tier ?? 'free'} tier · you are {session?.role ?? 'signed out'}</span>
      <button class="btn" type="button" onclick={() => goto('/flightdeck/runs')}>Runs →</button>
    </div>
  </header>

  <p class="hook">What will you <b>prove</b> today?</p>

  {#if error}<div class="err">{error}</div>{/if}

  <section class="path lead">
    <div class="ph">
      <span class="pn mono">01</span>
      <div>
        <h2>Instrument an agent you already run</h2>
        <p class="sub">Every call is signed on your machine and mirrored here. Your chain never leaves your disk.</p>
      </div>
    </div>

    <div class="pbody">
      {#if $freshApiKey}
        <KeyReveal apiKey={$freshApiKey} ondismiss={forgetFreshKey} />
      {:else}
        <div class="keyrow">
          <button class="btn primary" type="button" disabled={busy || !canManage} onclick={issueKey}>
            {busy ? 'Issuing…' : 'Generate API key'}
          </button>
          <a class="lnk" href="/flightdeck/keys">See all API keys</a>
          {#if !canManage}<span class="note mono">viewer role cannot issue keys</span>{/if}
        </div>
      {/if}

      <div class="lab mono">Paste this where your agent runs</div>
      <SetupSnippets apiKey={$freshApiKey} {cloudUrl} {consoleUrl} />

      <div class="wait" class:live={runCount !== null && runCount > 0}>
        {#if runCount === null}
          <span class="dot pending"></span><span class="mono">Checking for runs…</span>
        {:else if runCount === 0}
          <span class="dot pending"></span><span class="mono">Waiting for your first run…</span>
          <span class="hint">Run your agent with the key set and it appears here.</span>
        {:else}
          <span class="dot on"></span><span class="mono">First run captured.</span>
          <a class="lnk" href={firstRunId ? `/flightdeck/runs/${firstRunId}` : '/flightdeck/runs'}>Open it →</a>
        {/if}
      </div>
    </div>
  </section>

  <div class="or"><span>OR</span></div>

  <section class="path">
    <div class="ph">
      <span class="pn mono">02</span>
      <div>
        <h2>Watch the 60-second proof first</h2>
        <p class="sub">A poisoned README walks an agent to an SSH key. Signed, detected, explained, entirely on your machine.</p>
      </div>
    </div>
    <div class="pbody"><pre class="cmd mono">air demo</pre></div>
  </section>

  <div class="or"><span>OR</span></div>

  <section class="path">
    <div class="ph">
      <span class="pn mono">03</span>
      <div>
        <h2>Verify a chain you already have</h2>
        <p class="sub">Read any chain and check its evidence offline. No key, no account, no upload.</p>
      </div>
    </div>
    <div class="pbody"><pre class="cmd mono">air trace .air/air-trace-*.log
air health .air/</pre></div>
  </section>
</div>

<style>
  .home { display: flex; flex-direction: column; gap: 14px; max-width: 1040px; }

  .ident { display: flex; align-items: center; justify-content: space-between; gap: 18px; flex-wrap: wrap; }
  .who { display: flex; align-items: center; gap: 12px; min-width: 0; }
  .mark { width: 26px; height: 26px; flex: none; background: var(--air); clip-path: polygon(50% 0, 100% 100%, 0 100%); }
  h1 { font-family: var(--display); font-size: 22px; font-weight: 600; color: var(--ink); }
  .idchip { font-size: 10px; letter-spacing: .04em; color: var(--ink); border: 1px solid var(--hair); padding: 3px 8px; }
  .acts { display: flex; align-items: center; gap: 14px; }
  .tier { font-size: 11px; color: var(--ink); }

  .hook { font-family: var(--display); font-size: 17px; font-weight: 500; color: var(--ink); margin: 2px 0 10px; }
  .hook b { color: var(--air2); font-weight: 700; }

  .path { border: 1px solid var(--hair); background: rgba(255,255,255,.02); }
  .path.lead { border-color: var(--stroke); background: rgba(255,255,255,.035); }
  .ph { display: flex; gap: 14px; padding: 18px 20px; border-bottom: 1px solid var(--hair); }
  .pn { font-size: 11px; color: var(--air2); padding-top: 3px; letter-spacing: .1em; }
  h2 { font-family: var(--display); font-size: 15px; font-weight: 600; color: var(--ink); }
  .sub { font-size: 12px; color: var(--ink); margin-top: 5px; max-width: 74ch; }
  .pbody { padding: 18px 20px; display: flex; flex-direction: column; gap: 14px; }

  .keyrow { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
  .btn.primary { border-color: var(--air); background: rgba(230,57,70,.16); color: var(--ink); font-weight: 600; }
  .btn.primary:disabled { opacity: .55; cursor: default; }
  .lnk { font-family: var(--mono); font-size: 11px; color: var(--blue); text-decoration: none; border-bottom: 1px solid rgba(109,181,255,.4); }
  .note { font-size: 10px; color: var(--ink); }
  .lab { font-size: 10px; letter-spacing: .16em; text-transform: uppercase; color: var(--ink); }

  .cmd { font-size: 12px; color: var(--ink); border: 1px solid var(--hair); background: rgba(0,0,0,.28); padding: 12px 14px; white-space: pre-wrap; }

  .wait { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; padding: 11px 14px; border: 1px solid var(--hair); background: rgba(0,0,0,.22); font-size: 11px; }
  .wait.live { border-color: rgba(72,230,164,.4); background: rgba(72,230,164,.08); }
  .wait .hint { color: var(--ink); font-size: 11px; }
  .dot { width: 7px; height: 7px; border-radius: 50%; flex: none; }
  .dot.pending { background: var(--amber); animation: pulse 1.6s ease-in-out infinite; }
  .dot.on { background: var(--teal); }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .3; } }

  .or { display: flex; align-items: center; gap: 14px; color: var(--ink); }
  .or::before, .or::after { content: ''; height: 1px; background: var(--hair); flex: 1; }
  .or span { font-family: var(--mono); font-size: 10px; letter-spacing: .18em; }

  .err { padding: 10px 14px; border: 1px solid rgba(230,57,70,.5); background: rgba(230,57,70,.12); color: var(--ink); font-size: 12px; }

  @media (max-width: 720px) {
    .ident { flex-direction: column; align-items: flex-start; }
    .acts { width: 100%; justify-content: space-between; }
  }
</style>
