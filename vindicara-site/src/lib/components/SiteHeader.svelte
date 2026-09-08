<script>
  // @ts-nocheck
  // Single shared marketing top-nav: logo + Solutions / Products / Company mega-menus.
  // Used on every public page (homepage, solutions/*, AppShell pages, APPM pages).
  // Self-contained: defines its own CSS variables on <header> so it renders correctly
  // regardless of the page it is dropped into (it does not rely on .air-home).
  import { onMount } from 'svelte';
  import { beginAuth0Login } from '$lib/console/stores/session';
  import MobileSheet from './MobileSheet.svelte';

  let openMenu = $state(null);
  let mobileOpen = $state(false);
  function toggleMenu(id){ openMenu = openMenu === id ? null : id; }

  onMount(() => {
    const onDocClick = () => { openMenu = null; };
    document.addEventListener('click', onDocClick);
    return () => document.removeEventListener('click', onDocClick);
  });
</script>

<header>
  <div class="bar">
    <a class="logo" href="/home"><img src="/plane.svg" alt="" class="logo-img" /><span class="wordmark"><span class="proj">project</span> <span class="airw">AIR</span><span class="tm">™</span></span></a>
    <nav>
      <a class="nav-item lead" href="https://axiisium.com">Axiisium</a>
      <button class="nav-item" class:on={openMenu==='solutions'} onclick={(e)=>{ e.stopPropagation(); toggleMenu('solutions'); }}>Solutions <span class="car">▾</span></button>
      <button class="nav-item" class:on={openMenu==='products'} onclick={(e)=>{ e.stopPropagation(); toggleMenu('products'); }}>Products <span class="car">▾</span></button>
      <button class="nav-item" class:on={openMenu==='company'} onclick={(e)=>{ e.stopPropagation(); toggleMenu('company'); }}>Company <span class="car">▾</span></button>
      <a class="ghost" href="/get-started">Customers</a>
      <a class="ghost" href="/pricing">Pricing</a>
    </nav>
    <div class="right">
      <button type="button" class="ghost signin" onclick={(e)=>{ e.stopPropagation(); beginAuth0Login(); }}>Sign in</button>
      <a class="cta" href="/contact">Book a demo</a>
    </div>
    <button
      class="burger"
      class:open={mobileOpen}
      aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
      aria-expanded={mobileOpen}
      aria-controls="mobile-nav"
      onclick={(e)=>{ e.stopPropagation(); mobileOpen = !mobileOpen; }}
    ><span></span><span></span><span></span></button>
  </div>

  <div class="mega" class:open={openMenu==='solutions'} onclick={(e)=>e.stopPropagation()}>
    <div class="mega-in">
      <div class="col">
        <h4>By industry</h4>
        <a class="mi" href="/solutions/healthcare"><span class="ic"></span><span><span class="mt">Healthcare</span><span class="md">FHIR/HL7, HIPAA, BAA</span></span></a>
        <a class="mi" href="/solutions/finance"><span class="ic"></span><span><span class="mt">Finance &amp; insurance</span><span class="md">FINRA/SEC audit trails</span></span></a>
        <a class="mi" href="/solutions/government"><span class="ic"></span><span><span class="mt">Government &amp; public sector</span><span class="md">Air-gapped, sovereign</span></span></a>
        <a class="mi" href="/solutions/platforms"><span class="ic"></span><span><span class="mt">AI agent platforms</span><span class="md">Accountability for your users</span></span></a>
      </div>
      <div class="col">
        <h4>By use case</h4>
        <a class="mi" href="/solutions/audit-readiness"><span class="ic"></span><span><span class="mt">Audit readiness</span><span class="md">SOC 2 · HIPAA · ISO 42001 · EU AI Act</span></span></a>
        <a class="mi" href="/solutions/incident-response"><span class="ic"></span><span><span class="mt">Incident response</span><span class="md">Reconstruct &amp; prove in minutes</span></span></a>
        <a class="mi" href="/solutions/compliance-evidence"><span class="ic"></span><span><span class="mt">Compliance evidence</span><span class="md">Records assessors actually ask for</span></span></a>
        <a class="mi" href="/solutions/agent-governance"><span class="ic"></span><span><span class="mt">Agent governance</span><span class="md">Who authorized what, proven</span></span></a>
      </div>
      <div class="col">
        <h4>By framework</h4>
        <a class="mi" href="/solutions/soc2"><span class="ic"></span><span><span class="mt">SOC 2</span><span class="md">CC7.2 / CC7.3 agent evidence</span></span></a>
        <a class="mi" href="/solutions/hipaa"><span class="ic"></span><span><span class="mt">HIPAA</span><span class="md">45 CFR 164.312(b)</span></span></a>
        <a class="mi" href="/solutions/iso-42001"><span class="ic"></span><span><span class="mt">ISO 42001</span><span class="md">AI management system</span></span></a>
        <a class="mi" href="/solutions/eu-ai-act"><span class="ic"></span><span><span class="mt">EU AI Act</span><span class="md">Article 12 logging</span></span></a>
      </div>
      <div class="col hl">
        <h4>Highlights</h4>
        <a class="hcard feat" href="/contact"><div class="ht">Book an agent audit</div><div class="hd">See what your agents did. Free eval, nothing deployed.</div></a>
        <a class="hcard" href="/evidence"><div class="ht">Hardware-rooted evidence</div><div class="hd">Validated on real NVIDIA H100 confidential compute.</div></a>
      </div>
    </div>
  </div>

  <div class="mega" class:open={openMenu==='products'} onclick={(e)=>e.stopPropagation()}>
    <div class="mega-rich">
      <a class="feature" href="/platform">
        <div class="feat-dots"></div>
        <div class="feat-body">
          <div class="feat-kicker">Project <span class="air">AIR</span> Platform</div>
          <div class="feat-title">Your complete agent-accountability HQ</div>
          <div class="feat-link">Explore platform →</div>
        </div>
      </a>
      <div class="prod-grid">
        <a class="pcard ax" href="https://axiisium.com"><div class="pc-h">Axiisium</div><div class="pc-d">The Project AIR trust layer, proving out live on AML diagnosis.</div><div class="pc-l">See the flagship →</div></a>
        <a class="pcard" href="/audit"><div class="pc-h">Audit</div><div class="pc-d">The record you take into your audit.</div><div class="pc-l">Learn more →</div></a>
        <a class="pcard" href="/prove"><div class="pc-h">Prove</div><div class="pc-d">Signed, anchored, independently verifiable.</div><div class="pc-l">Learn more →</div></a>
        <a class="pcard" href="/protect"><div class="pc-h">Protect</div><div class="pc-d">Halt agents before harm, not after.</div><div class="pc-l">Learn more →</div></a>
        <a class="pcard" href="/monitor"><div class="pc-h">Monitor</div><div class="pc-d">16 detectors, every action, live.</div><div class="pc-l">Learn more →</div></a>
        <a class="pcard" href="/get-started"><div class="pc-h"><span class="air">AIR</span> SDK &amp; CLI</div><div class="pc-d">Open source, on PyPI. Start in an afternoon.</div><div class="pc-l">Learn more →</div></a>
        <a class="pcard" href="/flightdeck?demo=1"><div class="pc-h">FlightDeck</div><div class="pc-d">The operator cockpit for your fleet.</div><div class="pc-l">See the demo →</div></a>
        <a class="pcard" href="/pricing"><div class="pc-h"><span class="air">AIR</span> Cloud</div><div class="pc-d">Hosted ingestion, retention, alerting.</div><div class="pc-l">Learn more →</div></a>
        <a class="pcard" href="/admissibility"><div class="pc-h">Admissibility</div><div class="pc-d">Self-authenticating, FRE 902(13)–(14).</div><div class="pc-l">Learn more →</div></a>
        <a class="pcard" href="/structural-verification"><div class="pc-h">Structural Verification</div><div class="pc-d">The deterministic floor agents can't talk past.</div><div class="pc-l">Learn more →</div></a>
      </div>
    </div>
  </div>

  <div class="mega" class:open={openMenu==='company'} onclick={(e)=>e.stopPropagation()}>
    <div class="mega-in">
      <div class="col">
        <h4>Company</h4>
        <a class="mi" href="/about"><span class="ic"></span><span><span class="mt">About</span><span class="md">Why we build the record</span></span></a>
        <a class="mi" href="https://axiisium.com"><span class="ic"></span><span><span class="mt">Axiisium</span><span class="md">Our healthcare AI flagship</span></span></a>
        <a class="mi" href="/contact"><span class="ic"></span><span><span class="mt">Contact</span><span class="md">Talk to us</span></span></a>
        <a class="mi" href="/policy"><span class="ic"></span><span><span class="mt">Policy</span><span class="md">Evidence-based agent governance</span></span></a>
      </div>
      <div class="col">
        <h4>Resources</h4>
        <a class="mi" href="/blog"><span class="ic"></span><span><span class="mt">Blog</span><span class="md">Writing on agent accountability</span></span></a>
        <a class="mi" href="/press"><span class="ic"></span><span><span class="mt">Press</span><span class="md">News &amp; coverage</span></span></a>
        <a class="mi" href="https://github.com/vindicara-inc/projectair" target="_blank" rel="noopener"><span class="ic"></span><span><span class="mt">Docs &amp; GitHub</span><span class="md">Apache 2.0, read every line</span></span></a>
      </div>
      <div class="col">
        <h4>Community</h4>
        <a class="mi" href="https://github.com/vindicara-inc/projectair" target="_blank" rel="noopener"><span class="ic"></span><span><span class="mt">Open source</span><span class="md">Our OSS projects</span></span></a>
        <a class="mi" href="/contact"><span class="ic"></span><span><span class="mt">Events</span><span class="md">Where to find us</span></span></a>
        <a class="mi" href="/design-partner"><span class="ic"></span><span><span class="mt">Partners</span><span class="md">Build with Vindicara</span></span></a>
      </div>
      <div class="col hl">
        <h4>Highlights</h4>
        <a class="hcard feat" href="https://axiisium.com"><div class="ht">Axiisium</div><div class="hd">Our healthcare flagship: multimodal AI for blood cancer, built to be provable.</div></a>
        <a class="hcard" href="https://github.com/vindicara-inc/projectair" target="_blank" rel="noopener"><div class="ht">Open source on PyPI</div><div class="hd">Apache-2.0-licensed. Install projectair and verify every line.</div></a>
      </div>
    </div>
  </div>
