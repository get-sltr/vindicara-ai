<script>
  import { goto } from '$app/navigation';
  import AppShell from '$components/AppShell.svelte';

  // Stripe Payment Link for Pro ($25/mo, single seat; the Stripe price behind
  // this link must be the $25 one). Fires
  // checkout.session.completed, which the deployed license webhook turns into a
  // signed Pro license token + fulfillment email. See docs/pro-tier-spec.md.
  const PRO_CHECKOUT = 'https://buy.stripe.com/dRm4gy7fk7IwbfO1eT1RC06';
  // Team ($599/mo base; seats + action overage metered as Stripe subscription
  // items). Resolves to price_1TUfSD… -> tier "team" in the license webhook.
  const TEAM_CHECKOUT = 'https://buy.stripe.com/4gMdR8dDI9QEgA88Hl1RC02';
</script>
<svelte:head><title>Project AIR · Pricing</title></svelte:head>

<AppShell active="pricing" title="pricing" scroll>
  <div class="shead">
    <div><div class="eyebrow">Pricing</div><h2>Evidence for what your agents did.</h2></div>
    <span class="sp"></span>
    <p class="lead">Start free on your laptop. Go Pro for your own hosted FlightDeck. Move to Team when proof becomes a group obligation. Regulated, six-year, or sovereign needs live on the next page.</p>
  </div>

  <div class="tiers">

    <div class="tier">
      <div class="tn">Free</div><div class="tl">community · evaluate</div>
      <div class="price">$0</div>
      <div class="appm"><span class="p on">Audit</span><span class="p">Prove</span><span class="p">Protect</span><span class="p">Monitor</span></div>
      <ul>
        <li>Unlimited local capture (open-source CLI)</li>
        <li>All 16 detectors on your own agent</li>
        <li>7-day hosted history, then expires</li>
        <li>Watermarked, no Rekor anchor</li>
        <li>Read-only: see every finding, all actions locked</li>
      </ul>
      <button class="pb" onclick={() => goto('/get-started')}>pip install projectair</button>
    </div>

    <div class="tier feat">
      <div class="tn">Pro</div><div class="tl">individual · self-serve</div>
      <div class="price">$25<span>/mo</span></div>
      <div class="appm"><span class="p on">Audit</span><span class="p on">Prove</span><span class="p">Protect</span><span class="p">Monitor</span></div>
      <ul>
        <li>25,000 signed actions / mo · then $1.50 / 1k</li>
        <li>30-day hosted history · anchor is permanent</li>
        <li>Hosted FlightDeck · single operator (1 seat)</li>
        <li>Anchoring · RFC 3161 + Sigstore Rekor</li>
        <li>Premium detectors</li>
        <li>Evidence packs · yours to keep</li>
        <li>NIST AI RMF report</li>
        <li>Watermark removed</li>
      </ul>
      <a class="pb buy" href={PRO_CHECKOUT}>Get Pro →</a>
    </div>

    <div class="tier">
      <div class="tn">Team</div><div class="tl">prove · watch · intervene</div>
      <div class="price">$599<span>/mo base</span></div>
      <div class="subprice">5 seats + 250k actions / mo · overage $1.50 / 1k · +$99 / seat to 15</div>
      <div class="appm"><span class="p on">Audit</span><span class="p on">Prove</span><span class="p on">Protect</span><span class="p on">Monitor</span></div>
      <ul>
        <li class="plus">Everything in Pro, plus the rest of APPM</li>
        <li>Protect · real-time containment (revoke / quarantine / renew), each sealed as evidence</li>
        <li>Monitor · continuous fleet-wide watch</li>
        <li>Dual-control on the Engage cascade</li>
        <li>Cohort + full-fleet scope</li>
        <li>SIEM · Datadog, Splunk, Sumo Logic, Sentinel, Slack</li>
        <li>Multi-seat workspace · roles · routed alerting</li>
        <li>Admissibility · certified, legal-hold-ready evidence packs</li>
        <li>Fleet-posture / incident report</li>
        <li>1-year hosted history, queryable</li>
      </ul>
      <a class="pb buy" href={TEAM_CHECKOUT}>Start on Team →</a>
      <a class="seclink" href="/contact">or talk to sales</a>
    </div>

  </div>

  <p class="note">An action is one signed step: a tool call, an LLM call, a decision. A typical agent task is dozens. The Rekor anchor and any evidence pack you export are permanent and yours to keep; the hosted-history window only governs what stays queryable in FlightDeck. On Team you export a court-filable evidence pack and certify it yourself (FRE 902); Vindicara puts its own name on the attestation only at Enterprise.</p>

  <a class="next" href="/pricing/enterprise">
    <div>
      <div class="nh">Regulated, six-year retention, or sovereign?</div>
      <div class="nd">Enterprise and Air-gapped · SOC 2, HIPAA, EU AI Act, on your own iron</div>
    </div>
    <span class="na">Enterprise &amp; Air-gapped →</span>
  </a>
