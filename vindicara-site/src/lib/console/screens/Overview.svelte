<script lang="ts">
  import './overview.css';
  import { goto } from '$app/navigation';

  import { api } from '$lib/console/api/client';
  import type { FindingAction, OverviewData } from '$lib/console/api/types';
  import Globe3D from '$lib/console/components/Globe3D.svelte';
  import StarsField from '$lib/console/components/StarsField.svelte';
  import Drawer from '$lib/console/components/Drawer.svelte';
  import FlightDeckNav from '$lib/console/components/FlightDeckNav.svelte';

  import { operator, signedIn } from '$lib/console/stores/operator';
  import { mode, selectedScenarioId } from '$lib/console/stores/mode';
  import {
    actionLabel,
    actionTone,
    activeNodeCount,
    atcAgents,
    criticalIncidentCount,
    demoAtcIntent,
    detectorCount,
    fleetAgentCount,
    fleetCryptoFromProof,
    incidentsCryptoFromProof,
    timelineFromEnforcement,
    type AtcAgent
  } from './overview-data';
  import { flashOverview, overviewToast } from './overview-toast';
  import { openClockOut, recordReview } from '$lib/console/stores/sessionlog';
  import { lockSession } from '$lib/console/stores/session';

  let askQuery = $state('');
  let drawerOpen = $state(false);
  let overview = $state<OverviewData | null>(null);
  let loading = $state(true);
  let loadError = $state('');

  let employeePhotoSrc = $state<string | null>(null);
  let photoInput = $state<HTMLInputElement | null>(null);

  // Recent Forensic Activity lens selector — 4 chooser buttons.
  const FORENSIC_LENSES = ['Department', 'Service line', 'Agent role', 'Data Sensitivity'];
  let forensicLens = $state('Department');

  // Monitor scope selector — Agent / Cohort / Fleet.
  const MONITOR_SCOPES = ['Agent', 'Cohort', 'Fleet'];
  let monitorScope = $state('Agent');

  async function refresh() {
    loading = true;
    loadError = '';
    try {
      overview = await api.getOverview();
    } catch (e) {
      overview = null;
      loadError = e instanceof Error ? e.message : 'request failed';
    } finally {
      loading = false;
    }
  }

  $effect(() => {
    $mode;
    refresh();
  });

  const criticalAgents = $derived(atcAgents($mode, overview));
  const timelineEvents = $derived(overview ? timelineFromEnforcement(overview.enforcement) : []);
  const fleetCrypto = $derived(overview ? fleetCryptoFromProof(overview.proof) : []);
  const incidentsCrypto = $derived(overview ? incidentsCryptoFromProof(overview.proof) : []);

  const employeeProfile = $derived({
    photoSrc: employeePhotoSrc,
    name: $signedIn ? $operator.name : (overview?.onDuty?.name ?? 'John Smith'),
    position: $signedIn ? $operator.role : (overview?.onDuty?.position ?? 'Department Director'),
    department: $signedIn ? $operator.organization : (overview?.onDuty?.department ?? 'Emergency'),
    employeeNumber: overview?.onDuty?.employeeNumber ?? 'EMP-0047'
  });

  function openAtc(agent: AtcAgent) {
    if (agent.scenarioId) {
      selectedScenarioId.set(agent.scenarioId);
      recordReview(agent.scenarioId, agent.behavior);
    }
    goto('/flightdeck/incidents');
  }

  async function runAtcAction(agent: AtcAgent, intent: FindingAction['intent']) {
    const findingId = agent.findingId ?? `demo-${agent.scenarioId ?? agent.name}`;
    try {
      await api.actOnFinding(findingId, intent);
      if (agent.scenarioId) {
        selectedScenarioId.set(agent.scenarioId);
        recordReview(agent.scenarioId, agent.behavior);
      }
      flashOverview(`${actionLabel(intent)} applied · ${agent.name}`);
      await refresh();
    } catch (e) {
      flashOverview(e instanceof Error ? e.message : 'Action failed', 'warn');
    }
  }

  function askAir() {
    const q = askQuery.trim();
    if (!q) {
      flashOverview('Type a question about an agent action or compliance record', 'info');
      return;
    }
    flashOverview('Routing query to forensic search…', 'info');
    goto(`/report?q=${encodeURIComponent(q)}`);
  }

  function onAskKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter') {
      e.preventDefault();
      askAir();
    }
  }

  function employeeReport() {
    flashOverview('Opening session report for department head', 'info');
    goto('/flightdeck/report');
  }

  function employeeSignOff() {
    flashOverview('Clocking out · filing signed session report', 'info');
    openClockOut();
  }

  function employeeBreak() {
    flashOverview('Break started · session locked until re-authorize', 'warn');
    lockSession();
    void goto('/flightdeck/sign-in/');
  }

  function openTimelineEvent(title: string) {
    flashOverview('Opening signed forensic record', 'info');
    goto('/flightdeck/report');
  }

  function openCryptoCard(name: string) {
    if (name === 'Sigstore' || name === 'RFC3161') {
      goto('/flightdeck/report');
      return;
    }
    goto('/flightdeck/readiness');
  }

  function openPillar(pillar: 'monitor' | 'protect' | 'prove') {
    if (pillar === 'monitor') goto('/flightdeck/readiness');
    else if (pillar === 'protect') goto('/flightdeck/incidents');
    else goto('/flightdeck/report');
  }

  function openGlobe() {
    flashOverview('Opening global agent network map', 'info');
    goto('/flightdeck/rules');
  }

  function openTimelineSection() {
    flashOverview('Opening forensic activity log', 'info');
    goto('/flightdeck/report');
  }

  function openAtcSection() {
    flashOverview('Opening live traffic control queue', 'info');
    goto('/flightdeck/incidents');
  }

  function openDutyStatus() {
    flashOverview(`${employeeProfile.name} · on duty · ${employeeProfile.department}`, 'info');
  }

  function openEmployeePhoto() {
    photoInput?.click();
  }

  function onPhotoSelected(e: Event) {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      employeePhotoSrc = typeof reader.result === 'string' ? reader.result : null;
      flashOverview('Employee photo updated for this session', 'ok');
    };
    reader.readAsDataURL(file);
  }
