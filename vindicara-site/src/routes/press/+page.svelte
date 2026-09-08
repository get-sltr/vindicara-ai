<script>
  import AppShell from '$components/AppShell.svelte';
</script>
<svelte:head><title>Vindicara · Press</title></svelte:head>

<AppShell active="press" title="press" scroll={true}>
  <div class="prose">
    <div class="eyebrow">Press</div>
    <h1>Press and media.</h1>
    <p>For interviews, briefings, logos, or fact-checks, reach the team directly. We respond to working journalists quickly.</p>

    <div class="contactcard">
      <div class="cc"><span class="cl">Press contact</span><a href="mailto:press@vindicara.io">press@vindicara.io</a></div>
      <div class="cc"><span class="cl">General</span><a href="mailto:support@vindicara.io">support@vindicara.io</a></div>
    </div>

    <h2>Company facts</h2>
    <ul>
      <li>Vindicara is a Delaware C-Corp founded in April 2026, building Project AIR, evidence-grade infrastructure for AI agents.</li>
      <li>Project AIR is open source under the Apache License 2.0: github.com/vindicara-inc/projectair, installable with pip install projectair.</li>
      <li>Vindicara is a member of the NVIDIA Inception program.</li>
    </ul>

    <h2>Press releases</h2>
    <div class="rel placeholder">
      <div class="rh">Release entries appear here</div>
      <p class="muted">This section is a working template. Add each release as a dated entry with a headline, summary, and link. Nothing is published here that has not been issued.</p>
    </div>

    <h2>Brand assets</h2>
    <p>Logo files, the Project AIR wordmark, and usage guidance are available on request from press@vindicara.io. The wordmark is always "Project AIR" with AIR set in Vindicara red.</p>
  </div>
</AppShell>

<style>
  .prose h1{font-size:36px;margin:14px 0 0}
  .contactcard{display:flex;gap:0;flex-direction:column;border:1px solid var(--line);background:var(--panel);box-shadow:var(--shadow);margin:20px 0;padding:6px 20px}
  .cc{display:flex;justify-content:space-between;align-items:center;padding:14px 0;border-top:1px solid var(--line2)} .cc:first-child{border-top:0}
  .cc .cl{font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--faint)}
  .cc a{color:var(--air2);text-decoration:none;font-size:14px;font-weight:600} .cc a:hover{text-decoration:underline}
  .rel.placeholder{border:1px dashed var(--line);padding:20px;text-align:center}
  .rh{font-family:var(--display);font-size:15px;font-weight:600;color:var(--soft)}
</style>