</AppShell>

<style>
  .tiers{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
  .tier{background:var(--panel);border:1px solid var(--line);box-shadow:var(--shadow);padding:18px;display:flex;flex-direction:column}
  .tier.feat{border-color:var(--air);box-shadow:0 18px 46px -22px rgba(230,57,70,.5)}
  .tn{font-family:var(--display);font-size:20px;font-weight:600}
  .tl{font-family:var(--mono);font-size:9px;letter-spacing:.1em;text-transform:uppercase;color:var(--white);margin-top:3px;margin-bottom:12px}
  .price{font-family:var(--display);font-size:26px;font-weight:600;margin-bottom:12px}
  .price span{font-family:var(--mono);font-size:11px;color:var(--white);font-weight:400}
  .price.talk{font-size:15px;color:var(--white);font-weight:500}
  .subprice{font-family:var(--mono);font-size:10px;color:var(--white);margin:-8px 0 12px;line-height:1.4}
  .seclink{display:block;text-align:center;font-family:var(--mono);font-size:10px;letter-spacing:.06em;color:var(--white);text-decoration:none;margin-top:8px}
  .seclink:hover{color:var(--white)}
  .appm{display:flex;gap:6px;flex-wrap:wrap;margin:-4px 0 12px}
  .appm .p{font-family:var(--mono);font-size:9px;letter-spacing:.08em;text-transform:uppercase;padding:3px 8px;border:1px solid var(--line);color:var(--white)}
  .appm .p.on{color:var(--white);border-color:var(--air);background:var(--airbg)}
  ul{list-style:none;margin:0 0 4px;padding:0;display:flex;flex-direction:column;gap:9px;flex:1}
  li{font-size:12px;color:var(--white);display:flex;gap:8px;line-height:1.4}
  li::before{content:'›';color:var(--air2);font-weight:700}
  li.plus{color:var(--white);font-weight:600}
  li.plus::before{content:'+';color:var(--air2)}
  .pb{display:block;text-align:center;text-decoration:none;padding:11px;border:1px solid var(--line);font-weight:600;font-size:12px;cursor:pointer;background:none;color:var(--white);margin-top:14px}
  .pb.buy{background:var(--air);color:#fff;border-color:var(--air)}
  .pb.buy:hover{filter:brightness(1.08)}
  .note{font-family:var(--mono);font-size:10.5px;color:var(--white);margin-top:18px;text-align:center;line-height:1.6;max-width:84ch;margin-left:auto;margin-right:auto}
  .next{display:flex;align-items:center;gap:18px;background:var(--airbg);border:1px solid rgba(230,57,70,.28);padding:18px 22px;margin-top:24px;text-decoration:none}
  .next:hover{border-color:var(--air)}
  .nh{font-family:var(--display);font-size:16px;font-weight:600;color:var(--white)}
  .nd{font-size:12px;color:var(--white);margin-top:3px}
  .na{margin-left:auto;font-family:var(--mono);font-size:12px;font-weight:600;color:var(--air2);white-space:nowrap}
  @media (max-width:900px){ .tiers{grid-template-columns:1fr} .next{flex-direction:column;align-items:flex-start;gap:12px} .na{margin-left:0} }
</style>
