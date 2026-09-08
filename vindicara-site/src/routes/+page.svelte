<script>
  // @ts-nocheck
  // VINDICARA intro — a scroll-gated dot-globe over a vector grid floor.
  // Three scrolls, three lenses, three colors. Land-filled dot continents.
  import { onMount } from 'svelte';
  import { geoOrthographic, geoPath, geoDistance, geoEquirectangular } from 'd3-geo';
  import { feature } from 'topojson-client';
  import world from 'world-atlas/countries-110m.json';

  const STAGES = [
    { key: 'industry',  rgb: [255, 87, 99],   label: 'By industry',  sub: 'who you are' },
    { key: 'usecase',   rgb: [255, 216, 77],  label: 'By use case',  sub: 'the job to be done' },
    { key: 'framework', rgb: [167, 139, 250], label: 'By framework', sub: "the rule you're under" }
  ];

  let stage = $state(0);
  let entered = $state(false);

  onMount(() => {
    const canvas = document.getElementById('globe');
    const ctx = canvas.getContext('2d');
    const land = feature(world, world.objects.countries);
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // fill the whole continents with a dot lattice.
    // Land test via a one-time rasterized equirectangular mask, NOT geoContains:
    // geoContains runs a full point-in-polygon test per point (~5s over this grid),
    // which blanked the globe for seconds. Rasterizing the land once and sampling
    // pixel alpha is the same result in milliseconds. Same grid, same dots.
    const dots = (() => {
      const MW = 1024, MH = 512;
      const mc = document.createElement('canvas');
      mc.width = MW; mc.height = MH;
      const mctx = mc.getContext('2d');
      const mproj = geoEquirectangular().fitSize([MW, MH], { type: 'Sphere' });
      const mpath = geoPath(mproj, mctx);
      mctx.fillStyle = '#fff';
      mctx.beginPath(); mpath(land); mctx.fill();
      const mask = mctx.getImageData(0, 0, MW, MH).data;
      const isLand = (lon, lat) => {
        const xy = mproj([lon, lat]);
        if (!xy) return false;
        const x = xy[0] | 0, y = xy[1] | 0;
        if (x < 0 || x >= MW || y < 0 || y >= MH) return false;
        return mask[(y * MW + x) * 4 + 3] > 128;
      };

      const pts = [];
      let seed = 20260618;
      const rnd = () => { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed / 0x7fffffff; };
      for (let lat = -56; lat <= 80; lat += 1.5) {
        const step = 1.5 / Math.max(0.22, Math.cos(lat * Math.PI / 180));
        for (let lon = -180; lon <= 180; lon += step) {
          const plon = lon + (rnd() - 0.5) * 1.0;
          const plat = lat + (rnd() - 0.5) * 1.0;
          if (isLand(plon, plat)) pts.push([plon, plat, 0.5 + rnd() * 0.5]);
        }
      }
      return pts;
    })();

    let W = 0, H = 0, dpr = 1, R = 1, cx = 0, cy = 0;
    const proj = geoOrthographic().clipAngle(90).rotate([-10, -14, 0]);
    const path = geoPath(proj, ctx);

    function resize() {
      W = innerWidth; H = innerHeight; dpr = Math.min(devicePixelRatio || 1, 2);
      canvas.width = W * dpr; canvas.height = H * dpr;
      canvas.style.width = W + 'px'; canvas.style.height = H + 'px';
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      R = Math.min(W, H) * (W < 700 ? 0.6 : 0.46);
      cx = W / 2; cy = H * 0.66;
      proj.translate([cx, cy]).scale(R);
    }
    resize();
    addEventListener('resize', resize);

    let rot = -10;
    const cur = [255, 87, 99];
    function render() {
      const target = entered ? [125, 145, 185] : STAGES[stage].rgb;
      for (let i = 0; i < 3; i++) cur[i] += (target[i] - cur[i]) * 0.06;
      const [cr, cg, cb] = cur.map(Math.round);

      if (!reduce) rot += 0.085;
      proj.rotate([rot, -14, 0]);
      const center = [-rot, 14];

      ctx.clearRect(0, 0, W, H);

      // sphere — dark, softly lit, no rim line
      ctx.beginPath(); path({ type: 'Sphere' });
      const g = ctx.createRadialGradient(cx - R * 0.3, cy - R * 0.35, R * 0.1, cx, cy, R * 1.05);
      g.addColorStop(0, '#0a1a3a'); g.addColorStop(0.6, '#060f1f'); g.addColorStop(1, '#02040c');
      ctx.fillStyle = g; ctx.fill();

      // country borders — very faint
      ctx.beginPath(); path(land);
      ctx.lineWidth = 0.5; ctx.strokeStyle = 'rgba(255,255,255,.10)'; ctx.stroke();

      // continent lights — additive so the landmasses glow
      ctx.globalCompositeOperation = 'lighter';
      for (const d of dots) {
        if (geoDistance(center, d) > Math.PI / 2) continue;
        const p = proj(d);
        if (!p) continue;
        const a = d[2];
        ctx.beginPath();
        ctx.arc(p[0], p[1], 1.0 * a + 0.35, 0, 6.283);
        ctx.fillStyle = `rgba(${cr},${cg},${cb},${0.45 + a * 0.4})`;
        ctx.fill();
      }
      ctx.globalCompositeOperation = 'source-over';
      requestAnimationFrame(render);
    }
    requestAnimationFrame(render);

    let cooldown = false;
    function advance(dir) {
      if (cooldown) return;
      cooldown = true; setTimeout(() => (cooldown = false), 720);
      if (dir > 0) { if (stage < STAGES.length - 1) stage += 1; else entered = true; }
      else { if (entered) entered = false; else if (stage > 0) stage -= 1; }
    }
    const onWheel = (e) => { e.preventDefault(); if (Math.abs(e.deltaY) > 6) advance(e.deltaY > 0 ? 1 : -1); };
    addEventListener('wheel', onWheel, { passive: false });
    const onKey = (e) => {
      if (['ArrowDown', 'PageDown', ' '].includes(e.key)) { e.preventDefault(); advance(1); }
      else if (['ArrowUp', 'PageUp'].includes(e.key)) { e.preventDefault(); advance(-1); }
    };
    addEventListener('keydown', onKey);
    let ty = 0;
    const onTS = (e) => (ty = e.touches[0].clientY);
    const onTM = (e) => { const dy = ty - e.touches[0].clientY; if (Math.abs(dy) > 36) { advance(dy > 0 ? 1 : -1); ty = e.touches[0].clientY; } };
    addEventListener('touchstart', onTS, { passive: true });
    addEventListener('touchmove', onTM, { passive: true });

    window.__intro = { set: (n) => { entered = n >= 3; stage = Math.max(0, Math.min(2, n)); } };

    return () => {
      removeEventListener('resize', resize); removeEventListener('wheel', onWheel);
      removeEventListener('keydown', onKey); removeEventListener('touchstart', onTS); removeEventListener('touchmove', onTM);
    };
  });

  const css = (rgb) => `rgb(${rgb[0]},${rgb[1]},${rgb[2]})`;
