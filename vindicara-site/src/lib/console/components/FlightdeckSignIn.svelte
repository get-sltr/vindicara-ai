<script lang="ts">
  import { authError, beginAuth0Login } from '$lib/console/stores/session';
  let pending = $state<'google' | 'github' | 'generic' | null>(null);
  $effect(() => { if ($authError) pending = null; });
  function startGoogle() { pending = 'google'; void beginAuth0Login('google-oauth2'); }
  function startGitHub() { pending = 'github'; void beginAuth0Login('github'); }
  function startGeneric() { pending = 'generic'; void beginAuth0Login(); }
</script>

<div class="wrap">
  <section class="left" aria-labelledby="sign-in-title">
    <a class="logo" href="/" aria-label="Project AIR home"><span class="mark" aria-hidden="true">▶</span><span>V<span>/</span>P <b>AIR</b></span></a>
    <div class="center">
      <p class="chip">Flightdeck access</p>
      <h1 id="sign-in-title">Sign in to Flightdeck.</h1>
      <p class="sub">Monitor agent evidence, investigate findings, and manage containment from one operator console.</p>
      <div class="button-row">
        <button class="button google" onclick={startGoogle} disabled={pending !== null}><span class="google-mark" aria-hidden="true">G</span>{pending === 'google' ? 'Redirecting…' : 'Google'}</button>
        <button class="button github" onclick={startGitHub} disabled={pending !== null}><span aria-hidden="true">●</span>{pending === 'github' ? 'Redirecting…' : 'GitHub'}</button>
      </div>
      <button class="button sso" onclick={startGeneric} disabled={pending !== null}><span aria-hidden="true">▣</span><span>{pending === 'generic' ? 'Redirecting…' : 'Sign in with SSO'}</span><small>Enterprise identity</small></button>
      <button class="email" onclick={startGeneric} disabled={pending !== null}>Continue with email ›</button>
      <div class="divider" aria-hidden="true">or</div>
      <button class="demo" disabled aria-disabled="true" title="Public demo access is not configured yet.">▶ Test-drive a demo chain <small>coming soon</small></button>
      <p class="fine">OAuth is handled by Auth0. Provider credentials never enter Flightdeck.</p>
      {#if $authError}<p class="error" role="status" aria-live="polite">{$authError}</p>{/if}
    </div>
    <nav class="footer" aria-label="Sign-in resources"><a href="/get-started">Docs</a><a href="/pricing">Pricing</a><a href="/security">Security</a></nav>
  </section>
  <aside class="right" aria-label="Project AIR trust details">
    <p class="label">What Flightdeck adds to your agent operations</p>
    <article><h2><i class="ok">✓</i>Signed local evidence</h2><p><span class="air">AIR</span> records signed Intent Capsules where your agents run, so your evidence chain stays under your control.</p></article>
    <article><h2><i class="alert">↗</i>Findings you can inspect</h2><p>Investigate <strong>10 OWASP Agentic, 3 OWASP LLM, and 3 <span class="air">AIR</span>-native</strong> detector signals in one place.</p></article>
    <div class="badges"><span><i></i>BLAKE3 + signatures</span><span><i></i>Auth0 PKCE</span><span><i></i>16 detectors</span></div>
    <div class="sectors"><span>Developers</span><span>Security teams</span><span>Regulated systems</span></div>
  </aside>
</div>

<style>
  .air { color: var(--air, #e63946); font-weight: 700; }
  :global(html), :global(body) { margin:0; background:#070710; }
  :global(button), :global(a) { font:inherit; }
  :global(button:focus-visible), :global(a:focus-visible) { outline:3px solid #fff; outline-offset:3px; }
  .wrap { --red:#e63946; --hair:rgba(255,255,255,.1); --muted:rgba(255,255,255,.66); --faint:rgba(255,255,255,.46); min-height:100vh; display:grid; grid-template-columns:1.05fr .95fr; color:#fff; font-family:Inter,system-ui,sans-serif; background:#070710; }
  .left { min-height:100vh; position:relative; overflow:hidden; display:flex; flex-direction:column; padding:34px 6vw; background:linear-gradient(165deg,#16223f 0%,#101a30 55%,#0b1020 100%); }
  .left::after { content:''; position:absolute; inset:auto -10% -32% 20%; height:42rem; background:radial-gradient(ellipse,rgba(230,57,70,.14),transparent 63%); }
  .logo,.footer { position:relative; z-index:1; }.logo { display:flex; gap:10px; align-items:center; width:max-content; color:#fff; text-decoration:none; font:700 15px ui-monospace,SFMono-Regular,Menlo,monospace; letter-spacing:.2em; }.logo span span,.logo b,.mark { color:var(--red); }.mark { filter:drop-shadow(0 0 8px rgba(230,57,70,.7)); }
  .center { position:relative; z-index:1; width:100%; max-width:400px; margin:auto; padding:68px 0; }.chip { display:inline-block; margin:0 0 22px; padding:7px 13px; border:1px solid rgba(255,255,255,.28); border-radius:99px; background:rgba(255,255,255,.12); font:11px ui-monospace,SFMono-Regular,Menlo,monospace; letter-spacing:.1em; text-transform:uppercase; } h1 { margin:0 0 12px; font-size:clamp(2.1rem,4vw,2.7rem); line-height:1.08; letter-spacing:-.035em; }.sub { margin:0 0 28px; color:rgba(255,255,255,.76); line-height:1.55; }.button-row { display:grid; grid-template-columns:1fr 1fr; gap:11px; margin-bottom:11px; }.button,.demo { min-height:48px; border-radius:10px; font-weight:700; font-size:14px; }.button { display:inline-flex; align-items:center; justify-content:center; gap:9px; width:100%; border:1px solid var(--hair); }.button:disabled,.email:disabled { cursor:wait; opacity:.72; }.google { border:0; background:#fff; color:#161616; }.google-mark { color:#4285f4; font-size:18px; }.github { background:#10101c; color:#fff; }.sso { justify-content:flex-start; padding:0 13px; background:rgba(255,255,255,.06); color:#fff; border-color:rgba(255,255,255,.28); }.sso small { margin-left:auto; color:var(--faint); font:9px ui-monospace,SFMono-Regular,Menlo,monospace; letter-spacing:.08em; text-transform:uppercase; }.email { display:block; width:100%; border:0; background:transparent; color:rgba(255,255,255,.78); padding:9px; font-size:13px; }.divider { display:flex; align-items:center; gap:14px; margin:16px 0; color:var(--faint); font:10px ui-monospace,SFMono-Regular,Menlo,monospace; letter-spacing:.16em; text-transform:uppercase; }.divider::before,.divider::after { content:''; flex:1; height:1px; background:rgba(255,255,255,.16); }.demo { width:100%; border:1px solid rgba(230,57,70,.36); background:rgba(230,57,70,.1); color:rgba(255,255,255,.6); cursor:not-allowed; }.demo small { color:var(--faint); }.fine { margin:16px 0 0; color:rgba(255,255,255,.58); text-align:center; font-size:12px; line-height:1.45; }.error { margin:14px 0 0; padding:10px 12px; border:1px solid rgba(255,180,84,.5); border-radius:8px; color:#ffd4a0; background:rgba(255,180,84,.09); font-size:12px; }.footer { display:flex; gap:18px; margin-top:auto; }.footer a { color:rgba(255,255,255,.62); text-decoration:none; font-size:12px; }
  .right { position:relative; display:flex; flex-direction:column; justify-content:center; gap:16px; min-height:100vh; overflow:hidden; padding:48px 5vw; border-left:1px solid var(--hair); background:#eef1f6; }.right::before { content:''; position:absolute; inset:0; opacity:.5; background-image:radial-gradient(rgba(20,26,45,.05) 1px,transparent 1px); background-size:24px 24px; }.right>* { position:relative; }.label { margin:0 0 2px; color:rgba(18,26,45,.6); font:10px ui-monospace,SFMono-Regular,Menlo,monospace; letter-spacing:.14em; text-transform:uppercase; }.right article { padding:20px 22px; border:1px solid var(--hair); border-radius:14px; background:rgba(12,12,22,.7); }.right h2 { display:flex; align-items:center; gap:11px; margin:0 0 8px; font-size:15px; }.right h2 i { display:grid; place-items:center; width:30px; height:30px; border-radius:8px; font-style:normal; }.ok { background:rgba(93,202,165,.16); color:#5dcaa5; }.alert { background:rgba(230,57,70,.16); color:#ff5d68; }.right p { margin:0; color:var(--muted); font-size:13px; line-height:1.55; }.right strong { color:#fff; }.badges,.sectors { display:flex; flex-wrap:wrap; gap:8px; }.badges span,.sectors span { display:inline-flex; align-items:center; gap:7px; padding:7px 11px; border:1px solid var(--hair); border-radius:8px; background:rgba(255,255,255,.04); color:var(--muted); font:11px ui-monospace,SFMono-Regular,Menlo,monospace; letter-spacing:.04em; }.badges i { width:8px; height:8px; border-radius:50%; background:#fff; }.sectors span { border-radius:99px; color:var(--faint); font-size:10px; letter-spacing:.08em; text-transform:uppercase; }
  @media (max-width:880px) { .wrap { grid-template-columns:1fr; }.right { display:none; }.left { padding:28px 7vw; }.footer { margin-top:0; } } @media (max-width:420px) { .button-row { grid-template-columns:1fr; }.sso small { display:none; } }
</style>
