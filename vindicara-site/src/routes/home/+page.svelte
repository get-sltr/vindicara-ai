<script>
  // @ts-nocheck
  import { onMount } from 'svelte';
  import SiteHeader from '$lib/components/SiteHeader.svelte';

  onMount(() => {
    const s = document.createElement('script');
    s.src = '/three.min.js';
    s.onload = initGlobe;
    document.head.appendChild(s);

    function initGlobe(){
      const el=document.getElementById('globe'); if(!el||!window.THREE) return;
      const W=el.clientWidth||440, H=440;
      const scene=new THREE.Scene();
      const cam=new THREE.PerspectiveCamera(38,W/H,0.1,100); cam.position.z=4.0;
      const rnd=new THREE.WebGLRenderer({alpha:true,antialias:true}); rnd.setPixelRatio(Math.min(devicePixelRatio,2)); rnd.setSize(W,H); el.appendChild(rnd.domElement);
      const root=new THREE.Group(); root.rotation.z=0.36; scene.add(root);
      const loader=new THREE.TextureLoader(); loader.crossOrigin='anonymous';
      const night=loader.load('/earth-night.jpg');
      const earth=new THREE.Mesh(new THREE.SphereGeometry(1.15,72,72), new THREE.MeshBasicMaterial({map:night}));
      root.add(earth);
      earth.add(new THREE.Mesh(new THREE.SphereGeometry(1.152,72,72), new THREE.MeshBasicMaterial({map:night,transparent:true,opacity:0.8,blending:THREE.AdditiveBlending})));
      const topo=loader.load('/earth-topology.png');
      earth.add(new THREE.Mesh(new THREE.SphereGeometry(1.156,72,72), new THREE.MeshBasicMaterial({map:topo,color:0xffffff,transparent:true,opacity:1,blending:THREE.AdditiveBlending})));
      earth.add(new THREE.Mesh(new THREE.SphereGeometry(1.159,72,72), new THREE.MeshBasicMaterial({map:topo,color:0xffffff,transparent:true,opacity:0.9,blending:THREE.AdditiveBlending})));
      (function loop(){requestAnimationFrame(loop); earth.rotation.y+=0.0011; rnd.render(scene,cam);})();
      addEventListener('resize',()=>{const w=el.clientWidth;cam.aspect=w/H;cam.updateProjectionMatrix();rnd.setSize(w,H);});
    }
  });
</script>

<svelte:head>
  <title>Project AIR · The accountability layer for AI agents</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
</svelte:head>

<div class="air-home">
<div class="dotfield"></div>

<div class="annc">Commercial tiers now in private beta with design partners · <a href="/contact">Book an agent audit →</a></div>

<SiteHeader />

<section class="hero2">
  <div>
    <h1>When your agents act on their own, can you prove what they did?</h1>
    <p class="sub"><span class="air">AIR</span> signs every agent action, binds it to the human who authorized it, and anchors it to a public log. One loop, four moves.</p>
    <div class="looprow">AUDIT <span class="pipe">|</span> PROVE <span class="pipe">|</span> PROTECT <span class="pipe">|</span> MONITOR</div>
    <div class="cta-row">
      <a class="btn-red" href="/get-started">Start free</a>
      <a class="bookd" href="/contact">Book a demo →</a>
    </div>
    <div class="trustline">Open source · Apache 2.0 · no credit card · verify it yourself</div>
    <div class="statchips">
      <div class="sc"><b>212</b> agents live</div>
      <div class="sc"><b>Ed25519</b> signed</div>
      <div class="sc"><b>BLAKE3</b> chained</div>
    </div>
  </div>
  <div class="globe-wrap">
    <div class="glow-bg"></div>
    <div class="glabel">· Global agent network · <span class="lv">live</span> ·</div>
    <div id="globe" class="globe"></div>
  </div>
</section>

<div class="scene">
  <div class="ts">02:14:07 · agent: records-export-07</div>
  <div class="big">An agent with database access just exported 9,000 patient records.</div>
  <div class="sub">Your team can tell you it happened. They can't prove what it was authorized to do, or that the log wasn't edited after. That's the question every regulator, auditor, and court is about to ask.</div>
</div>

