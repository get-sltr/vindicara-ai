<script>
  // @ts-nocheck
  import AppShell from '$components/AppShell.svelte';

  const proposals = [
    {
      kicker: 'The accountability gap',
      title: 'Prevention is not proof',
      desc: 'When an autonomous agent acts, most organizations cannot show what it was authorized to do, or that the record was not edited afterward. Our position on why accountability, not just prevention, is the layer that is missing.',
      href: '/blog/ai-agent-accountability-crisis-2026'
    },
    {
      kicker: 'An evidence standard',
      title: 'A baseline for agent actions',
      desc: 'A proposal for treating every consequential agent action as a signed, tamper-evident, independently verifiable record, the bar we believe high-risk deployments should be held to.',
      href: '/structural-verification'
    },
    {
      kicker: 'EU AI Act',
      title: 'Article 72, in practice',
      desc: 'How the record-keeping and logging obligations of the EU AI Act map to a concrete, cryptographically verifiable implementation that exists today, not a policy aspiration.',
      href: '/blog/eu-ai-act-article-72-guide'
    },
    {
      kicker: 'Admissibility',
      title: 'Built to hold up where it counts',
      desc: 'Agent evidence is only useful where decisions get made: an audit, an insurance claim, a courtroom. Designing for US Federal Rules of Evidence 902(13)-(14) from the very first record.',
      href: '/admissibility'
    }
  ];

  const priorities = [
    {
      n: 'Verifiable accountability over assertion',
      d: 'Operators of high-risk agents should be able to show, not state, what their agents did. We map agent behavior against the OWASP Top 10 for Agentic Applications and write tamper-evident records, Signed Intent Capsules, that are signed in the process that took the action and anchored to the public Sigstore Rekor transparency log. A single altered byte breaks verification at the exact record.'
    },
    {
      n: 'Human authority over autonomous action',
      d: 'No consequential action should run without tracing back to a named human. Project AIR binds each action to an authorizing identity through standard OIDC providers, and can halt an agent before it crosses a line a human never approved. Accountability requires a human in the chain of custody, not only a model in the loop.'
    },
    {
      n: 'Open standards and interoperability',
      d: 'Evidence is only valuable if it travels. We build to an open record format and align with the frameworks assessors already use: EU AI Act record-keeping (Articles 12 and 72), NIST AI RMF, and ISO 42001. We support a shared evidence standard so accountability stays portable across tools, vendors, and borders, including when one agent delegates work to another.'
    },
    {
      n: 'Legal and audit admissibility',
      d: 'The purpose of a record is the moment someone has to rely on it. We design agent evidence to be self-authenticating under US Federal Rules of Evidence 902(13)-(14), so an auditor, insurer, or court can act on it without weeks of reconstruction.'
    },
    {
      n: 'Open source and independent verification',
      d: 'Trust should not be a prerequisite for accountability. The core of Project AIR is Apache-2.0-licensed and public on PyPI. We dogfood it: every request to this site is recorded with the same library we ship and anchored to a log anyone can inspect, with zero Vindicara infrastructure in the path.'
    },
    {
      n: 'Honest disclosure',
      d: 'We state what Project AIR does not do as plainly as what it does. Overclaiming the capabilities of accountability tooling is itself a governance risk. Our published coverage is grounded in specific standards, and we label clearly what is shipped, what is in beta, and what is on the roadmap.'
    }
  ];
</script>

<svelte:head>
  <title>Policy · Project AIR — evidence-based governance for AI agents</title>
  <meta name="description" content="Vindicara's policy approach: agent accountability built on tamper-evident, independently verifiable evidence, aligned with the EU AI Act, NIST AI RMF, ISO 42001, and the US Federal Rules of Evidence." />
</svelte:head>

