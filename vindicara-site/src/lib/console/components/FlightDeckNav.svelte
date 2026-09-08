<script lang="ts">
  import './flightdeck-nav.css';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { mode, type Mode } from '$lib/console/stores/mode';
  import { flashOverview } from '$lib/console/screens/overview-toast';

  let { onMenuClick }: { onMenuClick?: () => void } = $props();

  const path = $derived($page.url.pathname as string);

  function setMode(next: Mode) {
    mode.set(next);
  }

  function openApprovals() {
    flashOverview('Opening step-up approval queue', 'info');
    goto('/flightdeck/incidents');
  }
</script>

<header class="fd-nav">
  <div class="fd-nav-inner">
    <button class="fd-brand" type="button" onclick={() => goto('/flightdeck')}>
      <span class="fd-brand-mark" aria-hidden="true"></span>
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M12 2 L22 21 L12 16 L2 21 Z" fill="#ffd5d9" />
        <path d="M12 2 L22 21 L12 16 Z" fill="#e63946" />
      </svg>
      <span class="fd-brand-word">AIR</span>
    </button>

    <nav class="fd-links">
      <button class="fd-link" class:on={path === '/flightdeck'} type="button" onclick={() => goto('/flightdeck')}>Overview</button>
      <button class="fd-link" class:on={path.startsWith('/flightdeck/runs')} type="button" onclick={() => goto('/flightdeck/runs')}>Runs</button>
      <button class="fd-link" class:on={path === '/flightdeck/keys'} type="button" onclick={() => goto('/flightdeck/keys')}>Keys</button>
      <button class="fd-link" class:on={path === '/flightdeck/rules'} type="button" onclick={() => goto('/flightdeck/rules')}>Agents</button>
      <button class="fd-link" class:on={path === '/flightdeck/incidents'} type="button" onclick={() => goto('/flightdeck/incidents')}>Incidents</button>
      <button class="fd-link" class:on={path === '/flightdeck/report'} type="button" onclick={() => goto('/flightdeck/report')}>Forensics</button>
      <button class="fd-link" type="button" onclick={openApprovals}>Approvals</button>
      <button class="fd-link" class:on={path === '/flightdeck/readiness'} type="button" onclick={() => goto('/flightdeck/readiness')}>Compliance</button>
    </nav>

    <div class="fd-actions">
      <div class="fd-mode-toggle" role="group" aria-label="Data mode">
        <button
          class="fd-mode-seg"
          class:on={$mode === 'demo'}
          aria-pressed={$mode === 'demo'}
          type="button"
          onclick={() => setMode('demo')}
        >
          Demo
        </button>
        <button
          class="fd-mode-seg fd-mode-seg--live"
          class:on={$mode === 'live'}
          aria-pressed={$mode === 'live'}
          type="button"
          onclick={() => setMode('live')}
        >
          Live
        </button>
      </div>
      <button class="fd-burger" type="button" aria-label="Menu" onclick={() => onMenuClick?.()}>
        <span></span><span></span><span></span>
      </button>
    </div>
  </div>
</header>