</script>

<div class="fd">
  <StarsField />
  <FlightDeckNav onMenuClick={() => (drawerOpen = true)} />

  <div class="fd-wrap fd-ask-wrap">
    <div class="fd-ask">
      <input bind:value={askQuery} placeholder="Ask about any agent action, causal chain, or compliance record..." onkeydown={onAskKeydown} />
      <button class="fd-ask-btn" type="button" onclick={askAir}>Ask <span class="fd-ask-air">AIR</span></button>
    </div>
  </div>

  <div class="fd-wrap fd-main">
    {#if loading && !overview}
      <div class="fd-loading">Loading console…</div>
    {:else if loadError}
      <div class="fd-loading">
        Couldn't load overview. {loadError}
        <div>
          <button class="fd-retry" type="button" onclick={() => refresh()}>Retry</button>
        </div>
      </div>
    {:else if overview}
    <div class="fd-grid">
      <section class="fd-col-fleet">
        <div class="fd-stack">
          <article class="fd-card fd-card--summary fd-card--click" role="button" tabindex="0" onclick={() => goto('/flightdeck/rules')} onkeydown={(e) => e.key === 'Enter' && goto('/flightdeck/rules')}>
            <div class="fd-summary-top">
              <span class="fd-summary-live"><span class="fd-summary-dot" aria-hidden="true"></span> Live fleet</span>
              <span class="fd-glow fd-glow--emerald">Active</span>
            </div>
            <div class="fd-summary-count">{fleetAgentCount(overview)}</div>
            <div class="fd-summary-label">agents</div>
          </article>

          {#each fleetCrypto as c}
            <article
              class="fd-card fd-card--crypto fd-card--crypto-{c.tone} fd-card--click"
              role="button"
              tabindex="0"
              onclick={() => openCryptoCard(c.name)}
              onkeydown={(e) => e.key === 'Enter' && openCryptoCard(c.name)}
            >
              <div class="fd-crypto-top">
                <span class="fd-crypto-name">{c.name}</span>
                <span class="fd-glow fd-glow--{c.tone}">{c.status}</span>
              </div>
              <div class="fd-crypto-metric">{c.metric}</div>
              <div class="fd-crypto-label">{c.label}</div>
            </article>
          {/each}
        </div>
      </section>

      <section class="fd-col-globe">
        <button class="fd-globe-label fd-globe-label--btn" type="button" onclick={openGlobe}>
          <span class="dot">•</span> Global Agent Network · <span class="live">Live</span> · {activeNodeCount(overview)} Active Nodes
        </button>
        <button class="fd-globe-hit" type="button" aria-label="Open agent network" onclick={openGlobe}>
          <Globe3D />
        </button>
        <div class="fd-lens-group">
          <div class="fd-faf-lenses" role="group" aria-label="View activity by">
            {#each FORENSIC_LENSES as lens}
              <button type="button" class="fd-faf-lens" class:on={forensicLens === lens} aria-pressed={forensicLens === lens} onclick={() => (forensicLens = lens)}>{lens}</button>
            {/each}
          </div>
          <div class="fd-faf-lenses" role="group" aria-label="Scope">
            {#each MONITOR_SCOPES as s}
              <button type="button" class="fd-faf-lens" class:on={monitorScope === s} aria-pressed={monitorScope === s} onclick={() => (monitorScope = s)}>{s}</button>
            {/each}
          </div>
        </div>
      </section>

      <section class="fd-col-incidents">
        <div class="fd-stack">
          <article
            class="fd-card fd-card--summary fd-card--summary-incidents fd-card--click"
            role="button"
            tabindex="0"
            onclick={() => goto('/flightdeck/incidents')}
            onkeydown={(e) => e.key === 'Enter' && goto('/flightdeck/incidents')}
          >
            <div class="fd-summary-top">
              <span class="fd-summary-live"><span class="fd-summary-dot" aria-hidden="true"></span> Prioritized</span>
              <span class="fd-glow fd-glow--critical">Critical</span>
            </div>
            <div class="fd-summary-count">{criticalIncidentCount(overview)}</div>
            <div class="fd-summary-label">critical</div>
          </article>

          {#each incidentsCrypto as c}
            <article
              class="fd-card fd-card--crypto fd-card--crypto-{c.tone} fd-card--click"
              role="button"
              tabindex="0"
              onclick={() => openCryptoCard(c.name)}
              onkeydown={(e) => e.key === 'Enter' && openCryptoCard(c.name)}
            >
              <div class="fd-crypto-top">
                <span class="fd-crypto-name">{c.name}</span>
                <span class="fd-glow fd-glow--{c.tone}">{c.status}</span>
              </div>
              <div class="fd-crypto-metric">{c.metric}</div>
              <div class="fd-crypto-label">{c.label}</div>
            </article>
          {/each}
        </div>
      </section>
    </div>

    <section class="fd-card fd-timeline">
      <button class="fd-h2-sm fd-h2-sm--btn" type="button" onclick={openTimelineSection}>
        Recent Forensic Activity · <em>Cryptographically Signed</em>
      </button>
      <div class="fd-tl-wrap">
        <div class="fd-tl-line"></div>
        <div class="fd-tl-grid">
          {#each [...timelineEvents, ...timelineEvents] as e, i}
            <button class="fd-tl-item" type="button" aria-hidden={i >= timelineEvents.length} tabindex={i >= timelineEvents.length ? -1 : 0} onclick={() => openTimelineEvent(e.title)}>
              <i class="fd-tl-dot fd-tl-dot--{e.status === 'pending' ? 'orange' : 'cyan'}"></i>
              <div class="fd-tl-row">
                <span class="fd-tl-time fd-mono">{e.t}</span>
                <span class="fd-tl-sep"> - </span>
                <span class="fd-tl-title">{e.title}</span>
              </div>
              <div class="fd-tl-actor">{e.actor}</div>
              <span class="fd-tl-state fd-tl-state--{e.status}">
                {e.status === 'ok' ? '✓ Verified' : 'Pending Review'}
              </span>
            </button>
          {/each}
        </div>
      </div>
    </section>

    <div class="fd-bottom-panels">
      <article class="fd-card fd-critical-box">
        <button class="fd-h2-sm fd-h2-sm--btn" type="button" onclick={openAtcSection}>AIR TRAFFIC CONTROL · <em>LIVE</em></button>
        <div class="fd-critical-inner">
          {#each criticalAgents as agent}
            <div class="fd-critical-entry">
              <button class="fd-critical-line" type="button" onclick={() => openAtc(agent)}>
                <span class="fd-critical-line-name">{agent.name}</span>
                <span class="fd-critical-line-behavior">{agent.behavior}</span>
                <span class="fd-glow fd-glow--critical">Critical</span>
              </button>
              <div class="fd-critical-actions">
                {#if agent.actions?.length}
                  {#each agent.actions.slice(0, 3) as action}
                    <button
                      class="fd-critical-action fd-critical-action--{actionTone(action.intent)}"
                      type="button"
                      onclick={() => runAtcAction(agent, action.intent)}
                    >
                      {action.label || actionLabel(action.intent)}
                    </button>
                  {/each}
                {:else}
                  <button class="fd-critical-action fd-critical-action--revoke" type="button" onclick={() => runAtcAction(agent, demoAtcIntent('revoke'))}>Revoke</button>
                  <button class="fd-critical-action fd-critical-action--quarantine" type="button" onclick={() => runAtcAction(agent, demoAtcIntent('quarantine'))}>Quarantine</button>
                  <button class="fd-critical-action fd-critical-action--renew" type="button" onclick={() => runAtcAction(agent, demoAtcIntent('renew'))}>Renew</button>
                {/if}
              </div>
            </div>
          {/each}
        </div>
      </article>

      <article
        class="fd-card fd-verify-box fd-card--click"
        role="button"
        tabindex="0"
        onclick={() => goto('/flightdeck/readiness')}
        onkeydown={(e) => e.key === 'Enter' && goto('/flightdeck/readiness')}
      >
        <span class="fd-h2-sm fd-verify-monitor">Monitor</span>
        <div class="fd-verify-content">
          <span class="fd-summary-live"><span class="fd-summary-dot" aria-hidden="true"></span> Deterministic floor</span>
          <div class="fd-verify-count">{detectorCount(overview)}</div>
          <div class="fd-verify-label">detectors &amp; structural verification</div>
        </div>
      </article>

      <div class="fd-employee-col">
        <article class="fd-card fd-employee-box">
          <button class="fd-h2-sm fd-employee-duty fd-employee-duty--btn" type="button" onclick={openDutyStatus}>On duty</button>
          <input bind:this={photoInput} class="fd-photo-input" type="file" accept="image/*" hidden onchange={onPhotoSelected} />
          <div class="fd-employee-inner">
            <button class="fd-employee-frame fd-employee-frame--btn" type="button" aria-label="Update employee photo" onclick={openEmployeePhoto}>
              {#if employeeProfile.photoSrc}
                <img class="fd-employee-photo" src={employeeProfile.photoSrc} alt="" />
              {:else}
                <div class="fd-employee-photo fd-employee-photo--empty" aria-hidden="true">
                  <svg viewBox="0 0 64 64" fill="none">
                    <circle cx="32" cy="24" r="11" stroke="currentColor" stroke-width="1.5" />
                    <path d="M14 54c2.5-12 10-18 18-18s15.5 6 18 18" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
                  </svg>
                </div>
              {/if}
            </button>
            <dl class="fd-employee-details">
              <div class="fd-employee-row">
                <dt>Name</dt>
                <dd>{employeeProfile.name}</dd>
              </div>
              <div class="fd-employee-row">
                <dt>Position</dt>
                <dd>{employeeProfile.position}</dd>
              </div>
              <div class="fd-employee-row">
                <dt>Department</dt>
                <dd>{employeeProfile.department}</dd>
              </div>
              <div class="fd-employee-row">
                <dt>Employee number</dt>
                <dd class="fd-mono">{employeeProfile.employeeNumber}</dd>
              </div>
            </dl>
          </div>
          <div class="fd-employee-actions">
            <button class="fd-employee-action fd-employee-action--report" type="button" onclick={employeeReport}>Report</button>
            <button class="fd-employee-action fd-employee-action--signoff" type="button" onclick={employeeSignOff}>Sign off</button>
            <button class="fd-employee-action fd-employee-action--break" type="button" onclick={employeeBreak}>Break</button>
          </div>
        </article>

        <div class="fd-pillars-tag" aria-label="Monitor, Protect, Prove">
          <button class="fd-pillar" type="button" onclick={() => openPillar('monitor')}>Monitor</button>
          <span class="fd-pillars-sep" aria-hidden="true">|</span>
          <button class="fd-pillar" type="button" onclick={() => openPillar('protect')}>Protect</button>
          <span class="fd-pillars-sep" aria-hidden="true">|</span>
          <button class="fd-pillar" type="button" onclick={() => openPillar('prove')}>Prove</button>
        </div>
      </div>
    </div>
    {/if}
  </div>

  <Drawer open={drawerOpen} onclose={() => (drawerOpen = false)} />

  {#if $overviewToast}
    <div class="fd-toast fd-toast--{$overviewToast.tone ?? 'ok'}" role="status">
      {$overviewToast.message}
    </div>
  {/if}
</div>