<AppShell active="policy" title="policy" scroll={true}>
  <div class="prose policy">
    <div class="eyebrow2">Policy</div>
    <h1>The rules for autonomous AI agents should be built on evidence.</h1>

    <p class="lead">AI agents are moving out of demos and into production workflows that touch patient records, money movement, and critical infrastructure, faster than the frameworks meant to govern them. Vindicara works with regulators, standards bodies, auditors, and the teams shipping agents to make agent accountability rest on something you can verify, not something you have to take on faith.</p>

    <div class="proposals">
      {#each proposals as p}
        <a class="prop" href={p.href}>
          <div class="pk">{p.kicker}</div>
          <div class="pt">{p.title}</div>
          <div class="pd">{p.desc}</div>
          <div class="pm">Read more →</div>
        </a>
      {/each}
    </div>

    <h2>Philosophy &amp; approach</h2>
    <p>We expect AI agents to run a growing share of the work that matters, and to make consequential decisions without a human watching each step. That is the premise of the technology, and it is not going away. The open question is not whether agents will act on their own. It is whether anyone will be able to prove what they did when it counts.</p>
    <p>Accountability cannot be retrofitted. A log written after the fact, by the same system that may have failed, is not evidence. It can be incomplete, it can be edited, and it asks a regulator or a court to simply trust the operator. We take the opposite position: the record has to be created at the moment of action, signed in the process that took it, anchored to a public transparency log, and bound to the human who authorized it. Then it is evidence anyone can check without trusting us.</p>
    <p>This is why Project AIR ships as open source under the Apache License 2.0. Accountability infrastructure that asks you to trust a black box reproduces the problem it claims to solve. The CLI, the SDK, and the record format are public, and any chain can be verified with no Vindicara infrastructure in the path.</p>
    <p>We also believe the industry should not write these rules alone. Standards bodies, regulators, and the courts set the bar that makes evidence portable and comparable across vendors. Our work is to make sure that bar is technically achievable today, and grounded in how agents actually behave rather than how anyone wishes they did.</p>

    <h2>Our policy priorities</h2>
    <div class="priorities">
      {#each priorities as p, i}
        <div class="prio">
          <div class="ph"><span class="pn">{(i+1).toString().padStart(2,'0')}</span><span class="pname">{p.n}</span></div>
          <p>{p.d}</p>
        </div>
      {/each}
    </div>

    <div class="engage">
      <div class="eh">Working with us</div>
      <p>We work with policymakers, standards organizations, auditors, and enterprises deploying agents in regulated environments. If you are shaping the rules for autonomous AI, or trying to meet the ones that already exist, we would like to help, and we will show you working evidence rather than slides.</p>
      <div class="erow">
        <a class="btn" href="/contact">Talk to our team →</a>
        <a class="btn ghost" href="/design-partner">Become a design partner</a>
      </div>
    </div>
  </div>
</AppShell>

<style>
  .policy h1{font-size:38px;margin:14px 0 0;max-width:20ch;line-height:1.1}
  .eyebrow2{font-family:var(--mono,ui-monospace, SFMono-Regular, Menlo, Consolas, monospace);font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:var(--air2);font-weight:600}
  .lead{font-size:18px;color:var(--white);line-height:1.6;margin:22px 0 8px;font-family:var(--display,'Spectral',Georgia,serif);max-width:64ch}

  .proposals{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:30px 0 12px}
  .prop{display:flex;flex-direction:column;border:1px solid var(--line);background:var(--navy1);padding:20px 22px;text-decoration:none;transition:.18s}
  .prop:hover{border-color:var(--air);transform:translateY(-2px)}
  .prop .pk{font-family:var(--mono,monospace);font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--faint)}
  .prop .pt{font-family:var(--display,'Spectral',serif);font-size:19px;font-weight:600;color:var(--white);margin-top:8px}
  .prop .pd{font-size:13px;color:var(--soft);line-height:1.55;margin-top:10px;flex:1}
  .prop .pm{color:var(--air2);font-size:12.5px;font-weight:600;margin-top:14px}

  .policy h2{font-size:24px;font-weight:700;color:var(--white);margin:42px 0 6px;font-family:var(--display,'Spectral',serif)}
  .policy p{font-size:14.5px;color:var(--soft);line-height:1.65;margin:10px 0;max-width:74ch}

  .priorities{display:grid;grid-template-columns:1fr 1fr;gap:18px 26px;margin-top:14px}
  .prio{border-top:2px solid var(--air);padding-top:12px}
  .prio .ph{display:flex;align-items:baseline;gap:10px}
  .prio .pn{font-family:var(--mono,monospace);font-size:12px;color:var(--air2);font-weight:600}
  .prio .pname{font-family:var(--display,'Spectral',serif);font-size:16px;font-weight:600;color:var(--white)}
  .prio p{font-size:13px;color:var(--soft);line-height:1.55;margin-top:7px;max-width:none}

  .engage{background:linear-gradient(180deg,var(--airbg),transparent);border:1px solid rgba(230,57,70,.4);padding:24px 26px;margin-top:34px;border-radius:4px}
  .engage .eh{font-family:var(--display,'Spectral',serif);font-size:20px;font-weight:700;color:var(--white)}
  .engage p{margin-top:8px}
  .erow{display:flex;gap:12px;flex-wrap:wrap;margin-top:16px}
  .btn{background:var(--air);color:#fff;font-weight:600;font-size:13.5px;padding:11px 18px;border-radius:8px;text-decoration:none}
  .btn:hover{background:var(--air2)}
  .btn.ghost{background:transparent;border:1px solid var(--line);color:var(--white)}
  .btn.ghost:hover{border-color:var(--air2)}

  @media (max-width:860px){ .proposals{grid-template-columns:1fr} .priorities{grid-template-columns:1fr} .policy h1{font-size:30px} }
</style>
