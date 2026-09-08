<script lang="ts">
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import AppShell from '$components/AppShell.svelte';
  import LiveMap from '$components/LiveMap.svelte';

  let { data } = $props();

  // Real PyPI install count: baked at build, refreshed live from the endpoint.
  let installs = $state<number | null>(data?.installsMonth ?? null);
  onMount(async () => {
    try {
      const r = await fetch('/api/live-map');
      if (r.ok) {
        const d = await r.json();
        if (typeof d.installsMonth === 'number' && d.installsMonth > 0) installs = d.installsMonth;
      }
    } catch (_) { /* keep baked value */ }
  });

  let plat = $state<'mac' | 'windows' | 'linux'>('mac');
  let copied = $state('');

  function copy(text: string, key: string) {
    try { navigator.clipboard?.writeText(text); } catch (_) { /* clipboard unavailable */ }
    copied = key;
    setTimeout(() => { if (copied === key) copied = ''; }, 1800);
  }

  const frameworks = [
    { name: 'OpenAI (and any compatible API)', code: 'from airsdk import AIRRecorder\nfrom airsdk.integrations.openai import instrument_openai\n\nrecorder = AIRRecorder("chain.jsonl", user_intent="Draft a report")\nclient = instrument_openai(OpenAI(), recorder)' },
    { name: 'Anthropic', code: 'from airsdk import AIRRecorder\nfrom airsdk.integrations.anthropic import instrument_anthropic\n\nrecorder = AIRRecorder("chain.jsonl", user_intent="Draft a report")\nclient = instrument_anthropic(Anthropic(), recorder)' },
    { name: 'LangChain', code: 'from airsdk import AIRRecorder, AIRCallbackHandler\n\nrecorder = AIRRecorder("chain.jsonl")\nagent.run("task", callbacks=[AIRCallbackHandler(recorder)])' },
    { name: 'Google Gemini', code: 'from airsdk import AIRRecorder, instrument_gemini\n\nrecorder = AIRRecorder("chain.jsonl")\nclient = instrument_gemini(genai.Client(), recorder)' },
    { name: 'LlamaIndex', code: 'from airsdk import AIRRecorder\nfrom airsdk.integrations.llamaindex import instrument_llamaindex\n\nrecorder = AIRRecorder("chain.jsonl")\nllm = instrument_llamaindex(LlamaOpenAI(model="gpt-4o"), recorder)' }
  ];

  const cli = [
    { cmd: 'air demo', desc: 'Run the full demo. A real signed chain in about 30 seconds, no setup.' },
    { cmd: 'air demo --scenario healthcare', desc: 'HIPAA-aligned clinical AI demo.' },
    { cmd: 'air trace chain.jsonl', desc: 'Replay a chain, verify signatures, run detectors, export a report.' },
    { cmd: 'air verify-public chain.jsonl', desc: 'Verify using only public infrastructure, zero Vindicara calls.' },
    { cmd: 'air explain --finding ASI02', desc: 'Plain-language causal explanation for one finding.' },
    { cmd: 'air verify-intent chain.jsonl', desc: 'Did the agent actually do what it declared it would?' },
    { cmd: 'air report article72', desc: 'Generate an EU AI Act Article 72 report.' }
  ];

  function term(p: string) { return p === 'windows' ? 'PowerShell' : 'Terminal'; }
</script>

<svelte:head>
  <title>Project AIR · Get started</title>
  <meta name="description" content="Install Project AIR and produce your first signed forensic report in minutes. A plain-language, step-by-step guide for macOS, Windows, and Linux, written for people who do not write code." />
</svelte:head>

