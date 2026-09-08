<script>
  import { goto } from '$app/navigation';
  import AppShell from '$components/AppShell.svelte';
</script>
<svelte:head><title>Project AIR · Why AIR</title></svelte:head>

<AppShell active="why-air" title="why air" scroll>
  <div class="page">

    <section class="hero reveal">
      <div class="eyebrow">What it is · why it matters · how it helps</div>
      <h1>The accountability layer<br>for AI agents.</h1>
      <p class="lead">Your agents act on their own. Project AIR makes every action they take signed, bound to the human who authorized it, and independently verifiable — so you can prove exactly what happened, and stop what shouldn't.</p>
      <div class="cta">
        <button class="btn" onclick={() => goto('/design-partner')}>Become a design partner</button>
        <button class="btn ghost" onclick={() => goto('/platform')}>See how it works</button>
        <span class="chip"><span class="pmt">$</span> pip install projectair</span>
      </div>
    </section>

    <section class="blk">
      <div class="eyebrow">What it is</div>
      <h2>A system of record for autonomous agents.</h2>
      <p class="lead bd">Project AIR sits across the AI agents in your business and runs one continuous loop: it establishes what each agent is allowed to do, watches every action it takes, contains the ones that step out of bounds, and seals the whole record as tamper-evident, cryptographically signed evidence — bound to the person who authorized it and anchored so anyone can verify it independently.</p>
      <div class="g4">
        <div class="card c"><div class="step">Audit</div><h3>Define authority</h3><p>Set what each agent may do, mapped to your compliance frameworks. The baseline is signed.</p></div>
        <div class="card c"><div class="step">Monitor</div><h3>Watch every action</h3><p>16 detectors — OWASP Agentic, LLM, and AIR-native — plus structural verification on every step.</p></div>
        <div class="card c"><div class="step">Protect</div><h3>Contain the bad ones</h3><p>A zero-trust registry halts or contains agents acting outside their authorized scope.</p></div>
        <div class="card c"><div class="step">Prove</div><h3>Seal as evidence</h3><p>Every action signed, chained, and anchored — tamper-evident and independently verifiable.</p></div>
      </div>
      <p class="kick">An auditor, regulator, insurer, or court can verify the record <b>without taking your word for it.</b></p>
    </section>

    <section class="blk">
      <div class="eyebrow">Why it's a good addition</div>
      <h2>The accountability gap is already here.</h2>
      <p class="lead bd">Agents are moving out of experiments and into real workflows — and most teams can't say what their agents actually did. In a 2026 survey, 88% of enterprises had an AI-agent security incident in the prior year, yet only 21% had runtime visibility and a third had no audit trail at all.</p>
      <div class="g2">
        <div class="card c"><h3 class="big">Your existing tools each own one piece.</h3><p>Your identity provider says <i>who</i> the agent is. Your cloud logs <i>what</i> it did. Neither can serve as independent proof — because the platform running your agents can't be the neutral party that certifies what they did. <b>That conflict of interest is the gap Project AIR fills.</b></p></div>
        <div class="card c"><h3 class="big">And the rules are closing in.</h3><p>EU AI Act Article 72 requires tamper-evident logging for high-risk AI, retained for years. NIST is standardizing agent controls. Project AIR is the evidence layer those rules assume you already have — pre-mapped, not retrofitted.</p></div>
      </div>
    </section>

    <section class="blk">
      <div class="eyebrow">How it helps your business</div>
      <h2>Evidence, not assertions.</h2>
      <div class="benefits">
        <div class="bf"><div class="bn">01</div><div><h3>Pass audits faster.</h3><p>Walk into EU AI Act, NIST AI RMF, SOC 2, and HIPAA reviews with signed, verifiable records instead of screenshots and spreadsheets. The evidence is already mapped to the framework.</p></div></div>
        <div class="bf"><div class="bn">02</div><div><h3>Cut liability and win disputes.</h3><p>Self-authenticating records — designed to support self-authentication under Federal Rules of Evidence 902(13)–(14) — hold up when an action is challenged in an investigation, a claim, or a courtroom.</p></div></div>
        <div class="bf"><div class="bn">03</div><div><h3>De-risk insurance.</h3><p>Provable controls and a clean evidence trail are exactly what AI-liability underwriters want. Better terms going in, cleaner claims coming out.</p></div></div>
        <div class="bf"><div class="bn">04</div><div><h3>Contain incidents before they cost you.</h3><p>Detect and halt a misbehaving agent in-line — and have the entire event sealed as evidence the moment it happens, not reconstructed weeks later.</p></div></div>
        <div class="bf"><div class="bn">05</div><div><h3>Deploy agents with confidence.</h3><p>Move faster because you can always prove what your agents did and who authorized it. Accountability stops being the thing that slows your rollout down.</p></div></div>
      </div>
    </section>

    <section class="blk">
      <div class="eyebrow">One incident, end to end</div>
      <h2>From a risky action to a verifiable record.</h2>
      <div class="flow card">
        <div class="st"><div class="n">1</div><span><b>Audit</b> — an agent is authorized to read records, never to export them in bulk. That boundary is signed.</span></div>
        <div class="st"><div class="n">2</div><span><b>Monitor</b> — the agent attempts a bulk export. A detector flags it instantly.</span></div>
        <div class="st"><div class="n">3</div><span><b>Protect</b> — the registry halts the agent and blocks the action before any data leaves.</span></div>
        <div class="st"><div class="n">4</div><span><b>Prove</b> — the authorization, the detection, and the containment are sealed into one signed, independently verifiable record.</span></div>
      </div>
      <p class="kick">Your cloud would have logged it. Your identity tool would name the agent. Only Project AIR hands you one verifiable chain showing what was authorized, what was caught, what was stopped — and who said the agent could act.</p>
    </section>

    <section class="blk">
      <div class="eyebrow">Built on standards</div>
      <h2>Open core. Independently verifiable.</h2>
      <p class="lead bd">The SDK, CLI, signed evidence chain, and all 16 detectors are open source under the Apache License 2.0. The forensic record works offline by default and exports to any downstream system or auditor.</p>
      <div class="trust">
        <span>OWASP Top 10 for Agentic</span>
        <span>EU AI Act Article 72</span>
        <span>NIST AI RMF</span>
        <span>SOC 2</span>
        <span>HL7 / FHIR R4</span>
        <span>Sigstore Rekor</span>
        <span>Apache 2.0 open source</span>
        <span>NVIDIA Inception</span>
      </div>
    </section>

    <section class="blk end">
      <div class="eyebrow">Start the forensic record today</div>
      <h2>Prove what your agents did.</h2>
      <div class="cta">
        <span class="chip"><span class="pmt">$</span> pip install projectair</span>
        <button class="btn" onclick={() => goto('/design-partner')}>Become a design partner</button>
      </div>
    </section>

  </div>