<section class="sec">
  <div class="wrap">
    <h2>Audit it. Prove it. Protect it. Monitor it.</h2>
    <p class="lead">One loop, running the whole time, so the answer exists before you need it.</p>
    <div class="feat2">
      <div class="fcard">
        <h3>Catch what breaks scope, the instant it happens.</h3>
        <p>16 detectors read every action in real time. The deterministic floor halts an agent the moment it steps outside what a human authorized.</p>
        <a class="flink" href="/monitor">See detection →</a>
        <div class="shot">
          <div class="ui-title2">Signed Intent Capsule · chain</div>
          <div class="chainrow"><b>Delegation</b> · dr.okafor authorized claims-bot</div>
          <div class="chainrow"><b>Action</b> · ehr.read — in scope</div>
          <div class="chainrow halt"><b>Halt</b> · bulk export blocked — SV-EXFIL</div>
          <div class="verify">✓ chain intact · verify on search.sigstore.dev</div>
        </div>
      </div>
      <div class="fcard">
        <h3>Prove it to anyone, without their trust.</h3>
        <p>Every action is signed in-process, bound to the authorizing human, and anchored to a public log. Self-authenticating evidence an auditor, insurer, or court can verify.</p>
        <a class="flink" href="/evidence">See the evidence →</a>
        <div class="shot">
          <div class="ui-title2">Containment</div>
          <div class="ui-row crit"><span>Agent halted · awaiting approval</span><span class="tag">Held</span></div>
          <div class="ui-row"><span>Approve &amp; sign · Auth0 / passkey</span><span class="ok">FIDO2</span></div>
          <div class="ui-foot">No agent acts without a delegation. Forged tokens stay halted.</div>
        </div>
      </div>
    </div>
    <div class="quote">
      <div class="q">Turn <span class="air" style="font-style:italic">AIR</span> on.</div>
      <div class="qsub">And from this moment, every action is on the record.</div>
    </div>
  </div>
</section>

<div class="proof">
  <h2>This page proves it.</h2>
  <p>Every request you just made was signed and anchored to a public transparency log. Not a claim, a dare. Verify it yourself, with zero Vindicara infrastructure in the path.</p>
  <div class="v">› verify on search.sigstore.dev</div>
</div>

<div class="trust">
  <span>OWASP Agentic</span><span>EU AI Act Art. 72</span><span>NIST AI RMF</span><span>FRE 902(13)–(14)</span><span>Apache 2.0 open source</span>
</div>
</div>