</header>

<MobileSheet bind:open={mobileOpen} />

<style>
  header{position:sticky;top:0;z-index:40;background:rgba(12,20,38,.95);backdrop-filter:blur(14px);border-bottom:1px solid var(--line);
    --navy:#070d1a; --panel:#101c34; --raise:#16264a;
    --white:#F7FAFF; --soft:#F3D98A; --faint:#FFC83D;
    --line:rgba(255,255,255,.14); --line2:rgba(255,255,255,.08);
    --air:#E63946; --air2:#ff5763; --airbg:rgba(230,57,70,.16);
    --ax:#F47B20; --ax2:#ff9a4d; --axbg:rgba(244,123,32,.16);
    font-family:'Inter',system-ui,-apple-system,sans-serif}
  .bar{max-width:1240px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;padding:14px 28px}
  .logo{display:flex;align-items:center;gap:9px;text-decoration:none}
  .logo-img{height:120px;width:auto;display:block;margin-left:-64px;margin-top:-38px}
  .wordmark{display:inline-flex;align-items:baseline;gap:6px;margin-left:-30px}
  .wordmark .proj{font-family:'Spectral',Georgia,serif;font-style:italic;font-weight:500;font-size:24px;color:#fff;letter-spacing:.004em}
  .wordmark .airw{font-family:'Inter',sans-serif;color:var(--air2);font-size:24px;line-height:1;font-weight:900;text-transform:uppercase;letter-spacing:.004em}
  .wordmark .tm{font-size:10px;color:#8a93a8;align-self:flex-start;margin:3px 0 0 1px}
  .air{color:var(--air2);font-weight:700}
  nav{display:flex;align-items:center;gap:4px}
  .nav-item{background:none;border:0;color:var(--white);font-family:inherit;font-size:14.5px;font-weight:500;padding:10px 14px;cursor:pointer;display:flex;align-items:center;gap:6px;border-radius:8px}
  .nav-item:hover,.nav-item.on{color:#fff;background:rgba(255,255,255,.07)}
  .nav-item .car{font-size:10px;color:var(--faint);transition:transform .15s}
  .nav-item.on .car{transform:rotate(180deg);color:var(--air2)}
  .nav-item.lead{color:var(--ax2);font-weight:700;text-decoration:none}
  .nav-item.lead:hover{background:var(--axbg);color:var(--ax2)}
  .right{display:flex;align-items:center;gap:8px}
  .ghost{color:var(--white);font-size:14px;text-decoration:none;padding:9px 12px;font-weight:500;border-radius:8px;background:none;border:0;font-family:inherit;cursor:pointer}
  .ghost:hover{color:#fff;background:rgba(255,255,255,.07)}
  .cta{background:var(--air);color:#fff;border:0;font-weight:600;font-size:14px;padding:10px 18px;border-radius:9px;cursor:pointer;text-decoration:none;display:inline-block}
  .cta:hover{background:var(--air2)}
  .burger{display:none;flex-direction:column;justify-content:center;gap:5px;width:42px;height:42px;padding:0 9px;background:none;border:0;cursor:pointer;border-radius:9px}
  .burger:hover{background:rgba(255,255,255,.07)}
  .burger span{display:block;height:2px;width:100%;background:var(--white);border-radius:2px;transition:transform .22s ease,opacity .18s ease}
  .burger.open span:nth-child(1){transform:translateY(7px) rotate(45deg)}
  .burger.open span:nth-child(2){opacity:0}
  .burger.open span:nth-child(3){transform:translateY(-7px) rotate(-45deg)}
  .burger:focus-visible{outline:2px solid var(--air2);outline-offset:2px}
  .mega{display:none;position:absolute;left:0;right:0;top:100%;background:var(--panel);border-bottom:1px solid var(--line);box-shadow:0 30px 60px -24px rgba(0,0,0,.85)}
  .mega.open{display:block}
  .mega-in{max-width:1240px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr 1fr 1.1fr;padding:6px 28px 20px}
  .col{padding:18px 26px 8px;border-right:1px solid var(--line2)}
  .col:last-child{border-right:0}
  .col h4{font-size:11px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--faint);margin-bottom:12px}
  .mi{display:flex;align-items:flex-start;gap:11px;padding:7px 0;text-decoration:none;color:var(--white)}
  .mi:hover .mt{color:var(--air2)}
  .mi .ic{flex:none;width:18px;height:18px;border-radius:5px;background:var(--airbg);border:1px solid rgba(230,57,70,.4);margin-top:1px}
  .mt{font-size:14px;font-weight:600;color:var(--white)}
  .md{font-size:12px;color:var(--soft);margin-top:1px;line-height:1.4}
  .hl h4{color:var(--air2)}
  .hcard{display:block;text-decoration:none;border:1px solid var(--line);border-radius:12px;padding:15px;margin-bottom:11px;background:var(--raise)}
  .hcard:hover{border-color:var(--air)}
  .hcard.feat{background:linear-gradient(180deg,var(--airbg),var(--raise));border-color:rgba(230,57,70,.5)}
  .hcard .ht{font-size:15px;font-weight:700;color:var(--white)}
  .hcard .hd{font-size:12px;color:var(--soft);margin-top:4px;line-height:1.45}
  .mega-rich{max-width:1240px;margin:0 auto;display:grid;grid-template-columns:300px 1fr;gap:18px;padding:22px 28px 28px}
  .feature{position:relative;border-radius:16px;overflow:hidden;background:#0a1228;border:1px solid var(--line);display:flex;align-items:flex-end;min-height:280px;text-decoration:none}
  .feat-dots{position:absolute;inset:0;background-image:radial-gradient(circle, rgba(255,255,255,.5) 1px, transparent 1.7px);background-size:18px 18px;-webkit-mask-image:radial-gradient(circle at 72% 26%,#000,transparent 72%);mask-image:radial-gradient(circle at 72% 26%,#000,transparent 72%)}
  .feat-body{position:relative;padding:22px}
  .feat-kicker{color:var(--faint);font-size:12px;font-weight:600;letter-spacing:.12em;text-transform:uppercase}
  .feat-title{color:#fff;font-size:21px;font-weight:800;margin-top:8px;line-height:1.18}
  .feat-link{color:var(--air2);font-weight:600;font-size:14px;margin-top:14px}
  .prod-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px}
  .pcard{border:1px solid var(--line);border-radius:12px;padding:16px;text-decoration:none;background:var(--panel);display:flex;flex-direction:column}
  .pcard:hover{border-color:var(--air)}
  .pc-h{color:#fff;font-weight:700;font-size:15px}
  .pc-d{color:var(--soft);font-size:12.5px;margin-top:5px;line-height:1.42;flex:1}
  .pc-l{color:var(--air2);font-size:12px;font-weight:600;margin-top:12px}
  .pcard.ax{border-color:rgba(244,123,32,.35)}
  .pcard.ax:hover{border-color:var(--ax)}
  .pcard.ax .pc-l{color:var(--ax2)}
  @media(max-width:880px){ .mega-in{grid-template-columns:1fr 1fr} .prod-grid{grid-template-columns:1fr 1fr} }
  /* nav / .right are hidden by industry.css at <=900; the burger (no global rule
     competes for it) is shown here at the same breakpoint so they swap in lockstep. */
  @media(max-width:900px){ .burger{display:inline-flex} }
  @media(max-width:600px){ .mega-in{grid-template-columns:1fr} .mega-rich{grid-template-columns:1fr} .prod-grid{grid-template-columns:1fr} }
  @media(prefers-reduced-motion:reduce){ .burger span{transition:none} }
</style>