</AppShell>

<style>
  .page{max-width:1000px;margin:0 auto;padding-bottom:36px}
  .hero{padding:26px 0 8px}
  .hero h1{font-size:54px;margin-top:14px}
  .hero .lead{font-size:17px;max-width:62ch;margin-top:18px}
  .cta{display:flex;gap:12px;margin-top:26px;flex-wrap:wrap;align-items:center}
  .blk{padding:42px 0;border-top:1px solid var(--line);margin-top:30px}
  .blk h2{font-size:30px;margin-top:10px}
  .lead.bd{margin-top:14px;font-size:15.5px;max-width:80ch}
  .kick{margin-top:18px;color:var(--soft);font-size:15px;line-height:1.6;max-width:80ch}
  .kick b{color:#fff}
  .g4{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:24px}
  .g2{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:22px}
  .card.c{padding:18px}
  .card .step{font-family:var(--mono);font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:var(--air2);margin-bottom:8px}
  .card.c h3{font-family:var(--ui);font-weight:700;font-size:15px}
  .card.c h3.big{font-size:16.5px;margin-bottom:8px}
  .card.c p{color:var(--soft);font-size:13.5px;line-height:1.6;margin-top:6px}
  .benefits{margin-top:18px}
  .bf{display:flex;gap:16px;padding:16px 0;border-bottom:1px solid var(--line)}
  .bf .bn{font-family:var(--mono);font-size:12px;color:var(--air2);width:26px;flex:none;padding-top:3px}
  .bf h3{font-family:var(--ui);font-weight:700;font-size:15.5px}
  .bf p{color:var(--soft);font-size:13.5px;line-height:1.6;margin-top:4px;max-width:74ch}
  .flow{padding:22px;margin-top:22px}
  .flow .st{display:flex;gap:14px;padding:9px 0;align-items:flex-start}
  .flow .n{font-family:var(--mono);font-size:12px;color:var(--air2);width:22px;flex:none;padding-top:2px}
  .flow .st b{color:#fff}
  .flow .st span{color:var(--soft);font-size:14.5px;line-height:1.5}
  .trust{display:flex;gap:8px;flex-wrap:wrap;margin-top:18px}
  .trust span{font-family:var(--mono);font-size:11px;color:var(--soft);border:1px solid var(--line);padding:6px 11px}
  .end{text-align:center}
  .end h2{font-size:34px}
  .end .cta{justify-content:center}
  @media (max-width:1080px){ .g4{grid-template-columns:1fr 1fr} .g2{grid-template-columns:1fr} .hero h1{font-size:38px} }
</style>