</script>

<svelte:head>
  <title>Vindicara — the accountability layer for AI agents</title>
  <meta name="description" content="Vindicara is the accountability layer for AI agents. Project AIR produces signed, tamper-evident, independently verifiable records of what an AI agent did and who authorized it, so every automated action traces back to a named human." />
  <link href="https://fonts.googleapis.com/css2?family=Spectral:wght@500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
</svelte:head>

<main style="--accent:{entered ? '#9fb0d0' : css(STAGES[stage].rgb)}">
  <div class="floor"><i></i></div>
  <div class="horizon"></div>
  <canvas id="globe"></canvas>

  <nav class="skip">
    <a href="/home">Project <span class="airx">AIR</span> →</a>
  </nav>

  <div class="wordmark">
    <h1>VINDICARA</h1>
    <div class="rule"></div>
    <p class="tagline">The accountability layer for AI agents</p>
  </div>

  <section class="seo-narrative">
    <h2>Vindicara: the accountability layer for AI agents</h2>
    <p>Vindicara builds the accountability layer for AI agents. Our product, Project AIR, produces signed, tamper-evident, and independently verifiable records of what an AI agent did and who authorized it, so every automated action traces back to a named human.</p>
    <p>Project AIR spans detection (surfacing what went wrong), verification (proving the record is real), explanation (showing why an action happened), containment (halting an agent and binding the action to a human approval), and cross-agent trust (preserving the chain of custody when one agent delegates to another). It ships as an open-source SDK and command-line tool on PyPI, alongside hosted and enterprise tiers.</p>
    <p>Teams adopt Vindicara three ways: by industry, such as healthcare; by use case, such as audit readiness; and by compliance framework, such as SOC 2. Vindicara runs Project AIR on its own production infrastructure and publishes a verifiable record of its own operations.</p>
    <p>Read more on our <a href="/about">About</a> page, explore the product on the <a href="/home">Project AIR</a> page, or see <a href="/pricing">pricing</a>.</p>
  </section>

  {#if !entered}
    <div class="lens" style="--accent:{css(STAGES[stage].rgb)}">
      <div class="lnum">0{stage + 1} <span>/ 03</span></div>
      <div class="llabel">{STAGES[stage].label}</div>
      <div class="lsub">{STAGES[stage].sub}</div>
    </div>
    <div class="hint">scroll to move through the three lenses</div>
  {:else}
    <div class="doors">
      <div class="dtitle">One record. Three ways in.</div>
      <div class="drow">
        <a class="door" style="--c:#ff5763" href="/solutions/healthcare">By industry</a>
        <a class="door" style="--c:#ffd84d" href="/solutions/audit-readiness">By use case</a>
        <a class="door" style="--c:#a78bfa" href="/solutions/soc2">By framework</a>
      </div>
      <a class="enter" href="/home">Project <span class="airx">AIR</span> →</a>
    </div>
  {/if}

  <div class="progress">
    {#each STAGES as s, i}
      <button class="seg" class:on={!entered && i === stage} class:done={entered || i < stage}
        style="--c:{css(s.rgb)}" aria-label={s.label}
        onclick={() => { entered = false; stage = i; }}></button>
    {/each}
    <button class="seg final" class:on={entered} style="--c:#9fb0d0" aria-label="Enter"
      onclick={() => (entered = true)}></button>
  </div>
</main>

<style>
  :global(body){margin:0;background:#070d1a}
  :global(body::after){display:none !important}  /* kill the global animated dotfield on this page */
  main{position:fixed;inset:0;overflow:hidden;color:#F7FAFF;
    font-family:'Inter',system-ui,sans-serif;
    background:radial-gradient(130% 95% at 50% 36%, color-mix(in srgb, var(--accent) 14%, transparent), transparent 60%), #070d1a;
    transition:background .8s ease}
  canvas{position:absolute;inset:0;z-index:2}

  /* vector grid floor */
  .floor{position:absolute;left:50%;bottom:0;width:260vw;height:40vh;transform:translateX(-50%);z-index:1;perspective:300px;perspective-origin:50% 0}
  .floor i{position:absolute;inset:0;transform:rotateX(76deg);transform-origin:50% 100%;
    background-image:
      linear-gradient(color-mix(in srgb,var(--accent) 15%,transparent) 1px, transparent 1px),
      linear-gradient(90deg, color-mix(in srgb,var(--accent) 15%,transparent) 1px, transparent 1px);
    background-size:46px 46px;
    -webkit-mask-image:linear-gradient(to top,#000 2%,rgba(0,0,0,.34) 22%,transparent 60%);
    mask-image:linear-gradient(to top,#000 2%,rgba(0,0,0,.34) 22%,transparent 60%);
    animation:floor 5.5s linear infinite}
  @keyframes floor{to{background-position:0 46px,0 46px}}
  .horizon{position:absolute;left:0;right:0;bottom:40vh;height:1px;z-index:1;
    background:linear-gradient(90deg,transparent,color-mix(in srgb,var(--accent) 42%,transparent),transparent);
    box-shadow:0 0 18px 1px color-mix(in srgb,var(--accent) 20%,transparent);transition:.8s ease}

  .skip{position:absolute;top:22px;right:26px;z-index:6;display:flex;flex-direction:column;align-items:flex-end;gap:7px}
  .skip a{font-family:ui-monospace, Menlo, Consolas, monospace;font-size:14px;letter-spacing:.04em;color:#F7FAFF;text-decoration:none;border-bottom:1px solid transparent;opacity:.9}
  .skip a:hover{opacity:1;border-bottom-color:#cdd8ec}
  .airx{color:#ff5763;font-weight:700}

  .wordmark{position:absolute;top:11vh;left:0;right:0;z-index:4;text-align:center;pointer-events:none}
  .wordmark h1{margin:0;font-family:'Spectral',serif;font-weight:600;font-size:clamp(40px,9vw,118px);letter-spacing:.14em;line-height:.9;color:#F7FAFF;text-indent:.14em;text-shadow:0 4px 60px rgba(0,0,0,.6)}
  .rule{width:min(560px,68vw);height:1px;background:linear-gradient(90deg,transparent,rgba(255,255,255,.4),transparent);margin:22px auto 0}
  .tagline{margin:16px auto 0;max-width:90vw;font-family:'Inter',system-ui,sans-serif;font-weight:400;font-size:clamp(13px,1.5vw,16px);letter-spacing:.05em;color:#aab6cf}
  /* accessible, crawler-readable company/product description; visually hidden (screen readers + search engines read it) */
  .seo-narrative{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0 0 0 0);clip-path:inset(50%);white-space:normal;border:0}

  .lens{position:absolute;left:0;right:0;bottom:15vh;z-index:5;text-align:center;pointer-events:none}
  .lnum{font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;font-size:13px;letter-spacing:.2em;color:var(--accent);font-weight:500;text-shadow:0 0 18px color-mix(in srgb,var(--accent) 55%,transparent)}
  .lnum span{color:#5f6b86;text-shadow:none}
  .llabel{font-family:'Spectral',serif;font-size:clamp(28px,4.5vw,48px);font-weight:600;color:#F7FAFF;margin-top:6px;letter-spacing:.01em}
  .lsub{font-size:15px;color:#9aa6c2;margin-top:8px;font-style:italic;font-family:'Spectral',serif}
  .hint{position:absolute;left:0;right:0;bottom:8vh;z-index:5;text-align:center;font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:#5f6b86;animation:breathe 2.6s ease-in-out infinite}
  @keyframes breathe{0%,100%{opacity:.4}50%{opacity:.85}}

  .doors{position:absolute;left:0;right:0;bottom:12vh;z-index:5;text-align:center}
  .dtitle{font-family:'Spectral',serif;font-size:clamp(22px,3.4vw,34px);font-weight:600;color:#F7FAFF;margin-bottom:22px}
  .drow{display:flex;gap:14px;justify-content:center;flex-wrap:wrap}
  .door{font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;font-size:13px;letter-spacing:.06em;text-decoration:none;color:#e7ecf6;padding:11px 20px;border:1px solid rgba(255,255,255,.2);border-radius:999px;background:rgba(255,255,255,.05);transition:.18s}
  .door:hover{border-color:var(--c);color:var(--c);box-shadow:0 0 0 3px color-mix(in srgb,var(--c) 18%,transparent),0 0 22px color-mix(in srgb,var(--c) 30%,transparent)}
  .enter{display:inline-block;margin-top:24px;font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;font-size:15px;letter-spacing:.04em;color:#F7FAFF;text-decoration:none;border-bottom:1px solid #F7FAFF;padding-bottom:2px}
  .enter:hover{color:#ff5763;border-color:#ff5763}

  .progress{position:absolute;bottom:28px;left:0;right:0;z-index:6;display:flex;gap:8px;justify-content:center}
  .seg{width:34px;height:3px;border:0;padding:0;border-radius:2px;background:rgba(255,255,255,.16);cursor:pointer;transition:.3s}
  .seg.on{background:var(--c);box-shadow:0 0 12px color-mix(in srgb,var(--c) 80%,transparent);width:48px}
  .seg.done{background:color-mix(in srgb,var(--c) 55%,rgba(255,255,255,.16))}
  .seg.final.on{background:var(--c);width:48px}

  @media (prefers-reduced-motion: reduce){ .hint,.floor i{animation:none} }
  @media (max-width:600px){ .wordmark{top:8vh} .lens{bottom:20vh} }
</style>
