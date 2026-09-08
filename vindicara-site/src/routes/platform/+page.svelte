<script>
  import AppShell from '$components/AppShell.svelte';
</script>
<svelte:head><title>Project AIR · The platform</title></svelte:head>

<AppShell active="platform" title="platform">
  <div class="wrap">
    <div class="shead">
      <div><div class="eyebrow">The platform</div><h2>Monitor. Enforce. Prove. Account.</h2></div>
      <span class="sp"></span>
      <p class="lead">Evidence plus enforcement, not evidence alone. The deterministic floor stops an uncovered agent before it acts, and signs the proof that it did.</p>
    </div>

    <div class="four">
      <div class="pcol"><div class="tag">M</div><h3>Monitor</h3><div class="pk">16 detectors</div><p>Every agent action is read against all 10 OWASP Top 10 for Agentic Applications signatures, 3 OWASP LLM categories, and 3 AIR-native checks. 14 run offline with zero config.</p><div class="math"><b>10</b> OWASP Agentic <i>+</i> <b>3</b> OWASP LLM <i>+</i> <b>3</b> AIR-native <i>=</i> <b>16</b></div><div class="fn">ASI04 ships a detector for MCP supply-chain risk; full supply-chain coverage is a commercial add-on.</div></div>
      <div class="pcol"><div class="tag red">E</div><h3>Enforce</h3><div class="pk">deterministic floor</div><p>Structural Verification runs as fixed logic over the causal graph. It returns the same verdict every time and cannot be prompt-injected or talked out of blocking. No agent acts without a human delegation.</p><div class="fn">SV-SECRET · SV-NET · SV-SCOPE · SV-ENTITY · SV-EXFIL</div></div>
      <div class="pcol"><div class="tag">P</div><h3>Prove</h3><div class="pk">signed + anchored</div><p>Each action is an AgDR record: BLAKE3 content hash, Ed25519 signature with opt-in ML-DSA-65 post-quantum signing, forward-chained and anchored to public Sigstore Rekor.</p><div class="fn">Records signed in-process, not reconstructed from logs.</div></div>
      <div class="pcol"><div class="tag">A</div><h3>Account</h3><div class="pk">delegated authority</div><p>Every agent is bound to a named human through Auth0, Microsoft Entra, Okta, or SPIFFE. This is the system of record for who authorized what, and the proof the authority was never exceeded.</p><div class="fn">The newest layer, and the one buyers ask for first.</div></div>
    </div>

    <div class="surfaces">
      <div class="surf"><div class="sl"><span class="nm">air</span><span class="lic">Apache 2.0 · OSS</span></div><p>The CLI. Ingest any agent trace, run the 16 detectors, output a signed forensic timeline. Free to download today.</p></div>
      <div class="surf"><div class="sl"><span class="nm">airsdk</span><span class="lic">Apache 2.0 · OSS</span></div><p>Drop-in instrumentation for LangChain, OpenAI, Anthropic, LlamaIndex, Gemini, and Google ADK. Signs every action at the moment it happens.</p></div>
      <div class="surf"><div class="sl"><span class="nm">FlightDeck</span></div><p>The hosted console. The deterministic floor enforced live, human-identity binding, and evidence packs. Where security, legal, and compliance work.</p></div>
    </div>
  </div>
</AppShell>

<style>
  .wrap{display:flex;flex-direction:column;height:100%;gap:18px}
  .four{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;flex:1;min-height:0}
  .pcol{background:var(--panel);border:1px solid var(--line);box-shadow:var(--shadow);padding:20px;display:flex;flex-direction:column}
  .pcol .tag{font-family:var(--display);font-size:15px;font-weight:700;color:#fff;width:30px;height:30px;display:grid;place-items:center;margin-bottom:14px;background:var(--raise)}
  .pcol .tag.red{background:var(--air)}
  .pcol h3{font-family:var(--display);font-size:20px;font-weight:600}
  .pcol .pk{font-family:var(--mono);font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--air2);margin:2px 0 10px}
  .pcol p{font-size:12.5px;color:var(--soft);line-height:1.55}
  .pcol .math{font-family:var(--mono);font-size:10.5px;color:var(--soft);margin-top:12px;padding:8px 10px;border:1px solid var(--line2);background:rgba(255,255,255,.02)}
  .pcol .math b{color:var(--white)} .pcol .math i{color:var(--faint);font-style:normal}
  .pcol .fn{font-family:var(--mono);font-size:10px;color:var(--faint);margin-top:auto;padding-top:12px}
  .surfaces{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
  .surf{border:1px solid var(--line);background:var(--navy1);padding:16px 18px}
  .surf .sl{display:flex;justify-content:space-between;align-items:center}
  .surf .nm{font-family:var(--mono);font-size:14px;font-weight:600} .surf .lic{font-family:var(--mono);font-size:9px;color:var(--faint);border:1px solid var(--line);padding:2px 7px}
  .surf p{font-size:11.5px;color:var(--soft);margin-top:8px;line-height:1.5}
  @media (max-width:1080px){ .four{grid-template-columns:1fr 1fr} .surfaces{grid-template-columns:1fr} }
</style>
