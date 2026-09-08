<script lang="ts">
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { lockSession } from '$lib/console/stores/session';

  let { open = false, onclose } = $props();

  const groups = [
    { title: 'Workspace', items: [
      { label: 'Runs', to: '/flightdeck/runs', tag: 'live' },
      { label: 'Keys and setup', to: '/flightdeck/keys' }
    ]},
    { title: 'Console', items: [
      { label: 'Overview', to: '/flightdeck' },
      { label: 'Agents', to: '/flightdeck/rules' },
      { label: 'Incidents', to: '/flightdeck/incidents', tag: '10' },
      { label: 'Forensics', to: '/flightdeck/report', tag: 'PDF' },
      { label: 'Approvals', to: '/flightdeck/incidents', tag: '2' },
      { label: 'Compliance', to: '/flightdeck/readiness' }
    ]},
    { title: 'Department', items: [
      { label: 'Active delegations', to: '/flightdeck', tag: 'dept' },
      { label: 'Step-up queue', to: '/flightdeck/incidents', tag: '2' },
      { label: 'Handoff lineage', to: '/flightdeck/incidents' }
    ]},
    { title: 'Policy & proof', items: [
      { label: 'Rules', to: '/flightdeck/rules', tag: '.md' },
      { label: 'Tamper-evident report', to: '/flightdeck/report', tag: 'PDF' },
      { label: 'Evidence packs', to: '/flightdeck/incidents', tag: '12' }
    ]},
    { title: 'Plugins', items: [
      { label: 'All plugins', to: '/flightdeck/plugins', tag: '9' },
      { label: 'SIEM export', to: '/flightdeck/plugins', tag: '5' },
      { label: 'Insurance API', to: '/flightdeck/insurance', tag: 'ENT' }
    ]},
    { title: 'Account', items: [
      { label: 'Settings', to: '/flightdeck/settings', tag: 'ENT' }
    ]}
  ];

  function nav(to: string) { goto(to); onclose?.(); }
</script>

<div class="scrim {open ? 'on' : ''}" onclick={() => onclose?.()} role="presentation"></div>
<nav class="drawer {open ? 'on' : ''}" aria-hidden={!open}>
  <div class="dhead"><span class="dot"></span><span class="logo">Project&nbsp;<span class="air">AIR</span></span><button class="x" onclick={() => onclose?.()}>✕</button></div>

  {#each groups as g}
    <div class="dgrp">{g.title}</div>
    {#each g.items as it}
      <button class="ditem {$page.url.pathname === it.to ? 'on' : ''}" onclick={() => nav(it.to)}>
        <span class="di"></span>{it.label}{#if it.tag}<span class="tag">{it.tag}</span>{/if}
      </button>
    {/each}
  {/each}

  <div class="dgrp"> </div>
  <button class="ditem lk" onclick={() => { lockSession(); onclose?.(); goto('/flightdeck/sign-in/'); }}><span class="di"></span>Lock session</button>
</nav>

<style>
  .scrim { position: fixed; inset: 0; background: rgba(0,0,0,.5); backdrop-filter: blur(2px); z-index: 60; opacity: 0; pointer-events: none; transition: .25s; }
  .scrim.on { opacity: 1; pointer-events: auto; }
  .drawer { position: fixed; top: 0; left: 0; bottom: 0; width: 300px; z-index: 61; transform: translateX(-110%); transition: transform .28s cubic-bezier(.2,.7,.2,1);
    border-right: 1px solid var(--stroke); background: linear-gradient(160deg, rgba(20,22,30,.97), rgba(8,9,14,.98)); backdrop-filter: blur(30px); display: flex; flex-direction: column; overflow: auto; }
  .drawer.on { transform: none; }
  .dhead { padding: 20px; display: flex; align-items: center; gap: 10px; border-bottom: 1px solid var(--hair); }
  .dot { width: 11px; height: 11px; border-radius: 2px; background: var(--air); box-shadow: 0 0 14px var(--air); }
  .logo {
    font-family: var(--display);
    font-weight: 700;
    font-size: 18px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
  }
  .logo :global(.air) { color: var(--air); font-weight: 700; }
  .x {
    margin-left: auto;
    color: var(--faint);
    cursor: pointer;
    font-size: 16px;
    background: none;
    border: 0;
    font-family: var(--display);
  }
  .dgrp {
    padding: 15px 16px 5px;
    font-family: var(--display);
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--faint);
  }
  .ditem {
    width: 100%;
    text-align: left;
    background: none;
    border: 0;
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 11px 18px;
    cursor: pointer;
    color: var(--muted);
    font-family: var(--display);
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    border-left: 2px solid transparent;
    transition: .13s;
  }
  .ditem:hover { background: rgba(255,255,255,.04); color: var(--ink); }
  .ditem.on { color: var(--ink); border-left-color: var(--air); background: rgba(230,57,70,.08); }
  .di { width: 7px; height: 7px; border-radius: 50%; background: var(--faint); flex: 0 0 7px; }
  .ditem.on .di { background: var(--air); box-shadow: 0 0 8px var(--air); }
  .ditem.lk { color: #ffc4a3; }
  .ditem.lk .di { background: var(--orange); }
  .tag {
    margin-left: auto;
    font-family: var(--display);
    font-size: 8px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--faint);
    border: 1px solid var(--hair);
    padding: 2px 6px;
  }
</style>
