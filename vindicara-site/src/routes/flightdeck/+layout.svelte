<script lang="ts">
  import '$lib/console/console.css';
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { get } from 'svelte/store';
  import { page } from '$app/stores';
  import Rail from '$lib/console/components/Rail.svelte';
  import Drawer from '$lib/console/components/Drawer.svelte';
  import FlightDeckNav from '$lib/console/components/FlightDeckNav.svelte';
  import ClockOut from '$lib/console/components/forensics/ClockOut.svelte';
  import { sessionToken } from '$lib/console/stores/session';
  import { mode } from '$lib/console/stores/mode';

  let { children } = $props();
  let drawerOpen = $state(false);

  // Auth-gate: in LIVE mode with no token, send the operator to Auth0 first.
  // Demo mode never redirects (public showcase). Skip on /flightdeck/auth/*.
  onMount(() => {
    const url = get(page).url;
    const onAuthRoute =
      url.pathname.startsWith('/flightdeck/auth/') || url.pathname.startsWith('/flightdeck/sign-in');
    const isDemo = url.searchParams.has('demo');
    // ?demo = the explicit public sales showcase (no login). Everyone else,
    // including Free, MUST sign in first: that is the whole point of the Free
    // UI (capture the user, then nudge upgrades). A signed-in operator runs Live.
    if (isDemo) {
      mode.set('demo');
    } else if (get(sessionToken)) {
      mode.set('live');
    }
    if (!onAuthRoute && !isDemo && !get(sessionToken)) {
      void goto('/flightdeck/sign-in/');
    }
  });

  // Full-bleed pages that bring their own nav (no Rail): the transient Auth0
  // callback/logout pages and sign-in.
  //
  // /flightdeck used to be listed here as "the Overview landing", but the route
  // renders Inbox, which has no nav of its own. That made the landing screen a
  // dead end: no way to reach Keys, Runs, or anything else without editing the
  // URL. It now gets the standard shell like every other screen.
  const bareShellPaths: string[] = [];
  let overviewShell = $derived(
    bareShellPaths.includes($page.url.pathname) || $page.url.pathname.startsWith('/flightdeck/auth/') || $page.url.pathname.startsWith('/flightdeck/sign-in/')
  );
</script>

{#if overviewShell}
  {#key $mode}
    {@render children()}
  {/key}
  <ClockOut />
{:else}
<div class="aurora"><i></i><i></i><i></i></div>
<div class="grain"></div>

<div class="console-page">
  <FlightDeckNav onMenuClick={() => (drawerOpen = true)} />

  <div class="app">
    <Rail />

    <main class="work">
      {#key $mode}
        {@render children()}
      {/key}

      <footer class="tagfoot">
        <span class="w">Monitor</span>
        <span class="bar">|</span>
        <span class="w">Protect</span>
        <span class="bar">|</span>
        <span class="w">Prove</span>
      </footer>
    </main>
  </div>
</div>

<Drawer open={drawerOpen} onclose={() => (drawerOpen = false)} />
<ClockOut />
{/if}

<style>
  .console-page { position: relative; z-index: 2; min-height: 100vh; }
  .app { display: grid; grid-template-columns: 320px 1fr; gap: 18px; align-items: start; min-height: calc(100vh - 56px); padding: 18px 22px 22px; }
  .work { display: flex; flex-direction: column; gap: 24px; min-width: 0; min-height: calc(100vh - 96px); }
  .tagfoot { margin-top: auto; padding: 26px 0 6px; display: flex; align-items: center; justify-content: center; gap: 16px; border-top: 1px solid var(--hair); }
  .tagfoot .w { font-family: var(--mono); font-size: 11px; letter-spacing: .34em; text-transform: uppercase; color: var(--muted); }
  .tagfoot .bar { color: var(--air); font-weight: 700; opacity: .55; }
  @media (max-width: 980px) { .app { grid-template-columns: 1fr; } }
</style>
