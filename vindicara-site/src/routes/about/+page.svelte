<script>
  import AppShell from '$components/AppShell.svelte';
  const pillars = [
    { n: 'Policy Engine', d: 'Real-time detection of agent policy violations.' },
    { n: 'MCP Scanner', d: 'Finds vulnerable tool and connector configurations before they are exploited.' },
    { n: 'Agent IAM', d: 'Scopes, suspends, and revokes an agent in one call.' },
    { n: 'Behavioral Drift', d: 'Catches agents straying from their established baseline.' },
    { n: 'Compliance-as-Code', d: 'Turns the runtime log into audit-ready evidence inputs.' }
  ];
</script>
<svelte:head><title>Vindicara · About</title></svelte:head>

<AppShell active="about" title="about" scroll={true}>
  <div class="prose">
    <div class="eyebrow">About Vindicara</div>
    <h1>We build the system of record for human accountability over AI agents.</h1>

    <p class="big">Vindicara started as a runtime security engine. It became something more focused: the company that makes the record proving who authorized an AI agent, and what that agent did.</p>

    <h2>How Vindicara started</h2>
    <p>Vindicara began as a five-pillar runtime security platform for AI agents, an engine that watched agents in production, caught policy violations, scanned their tools, contained them when they misbehaved, and turned the runtime log into compliance evidence.</p>

    <div class="pillars">
      {#each pillars as p, i}
        <div class="pill"><div class="pn"><span class="pi">{i+1}</span>{p.n}</div><div class="pd">{p.d}</div></div>
      {/each}
    </div>

    <h2>The transition to Project AIR</h2>
    <p>Building that engine surfaced a sharper truth. Prevention is crowded and probabilistic, and agents still go off-script in production. The question customers could not answer was not "can you stop everything," it was "when something happens, can you prove what the agent did and who authorized it." That question had no good answer on the market.</p>
    <p>So the five pillars became the substrate, and the answer to that question became the flagship: <b>Project AIR</b>. The runtime engine still runs underneath, but the headline is the evidence and the enforcement that sit on top: monitor every action, enforce a deterministic floor an uncovered agent cannot cross, and prove the result with a signed, anchored, court-supportable record. No agent is autonomous. Every action traces back to a named human, and Project AIR is the record of that authority.</p>

    <h2>What we believe</h2>
    <div class="prins">
      <div class="pr"><div class="pt">Evidence over assertion</div><p>We ship proof a buyer can verify, not claims they have to trust.</p></div>
      <div class="pr"><div class="pt">A floor that cannot be talked out of it</div><p>Enforcement runs as fixed logic, not a model that can be jailbroken.</p></div>
      <div class="pr"><div class="pt">Honest disclosure</div><p>We state what Project AIR does not do as plainly as what it does.</p></div>
    </div>

    <div class="dogfood">
      <div class="dh">We run on our own infrastructure</div>
      <p>Every request to this site is recorded as a signed AgDR chain using the same airsdk library you install from PyPI, anchored to public Sigstore Rekor every 60 seconds and published as redacted JSONL. The trust contract is identical to what we sell: signed at the moment of action, not reconstructed from logs.</p>
    </div>

    <div class="backed">
      <div class="bh">Backed by</div>
      <div class="badges">
        <a href="https://www.nvidia.com/en-us/startups/" target="_blank" rel="noopener" aria-label="NVIDIA Inception Program">
          <img src="/nvidia-inception-program-badge.svg" alt="NVIDIA Inception Program member" />
        </a>
        <a class="e2b" href="https://e2b.dev/startups" target="_blank" rel="noopener" aria-label="E2B for Startups">
          <img src="/e2b-startups.svg" alt="Sponsored by E2B for Startups" />
        </a>
      </div>
    </div>
  </div>
</AppShell>

<style>
  .prose h1{font-size:38px;margin:14px 0 0;max-width:18ch}
  .big{font-size:17px;color:var(--white);line-height:1.6;margin:20px 0 6px;font-family:var(--display)}
  .pillars{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin:16px 0 8px}
  .pill{border:1px solid var(--line);background:var(--navy1);padding:14px}
  .pn{font-size:12.5px;font-weight:700;display:flex;align-items:center;gap:8px}
  .pi{font-family:var(--mono);font-size:10px;color:var(--air2);border:1px solid rgba(230,57,70,.3);width:18px;height:18px;display:grid;place-items:center}
  .pd{font-size:11px;color:var(--soft);margin-top:8px;line-height:1.45}
  .prins{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:8px 0}
  .prins .pr{border-top:2px solid var(--air);padding-top:12px}
  .prins .pt{font-family:var(--display);font-size:15px;font-weight:600} .prins p{font-size:12px;color:var(--soft);margin-top:5px;line-height:1.45}
  .dogfood{background:#0a1326;border:1px solid var(--line);padding:18px 20px;margin-top:20px}
  .dogfood .dh{font-family:var(--mono);font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--air2);margin-bottom:8px}
  .dogfood p{font-size:13px;color:var(--soft);line-height:1.6}
  .backed{margin-top:28px;padding-top:20px;border-top:1px solid var(--line)}
  .backed .bh{font-family:var(--mono);font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:var(--white);margin-bottom:12px}
  .badges{display:flex;align-items:center;gap:24px;flex-wrap:wrap}
  .backed a{display:inline-block}
  .backed img{height:64px;width:auto;display:block}
  .backed .e2b img{height:30px}
  @media (max-width:1080px){ .pillars{grid-template-columns:1fr 1fr} .prins{grid-template-columns:1fr} }
</style>