<AppShell active="get-started" title="get started" scroll={true} dots={false}>
  <LiveMap />
  {#if installs}
    <p class="gs-installs" style="text-align:center;font-family:var(--mono,ui-monospace, SFMono-Regular, Menlo, Consolas, monospace);font-size:12px;letter-spacing:.05em;color:#9aa6bd;margin:0 0 14px;opacity:.9">{installs.toLocaleString()} installs in the last 30 days · Apache 2.0 · on PyPI</p>
  {/if}
  <div class="gs">
    <header class="ghead reveal">
      <div class="eyebrow">Get started</div>
      <h1>Your first signed forensic report, one step at a time.</h1>
      <p class="lead">This guide assumes no coding experience. If you can copy a line of text and paste it, you can produce a real, cryptographically signed evidence chain on your own computer. Nothing is sent to us. Everything runs locally.</p>
      <div class="picker" role="tablist" aria-label="Operating system">
        <button class:on={plat === 'mac'} onclick={() => plat = 'mac'} role="tab" aria-selected={plat === 'mac'}>macOS</button>
        <button class:on={plat === 'windows'} onclick={() => plat = 'windows'} role="tab" aria-selected={plat === 'windows'}>Windows</button>
        <button class:on={plat === 'linux'} onclick={() => plat = 'linux'} role="tab" aria-selected={plat === 'linux'}>Linux</button>
      </div>
      <p class="hint">Pick your computer above. The instructions below update to match it.</p>
    </header>

    <section class="explain reveal">
      <h2>What you are about to do, in plain words</h2>
      <div class="cards">
        <div class="card xc"><div class="cn">1. Install a tool called <span class="air">AIR</span></div><p>A small, free, open-source program. You install it once. It adds a command named <code>air</code> to your computer.</p></div>
        <div class="card xc"><div class="cn">2. Run a built-in demo</div><p>One command, <code>air demo</code>, creates a realistic record of an AI agent doing something dangerous, and signs every step.</p></div>
        <div class="card xc"><div class="cn">3. Read the evidence</div><p>You get a tamper-evident file showing exactly what happened, in order, signed so no one can quietly change it later.</p></div>
      </div>
      <p class="note">Project AIR ships 16 detectors (10 OWASP Agentic, 3 OWASP LLM, 3 AIR-native). The demo runs the detectors that work fully offline; two NemoGuard detectors need an NVIDIA NemoGuard NIM and stay off in the demo.</p>
    </section>

    <!-- STEP 0 -->
    <section class="step reveal">
      <div class="sh"><span class="badge">0</span><h2>Open a terminal</h2></div>
      <p class="sp">A terminal is a window where you type commands instead of clicking buttons. It looks intimidating; it is just a text box. Here is how to open it.</p>
      {#if plat === 'mac'}
        <ol class="steps">
          <li>Press <kbd>Command</kbd> and the <kbd>Space</kbd> bar together. A search box appears.</li>
          <li>Type the word <b>Terminal</b>.</li>
          <li>Press <kbd>Return</kbd>. A window opens. That is your terminal.</li>
        </ol>
      {:else if plat === 'windows'}
        <ol class="steps">
          <li>Click the <b>Start</b> menu (the Windows icon, bottom left).</li>
          <li>Type the word <b>PowerShell</b>.</li>
          <li>Click <b>Windows PowerShell</b> in the results. A blue window opens. That is your terminal.</li>
        </ol>
      {:else}
        <ol class="steps">
          <li>On most desktops, press <kbd>Ctrl</kbd> <kbd>Alt</kbd> <kbd>T</kbd> together.</li>
          <li>Or open your applications menu and search for <b>Terminal</b>.</li>
          <li>A window opens. That is your terminal.</li>
        </ol>
      {/if}
      <p class="tip">Tip: to run any command below, click <b>Copy</b>, click inside your terminal window, paste (<kbd>{plat === 'mac' ? 'Command' : 'Ctrl'}</kbd> <kbd>V</kbd>), then press <kbd>{plat === 'windows' ? 'Enter' : 'Return'}</kbd>.</p>
    </section>

    <!-- STEP 1 -->
    <section class="step reveal">
      <div class="sh"><span class="badge">1</span><h2>Make sure you have Python 3.12 or newer</h2></div>
      <p class="sp">Project AIR runs on Python, a free programming language your computer may already have. First, check. Copy this line into your terminal and press enter.</p>
      {@render cmd(plat === 'windows' ? 'python --version' : 'python3 --version', 'pyver')}
      <p class="sp">If you see a number like <code>Python 3.12.4</code> or higher, you are set. Skip to Step 2. If you see an error, or a number below 3.12, install Python:</p>
      {#if plat === 'mac'}
        <div class="opt"><div class="ol">Easiest</div><p>Install <a href="https://brew.sh" target="_blank" rel="noopener">Homebrew</a> if you do not have it, then run:</p></div>
        {@render cmd('brew install python@3.13', 'pyinst')}
        <p class="sp">Or download the official installer from <a href="https://www.python.org/downloads/macos/" target="_blank" rel="noopener">python.org/downloads/macos</a> and double-click it.</p>
      {:else if plat === 'windows'}
        <div class="opt"><div class="ol">Easiest</div><p>In your terminal, run:</p></div>
        {@render cmd('winget install Python.Python.3.13', 'pyinst')}
        <p class="sp">Or download the installer from <a href="https://www.python.org/downloads/windows/" target="_blank" rel="noopener">python.org/downloads/windows</a>. When it runs, check the box that says <b>Add Python to PATH</b> before clicking Install. This matters.</p>
      {:else}
        <div class="opt"><div class="ol">Ubuntu or Debian</div></div>
        {@render cmd('sudo apt update && sudo apt install python3 python3-pip python3-venv', 'pyinst')}
        <div class="opt"><div class="ol">Fedora or RHEL</div></div>
        {@render cmd('sudo dnf install python3 python3-pip', 'pyinst2')}
      {/if}
    </section>

    <!-- STEP 2 -->
    <section class="step reveal">
      <div class="sh"><span class="badge">2</span><h2>Install Project AIR</h2></div>
      <p class="sp">We recommend a tool called <b>pipx</b>, which installs the <code>air</code> command cleanly without touching anything else on your computer. First install pipx:</p>
      {#if plat === 'mac'}
        {@render cmd('brew install pipx && pipx ensurepath', 'pipx')}
      {:else if plat === 'windows'}
        {@render cmd('python -m pip install --user pipx', 'pipx')}
        {@render cmd('python -m pipx ensurepath', 'pipx2')}
        <p class="tip">After running <code>ensurepath</code>, close your terminal and open a fresh one before continuing.</p>
      {:else}
        {@render cmd('python3 -m pip install --user pipx', 'pipx')}
        {@render cmd('python3 -m pipx ensurepath', 'pipx2')}
      {/if}
      <p class="sp">Now install Project AIR itself:</p>
      {@render cmd('pipx install projectair', 'install')}
      <details class="dd">
        <summary>Already comfortable with Python? Use pip instead.</summary>
        <p class="sp">Inside a virtual environment or project, you can run <code>pip install projectair</code>. The package name on PyPI is <code>projectair</code>; the command it gives you is <code>air</code>.</p>
        {@render cmd('pip install projectair', 'pip')}
      </details>
    </section>

    <!-- STEP 3 -->
    <section class="step reveal">
      <div class="sh"><span class="badge">3</span><h2>Check that it worked</h2></div>
      <p class="sp">Ask the tool for its version. You should see a version number, not an error.</p>
      {@render cmd('air --version', 'ver')}
      <p class="sp">Now run the demo. This is the moment it all becomes real.</p>
      {@render cmd('air demo', 'demo')}
      <div class="termout">
        <div class="tb"><span class="d r"></span><span class="d y"></span><span class="d g"></span><span class="tl">{term(plat)}</span></div>
        <div class="tbody">
          <div class="ln"><span class="pr">{plat === 'windows' ? 'PS&gt;' : '$'}</span> air demo</div>
          <div class="muted">[AIR] Generating signed forensic chain...</div>
          <div class="muted">[AIR] Detectors evaluated. Findings recorded.</div>
          <div class="ok">[AIR] Chain verified. Report saved to forensic-report.json</div>
        </div>
      </div>
      <p class="sp">If you see that last green line, congratulations. You just generated and verified a real signed evidence chain. No account, no internet required, no configuration.</p>
    </section>

    <!-- STEP 4 -->
    <section class="step reveal">
      <div class="sh"><span class="badge">4</span><h2>Read what you produced</h2></div>
      <p class="sp">The demo wrote two files into the folder your terminal is currently in: a chain file and a report. Open the report to see a plain summary of what the agent did and what was flagged.</p>
      {@render cmd(plat === 'windows' ? 'notepad forensic-report.json' : 'open forensic-report.json', 'open')}
      <p class="sp">Want to prove the chain has not been tampered with, using only public infrastructure? Run:</p>
      {@render cmd('air verify-public chain.jsonl', 'vp')}
      <p class="note">Every record is hashed with BLAKE3 and signed with Ed25519 in-process, at the moment the action happens. Change any step after the fact and verification fails. That is what makes it evidence rather than a log.</p>
    </section>

    <!-- OPTIONAL: FOR BUILDERS -->
    <section class="step reveal builders">
      <div class="sh"><span class="badge alt">+</span><h2>Optional: record your own AI agent</h2></div>
      <p class="sp">This part is for people who write code. If that is not you, you are already done; the steps above are the whole guide. If you do build agents, instrumenting one is a few lines.</p>
      <p class="sub">The manual way. Wrap your agent's actions with a recorder:</p>
      <div class="codeblock">
        <pre>from airsdk import AIRRecorder

recorder = AIRRecorder("chain.jsonl")

recorder.llm_start(prompt="Analyze this data...")
recorder.llm_end(response="Here is the analysis...")

recorder.tool_start(tool_name="db_query", tool_args=&#123;"sql": "SELECT ..."&#125;)
recorder.tool_end(tool_output="42 rows returned")

recorder.agent_finish(final_output="Task complete")</pre>
      </div>
      <p class="sub">Already using a framework? One line connects it. Same signed chain, no boilerplate.</p>
      <div class="fwgrid">
        {#each frameworks as fw}
          <div class="fw"><div class="fwn">{fw.name}</div><pre>{fw.code}</pre></div>
        {/each}
      </div>
      <p class="note">Any OpenAI-compatible endpoint also works through <code>instrument_openai</code>, including NVIDIA NIM, vLLM, Together AI, Groq, and Fireworks.</p>
    </section>

    <!-- CLI REFERENCE -->
    <section class="step reveal">
      <div class="eyebrow">Command reference</div>
      <h2 class="rh">The commands worth knowing</h2>
      <div class="clilist">
        {#each cli as c}
          <div class="clirow"><code>{c.cmd}</code><span>{c.desc}</span></div>
        {/each}
      </div>
    </section>

    <!-- TROUBLESHOOTING -->
    <section class="step reveal">
      <div class="eyebrow">Troubleshooting</div>
      <h2 class="rh">If something goes wrong</h2>
      <div class="ts">
        <div class="tsi">
          <h3><code>air</code>: command not found</h3>
          {#if plat === 'windows'}
            <p>Close your terminal and open a new one after <code>pipx ensurepath</code>. If it still fails, run <code>python -m projectair.cli demo</code> instead.</p>
          {:else if plat === 'mac'}
            <p>Run <code>pipx ensurepath</code>, then close and reopen your terminal. As a fallback, run <code>python3 -m projectair.cli demo</code>.</p>
          {:else}
            <p>Run <code>pipx ensurepath</code> and reopen your terminal, or add <code>~/.local/bin</code> to your PATH. Fallback: <code>python3 -m projectair.cli demo</code>.</p>
          {/if}
        </div>
        <div class="tsi">
          <h3>Python version too old</h3>
          <p>Project AIR needs Python 3.12 or newer. Check with <code>{plat === 'windows' ? 'python' : 'python3'} --version</code>. If you have several versions, target one explicitly, for example <code>python3.13 -m pip install projectair</code>.</p>
        </div>
        <div class="tsi">
          <h3>Permission errors during install</h3>
          {#if plat === 'windows'}
            <p>Avoid running as Administrator for installs. Prefer pipx, which isolates the install for you. As a fallback, <code>pip install --user projectair</code>.</p>
          {:else}
            <p>Never use <code>sudo pip install</code>. Use pipx, or create a virtual environment: <code>python3 -m venv .venv && source .venv/bin/activate && pip install projectair</code>.</p>
          {/if}
        </div>
        <div class="tsi">
          <h3>Still stuck</h3>
          <p>Open an issue on <a href="https://github.com/vindicara-inc/projectair/issues" target="_blank" rel="noopener">GitHub</a>, or email <a href="mailto:support@vindicara.io">support@vindicara.io</a>. Tell us your operating system and paste the exact error.</p>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="cta reveal">
      <div class="seal"><span class="sk">AIR</span></div>
      <div class="ct">
        <h2>That is the whole loop. Detect, sign, prove.</h2>
        <p class="lead">Read the full documentation and architecture on GitHub, or talk to us about putting signed evidence behind your production agents.</p>
        <div class="ctab">
          <a class="btn" href="https://github.com/vindicara-inc/projectair#readme" target="_blank" rel="noopener">Read the docs</a>
          <button class="btn ghost" onclick={() => goto('/design-partner')}>Become a design partner</button>
        </div>
      </div>
    </section>
  </div>
</AppShell>

{#snippet cmd(text: string, key: string)}
  <button class="cmd" onclick={() => copy(text, key)} title="Click to copy">
    <span class="cl"><span class="pr">{plat === 'windows' ? 'PS&gt;' : '$'}</span> {text}</span>
    <span class="cc">{copied === key ? 'Copied' : 'Copy'}</span>
  </button>
{/snippet}

<style>
  .gs{max-width:880px;margin:0 auto;padding-bottom:40px}
  .ghead h1{font-size:38px;margin:14px 0 0;max-width:20ch}
  .ghead .lead{font-size:15.5px;margin-top:16px;max-width:64ch}
  .picker{display:flex;gap:8px;margin-top:24px}
  .picker button{font-family:var(--mono);font-size:11.5px;letter-spacing:.08em;text-transform:uppercase;padding:9px 16px;background:transparent;color:var(--soft);border:1px solid var(--line);cursor:pointer;transition:.14s}
  .picker button:hover{color:var(--white);border-color:var(--white)}
  .picker button.on{background:var(--air);color:#fff;border-color:var(--air)}
  .hint{font-family:var(--mono);font-size:11px;color:var(--faint);margin-top:10px}

  .explain{margin-top:40px}
  .explain h2{font-size:22px;margin-bottom:16px}
  .cards{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
  .xc{padding:18px}
  .xc .cn{font-family:var(--display);font-size:15px;font-weight:600;margin-bottom:8px}
  .xc p{font-size:12.5px;color:var(--soft);line-height:1.55}
  .note{font-family:var(--mono);font-size:11px;color:var(--faint);line-height:1.7;margin-top:16px;border-left:2px solid var(--air);padding-left:14px}

  .step{margin-top:44px}
  .sh{display:flex;align-items:center;gap:14px;margin-bottom:14px}
  .badge{flex:none;width:34px;height:34px;display:grid;place-items:center;background:var(--air);color:#fff;font-family:var(--mono);font-weight:700;font-size:15px}
  .badge.alt{background:var(--panel);color:var(--air2);border:1px solid var(--air)}
  .sh h2{font-size:23px}
  .sp{font-size:14px;color:var(--soft);line-height:1.7;margin:10px 0}
  .sub{font-size:13.5px;color:var(--white);font-weight:600;margin:18px 0 10px}
  .steps{margin:8px 0 8px 4px;padding:0;list-style:none;counter-reset:s}
  .steps li{position:relative;padding:7px 0 7px 30px;font-size:14px;color:var(--soft);line-height:1.6;counter-increment:s}
  .steps li::before{content:counter(s);position:absolute;left:0;top:7px;width:20px;height:20px;display:grid;place-items:center;font-family:var(--mono);font-size:10px;color:var(--air2);border:1px solid var(--line)}
  .tip,.opt p{font-size:13px;color:var(--soft);line-height:1.6}
  .tip{background:var(--airbg);border:1px solid rgba(230,57,70,.28);padding:12px 14px;margin-top:12px;font-size:13px}
  .opt{margin-top:14px}
  .opt .ol{font-family:var(--mono);font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--air2);margin-bottom:4px}

  kbd{font-family:var(--mono);font-size:11px;background:var(--raise);border:1px solid var(--line);border-bottom-width:2px;padding:1px 6px;color:var(--white)}
  code{font-family:var(--mono);font-size:12.5px;color:var(--air2);background:rgba(0,0,0,.3);padding:1px 5px}
  a{color:var(--air2);text-decoration:none;border-bottom:1px solid transparent}
  a:hover{border-bottom-color:var(--air2)}

  .cmd{display:flex;width:100%;align-items:center;justify-content:space-between;gap:12px;background:#080d1a;border:1px solid var(--line);padding:12px 14px;margin:10px 0;cursor:pointer;text-align:left;transition:.14s}
  .cmd:hover{border-color:rgba(230,57,70,.45)}
  .cmd .cl{font-family:var(--mono);font-size:13px;color:var(--white);word-break:break-all}
  .cmd .pr{color:var(--air2);margin-right:8px}
  .cmd .cc{font-family:var(--mono);font-size:10.5px;color:var(--faint);flex:none}

  .termout{margin:12px 0;border:1px solid var(--line);background:#080d1a}
  .tb{display:flex;align-items:center;gap:7px;padding:9px 14px;border-bottom:1px solid var(--line2)}
  .tb .d{width:10px;height:10px;border-radius:50%}
  .tb .d.r{background:#ff5f56}.tb .d.y{background:#ffbd2e}.tb .d.g{background:#27c93f}
  .tb .tl{font-family:var(--mono);font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--faint);margin-left:8px}
  .tbody{padding:14px;font-family:var(--mono);font-size:12.5px;line-height:1.8}
  .tbody .ln{color:var(--white)} .tbody .pr{color:var(--air2);margin-right:8px}
  .tbody .muted{color:var(--faint)} .tbody .ok{color:var(--good)}

  .dd{margin-top:14px;border:1px solid var(--line);background:var(--navy1);padding:12px 16px}
  .dd summary{font-size:13px;color:var(--soft);cursor:pointer;font-weight:600}
  .dd summary:hover{color:var(--white)}

  .codeblock{background:#080d1a;border:1px solid var(--line);padding:16px;overflow-x:auto;margin:8px 0}
  .codeblock pre{font-family:var(--mono);font-size:12.5px;line-height:1.7;color:var(--soft);white-space:pre}
  .fwgrid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
  .fw{border:1px solid var(--line);background:var(--navy1);padding:14px}
  .fw .fwn{font-family:var(--display);font-size:14px;font-weight:600;margin-bottom:8px}
  .fw pre{font-family:var(--mono);font-size:11px;line-height:1.6;color:var(--soft);white-space:pre-wrap;word-break:break-word}

  .rh{font-size:22px;margin:8px 0 16px}
  .clilist{border:1px solid var(--line)}
  .clirow{display:flex;gap:16px;align-items:baseline;padding:12px 16px;border-bottom:1px solid var(--line2)}
  .clirow:last-child{border-bottom:0}
  .clirow code{flex:0 0 250px;background:none;padding:0;color:var(--air2)}
  .clirow span{font-size:13px;color:var(--soft);line-height:1.5}

  .ts{display:grid;grid-template-columns:1fr 1fr;gap:18px}
  .tsi h3{font-family:var(--ui);font-size:14px;font-weight:700;margin-bottom:6px;color:var(--white)}
  .tsi p{font-size:13px;color:var(--soft);line-height:1.6}

  .cta{margin-top:48px;display:flex;gap:20px;align-items:center;background:var(--panel);border:1px solid var(--line);box-shadow:var(--shadow);padding:26px}
  .cta .ct h2{font-size:22px;margin-bottom:8px}
  .cta .lead{font-size:14px;max-width:60ch}
  .ctab{display:flex;gap:12px;margin-top:18px;flex-wrap:wrap}

  @media (max-width:1080px){
    .ghead h1{font-size:30px}
    .cards,.fwgrid,.ts{grid-template-columns:1fr}
    .clirow{flex-direction:column;gap:4px} .clirow code{flex:none}
    .cta{flex-direction:column;align-items:flex-start}
  }
</style>
