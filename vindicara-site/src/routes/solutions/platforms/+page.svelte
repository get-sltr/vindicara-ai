<script>
  // @ts-nocheck
  import { onMount } from 'svelte';
  import SiteHeader from '$lib/components/SiteHeader.svelte';
  import { setupReveal } from '$lib/reveal.js';
  import '$lib/styles/industry.css';
  onMount(setupReveal);
</script>

<svelte:head>
  <title>AI agent platforms · Project AIR — provable accountability you can ship to your users</title>
  <meta name="description" content="Embed Project AIR in your agent platform and hand every customer signed, anchored proof of what their agents did and why. Execution and intent observability, mapped to EU AI Act, NIST AI RMF, ISO 42001, SOC 2 and GDPR — as your feature." />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
</svelte:head>

<div class="ind">
  <div class="dotfield"></div>
  <SiteHeader />

  <!-- hero -->
  <section class="hero">
    <div class="hl">
      <div class="eyebrow">Solutions / AI agent platforms</div>
      <h1>You run agents for thousands of customers.<br><em>Give each of them provable accountability.</em></h1>
      <p class="sub">Embed <span class="air">AIR</span> in your platform and give every customer signed, anchored proof of what their agents did, <b>and why</b>. Shipped as your feature, under your brand.</p>
      <div class="tagrow">
        <span>EU AI Act</span><span>NIST AI RMF</span><span>ISO 42001</span><span>SOC 2</span><span>GDPR</span>
      </div>
      <div class="ctarow">
        <a class="btn-red" href="/contact">Talk about embedding</a>
        <a class="bookd" href="#evidence">See the evidence ↓</a>
      </div>
      <div class="trustline">White-label · multi-tenant · your customers verify it themselves</div>
    </div>

    <div class="hfx">
      <div class="hglow"></div>
      <div class="capsule">
        <div class="cap-h"><span class="d"></span> White-label capsule · live</div>
        <div class="cap-row"><span class="k">Tenant</span><span class="v">acme-corp</span></div>
        <div class="cap-row"><span class="k">Agent</span><span class="v">support-resolver-12</span></div>
        <div class="cap-row"><span class="k">Powered by</span><span class="v">AIR · embedded</span></div>
        <div class="cap-row res"><span class="k">Action</span><span class="v">refund issued · in policy</span></div>
        <div class="cap-row halt"><span class="k">PII export</span><span class="v">blocked · SV-EXFIL</span></div>
        <div class="cap-sign">BLAKE3 · Ed25519 · per-tenant chain · anchored Rekor</div>
        <div class="cap-verify">✓ your customer verifies — zero calls to you</div>
      </div>
    </div>
  </section>

  <!-- 01 the stakes -->
  <div class="breaker rv"><span class="bn">01</span><span class="bk">The stakes</span></div>
  <div class="scene rv">
    <div class="ts">last 30 days · platform: your-agents-cloud</div>
    <div class="big">Your platform ran 4.2M agent actions for your customers last month.</div>
    <div class="sub">When their auditor or regulator asks what an agent did, and <b>why</b>, that's your platform's problem, not theirs. Most platforms can replay what happened; almost none can show why.</div>
  </div>

  <!-- 02 the mandate -->
  <div class="breaker rv"><span class="bn">02</span><span class="bk">The standards</span></div>
  <section class="wrap">
    <h2 class="rv">Agents are their own regulated category now.</h2>
    <div class="mcards">
      <div class="mc rv">
        <div class="mt">The frameworks</div>
        <div class="ml">the landscape</div>
        <p>Agent governance spans the EU AI Act, NIST AI RMF, ISO 42001, SOC 2 and GDPR — none designed for <em>agentic</em> AI.</p>
        <div class="mf">NIST opened an AI Agent Standards Initiative (Feb 2026); Singapore published the first agent governance framework (Jan 2026).</div>
      </div>
      <div class="mc rv">
        <div class="mt">Execution + intent</div>
        <div class="ml">what's usually missing</div>
        <p>A defensible agent trail needs both <em>execution</em> (what the agent did) and <em>intent</em> (why). Most programs capture only the first.</p>
        <div class="mf"><span class="air">AIR</span>'s causal graph and counterfactual replay are the "why" — the half most tools can't show.</div>
      </div>
      <div class="mc rv">
        <div class="mt">EU AI Act</div>
        <div class="ml">Articles 12 &amp; 73</div>
        <p>Logging (Art. 12) and incident reporting (Art. 73) are the agent-relevant obligations. The Digital Omnibus (provisional agreement May 7, 2026) defers high-risk Annex III obligations from Aug 2, 2026 to <em>Dec 2, 2027</em>.</p>
        <div class="mf flag">Provisional until adopted and published in the Official Journal (expected before Aug 2, 2026); until then Aug 2, 2026 stays an active date. Article 5 prohibitions have applied since Feb 2025.</div>
      </div>
    </div>
  </section>

  <!-- 03 how AIR answers -->
  <div class="breaker rv"><span class="bn">03</span><span class="bk">How <span class="air">AIR</span> answers</span></div>
  <section class="wrap">
    <h2 class="rv">Everything an OEM needs, as an embeddable layer.</h2>
    <div class="maprows">
      <div class="mr rv"><div class="demand">Give every customer their own evidence?</div><div class="answer"><span class="layer">Multi-tenant</span>Per-tenant signed chains, cryptographically isolated, one customer never sees another.</div></div>
      <div class="mr rv"><div class="demand">Prove not just what, but why?</div><div class="answer"><span class="layer">Causal</span>Causal graph plus counterfactual replay — intent observability, not just execution.</div></div>
      <div class="mr rv"><div class="demand">Map one record to whatever framework they cite?</div><div class="answer"><span class="layer">Report</span>One AgDR record → SOC 2 · ISO 42001 · EU AI Act · NIST evidence.</div></div>
      <div class="mr rv"><div class="demand">Ship it as your own feature?</div><div class="answer"><span class="layer">Embed</span>The Apache-2.0 <code>airsdk</code> under your brand; "powered by AIR" is optional.</div></div>
      <div class="mr rv"><div class="demand">Survive agent-to-agent handoffs?</div><div class="answer"><span class="layer">Handoff</span>Cross-agent chain of custody — the AgDR Handoff Protocol carries proof across delegations.</div></div>
    </div>
  </section>

  <!-- 04 the evidence -->
  <div class="breaker rv" id="evidence"><span class="bn">04</span><span class="bk">The evidence</span></div>
  <section class="evsec">
    <div class="evtext rv">
      <h2>Your brand on the record. Your customer verifies it.</h2>
      <p>Each customer gets a signed, anchored, per-tenant chain they can verify independently, with zero calls to your backend and zero to ours. You ship the accountability; they own the proof.</p>
      <a class="flink" href="/get-started">Read the SDK docs →</a>
    </div>
    <div class="record rv">
      <div class="rec-h">AgDR record · agdr/v2 · tenant: acme-corp</div>
      <div class="chainrow"><b>Delegation</b> · acme-admin authorized support-resolver-12</div>
      <div class="chainrow"><b>Action</b> · refund issued $240 — within policy</div>
      <div class="chainrow"><b>Why</b> · causal graph: ticket #88 → policy match → approve</div>
      <div class="chainrow halt"><b>Halt</b> · PII export blocked — SV-EXFIL</div>
      <div class="rec-sign">sig: ed25519 · hash: blake3 · per-tenant · anchor: Rekor</div>
      <div class="verify">✓ verified by the customer · zero calls to your platform</div>
    </div>
  </section>

  <!-- 05 what you get -->
  <div class="breaker rv"><span class="bn">05</span><span class="bk">What you get</span></div>
  <section class="wrap">
    <h2 class="rv">The tiers platform builders embed.</h2>
    <div class="tiers">
      <div class="tier feat rv">
        <div class="tn">Enterprise / OEM</div><div class="tl">embed &amp; white-label</div>
        <ul>
          <li>Multi-tenant, per-customer signed chains</li>
          <li>White-label, "powered by AIR" optional</li>
          <li>Causal graph, query &amp; counterfactual replay</li>
          <li>AgDR Handoff for agent-to-agent custody</li>
          <li>SOC 2 · ISO 42001 · EU AI Act · NIST evidence</li>
        </ul>
        <a class="pb" href="/contact">Talk about embedding</a>
      </div>
      <div class="tier rv">
        <div class="tn">Air-gapped</div><div class="tl">for your regulated tenants</div>
        <div class="plus2">Everything in Enterprise, plus</div>
        <ul>
          <li>On-prem / offline anchoring per tenant</li>
          <li>No phone-home — records never leave</li>
          <li>Extended retention + PQ re-anchoring</li>
          <li>Admissibility Pack — FRE 902 + expert support</li>
        </ul>
        <a class="pb" href="/contact">Talk to us</a>
      </div>
    </div>
    <p class="payline">The OSS <span class="air">AIR</span> SDK is on PyPI today, Apache-2.0-licensed: start embedding in an afternoon, then turn on multi-tenant chains, replay and framework reports when your customers ask.</p>
  </section>

  <!-- close -->
  <section class="close rv">
    <h2>Hand your users proof, not promises.</h2>
    <p>Let's scope an embed: per-tenant chains, the causal "why," and the framework reports your customers' auditors ask for, shipped as your feature.</p>
    <a class="btn-red big" href="/contact">Talk about embedding →</a>
    <div class="pills">
      <span>EU AI Act Art. 12 / 73</span><span>NIST AI RMF</span><span>ISO 42001</span><span>SOC 2</span><span>GDPR</span><span>AgDR Handoff</span>
    </div>
  </section>

  <footer class="foot">
    <span class="fco">Vindicara · <span class="proj">project</span> <span class="air-wm">AIR</span> v1.0.1</span>
    <span class="fmail">support@vindicara.io · This page is itself on the record.</span>
  </footer>
</div>