<style>
  .air-home{
    --navy:#070d1a; --navy1:#0c1426; --panel:#101c34; --raise:#16264a;
    --white:#F7FAFF; --soft:#F3D98A; --faint:#FFC83D;
    --line:rgba(255,255,255,.14); --line2:rgba(255,255,255,.08);
    --air:#E63946; --air2:#ff5763; --airbg:rgba(230,57,70,.16);
    position:relative; min-height:100vh; background:var(--navy); color:var(--white);
    font-family:'Inter',system-ui,-apple-system,sans-serif; -webkit-font-smoothing:antialiased;
  }
  .dotfield{position:fixed;inset:0;z-index:0;pointer-events:none;
    background-image:radial-gradient(circle, rgba(255,255,255,.55) 1.1px, transparent 1.9px);
    background-size:24px 24px;
    -webkit-mask-image:radial-gradient(circle,#000 0%,transparent 45%);
    mask-image:radial-gradient(circle,#000 0%,transparent 45%);
    -webkit-mask-size:42% 42%;mask-size:42% 42%;
    -webkit-mask-repeat:no-repeat;mask-repeat:no-repeat;
    animation:dotsweep 26s linear infinite}
  @keyframes dotsweep{
    0%{-webkit-mask-position:0% 38%;mask-position:0% 38%}
    25%{-webkit-mask-position:50% 38%;mask-position:50% 38%}
    50%{-webkit-mask-position:100% 38%;mask-position:100% 38%}
    75%{-webkit-mask-position:50% 38%;mask-position:50% 38%}
    100%{-webkit-mask-position:0% 38%;mask-position:0% 38%}}
  @media (prefers-reduced-motion: reduce){ .dotfield{animation:none;opacity:.5} }
  .annc{position:relative;z-index:1;background:var(--air);color:#fff;text-align:center;font-size:13px;padding:9px 16px;font-weight:500}
  .annc a{color:#fff;text-decoration:underline;text-underline-offset:2px;font-weight:600}
  .air{color:var(--air2);font-weight:700}
  .wrap{max-width:1100px;margin:0 auto;padding:0 28px;position:relative;z-index:1}
  .cta-row{display:flex;gap:12px;align-items:center;margin-top:30px;flex-wrap:wrap}
  .btn-red{background:var(--air);color:#fff;border:0;font:600 15px Inter,sans-serif;padding:13px 22px;border-radius:10px;cursor:pointer;text-decoration:none;display:inline-block}
  .btn-red:hover{background:var(--air2)}
  .scene{position:relative;z-index:1;margin:46px auto;max-width:760px;background:#0c1733;border:1px solid var(--line);border-left:3px solid var(--air);border-radius:14px;padding:26px 30px}
  .scene .ts{font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;font-size:13px;color:var(--air2)}
  .scene .big{font-size:21px;color:#eef3fb;line-height:1.5;margin-top:10px;font-weight:600}
  .scene .sub{font-size:15px;color:#cdd8ec;margin-top:12px;line-height:1.6}
  .sec{padding:46px 0;position:relative;z-index:1}
  .sec h2{font-size:32px;font-weight:800;letter-spacing:-.02em;text-align:center;color:#fff}
  .sec .lead{text-align:center;color:#cdd8ec;font-size:16px;max-width:60ch;margin:12px auto 0}
  .proof{position:relative;z-index:1;margin:46px auto;max-width:860px;text-align:center;background:linear-gradient(180deg,var(--airbg),transparent);border:1px solid rgba(230,57,70,.4);border-radius:16px;padding:34px}
  .proof h2{font-size:26px;color:#fff;font-weight:800}
  .proof p{color:#cdd8ec;font-size:15px;margin:10px auto 0;max-width:62ch;line-height:1.6}
  .proof .v{margin-top:16px;font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;font-size:13px;color:var(--air2)}
  .trust{display:flex;gap:10px;flex-wrap:wrap;justify-content:center;margin:28px 0 72px;position:relative;z-index:1}
  .trust span{font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;font-size:11px;color:var(--faint);border:1px solid var(--line);padding:7px 12px;border-radius:999px}
  .hero2{position:relative;z-index:1;max-width:1180px;margin:0 auto;padding:64px 28px 18px;display:grid;grid-template-columns:1.05fr 1fr;gap:40px;align-items:center}
  .hero2 h1{font-size:46px;font-weight:800;letter-spacing:-.03em;line-height:1.09;color:#fff;margin:14px 0 0}
  .hero2 .sub{font-size:17px;color:#cdd8ec;line-height:1.6;margin-top:18px;max-width:52ch}
  .hero2 .cta-row{justify-content:flex-start}
  .bookd{color:#fff;text-decoration:none;font-weight:600;font-size:15px;padding:13px 6px}
  .bookd:hover{color:var(--air2)}
  .trustline{font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;font-size:11.5px;color:var(--faint);margin-top:16px}
  .looprow{font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;font-size:13px;letter-spacing:.14em;color:#fff;font-weight:600;margin-top:20px}
  .looprow .pipe{color:var(--air2);margin:0 9px;font-weight:700}
  .glow-bg{position:absolute;inset:-26px;z-index:-1;background:radial-gradient(60% 60% at 72% 26%, rgba(230,57,70,.24), transparent 70%);filter:blur(18px)}
  .ui-row{display:flex;justify-content:space-between;align-items:center;gap:10px;background:#101c34;border:1px solid var(--line2);border-radius:9px;padding:9px 12px;margin-bottom:7px;color:#dbe3f2;font-size:12.5px}
  .ui-row.crit{border-color:rgba(230,57,70,.45)}
  .ui-row .tag{font-size:10px;color:#ff9a9a;border:1px solid rgba(230,57,70,.45);padding:2px 8px;border-radius:999px;white-space:nowrap}
  .ui-row .ok{font-size:11px;color:#3fd99b;white-space:nowrap}
  .ui-foot{font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;font-size:10.5px;color:var(--faint);margin-top:8px}
  .ui-title2{font-weight:700;color:#fff;font-size:13px;margin-bottom:10px}
  .chainrow{background:#101c34;border:1px solid var(--line2);border-left:2px solid var(--faint);border-radius:0 8px 8px 0;padding:8px 12px;margin-bottom:6px;color:#dbe3f2;font-size:12.5px}
  .chainrow b{color:#fff}
  .chainrow.halt{border-left-color:var(--air)}
  .verify{margin-top:8px;color:#3fd99b;font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;font-size:11px}
  .feat2{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:30px}
  .fcard{background:#0c1733;border:1px solid var(--line);border-radius:18px;padding:26px 26px 0;overflow:hidden}
  .fcard h3{font-size:20px;font-weight:700;color:#fff;line-height:1.25}
  .fcard p{font-size:14px;color:#cdd8ec;line-height:1.55;margin-top:10px}
  .flink{display:inline-block;color:var(--air2);font-weight:600;font-size:13px;margin-top:12px;text-decoration:none}
  .shot{margin-top:20px;border-radius:14px 14px 0 0;border:1px solid var(--line);border-bottom:0;background:#0b1426;padding:14px}
  .quote{max-width:880px;margin:46px auto 0;text-align:center}
  .quote .q{font-size:32px;font-weight:700;color:#fff;line-height:1.2;letter-spacing:-.01em}
  .quote .qsub{font-size:17px;color:#cdd8ec;margin-top:14px;line-height:1.55}
  .globe-wrap{position:relative;display:flex;align-items:center;justify-content:center}
  .globe{width:100%;height:440px}
  .glabel{position:absolute;top:6px;left:0;right:0;text-align:center;font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--faint)}
  .glabel .lv{color:#3fd99b}
  .statchips{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}
  .sc{font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;font-size:12px;color:#cdd8ec;border:1px solid var(--line);border-radius:999px;padding:7px 13px}
  .sc b{color:#fff}
  @media(max-width:880px){ .hero2{grid-template-columns:1fr} .feat2{grid-template-columns:1fr} }
  @media(max-width:820px){ .hero2 h1{font-size:36px} }
</style>
