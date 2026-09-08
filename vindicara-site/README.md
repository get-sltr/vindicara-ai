# Vindicara · Project AIR — site

The enterprise redesign of vindicara.io, built in SvelteKit (static SPA, same as the
current deploy). Dark navy / red / white, Spectral + Hanken Grotesk + SF Mono.

Hand this whole folder to Cowork. It can `npm install`, `npm run build`, and deploy the
`build/` output to S3/CloudFront.

## Run and build

```bash
npm install
npm run dev        # http://localhost:5190
npm run build      # static output -> ./build  (deploy this to S3/CloudFront)
npm run preview
npm run check      # svelte-check
```

> Validation already done: all 15 Svelte components compile clean in Svelte 5 runes
> mode. A full `npm run build` should be run once on Cowork's machine; it was not run
> in the authoring sandbox because npm installs were throttled there.

## Structure

```
src/
  app.html                      fonts + shell
  lib/styles/app.css            design tokens, shared classes
  lib/components/
    AppShell.svelte             left product rail + top bar + footer company menu
    HeroMark.svelte             subtle rotating, pointer-aware starburst (SSR-safe)
  routes/
    +layout.svelte / +layout.js prerender + SSR off (static SPA)
    +page.svelte                Vindicara splash (the front door)
    overview/  platform/  evidence/  flightdeck/  pricing/   product screens (fixed)
    admissibility/  about/  blog/  press/  terms/  contact/   content pages (scroll)
```

## Navigation model

- **Left rail** = product: Overview, The platform, Evidence, FlightDeck, Admissibility, Pricing.
- **Footer menu** = company: About, Blog, Press, Terms, Contact.
- The splash (`/`) has no rail. "Enter Project AIR" goes to `/overview`. Clicking the
  brand block in the rail returns to the splash.

## What is real vs placeholder (so nobody overstates it)

- **Blog** links three posts that are live on vindicara.io today; new entries get added to the index.
- **Press** states only verifiable facts (Delaware C-Corp, April 2026, Apache 2.0 OSS, NVIDIA Inception). The releases block is a labeled template. No coverage is invented.
- **Terms** is a structural template with standard headings, clearly marked: it needs a lawyer before publishing.
- **Contact** form validates and confirms in-page; wire it to a real form endpoint or email service (`submit()` in `contact/+page.svelte`).
- Carrier and SIEM names are integrations/targets, not announced partnerships.

## Content decisions baked in (do not regress)

- Hero leads with delegated authority; "signed receipts" is demoted.
- Monitor / Enforce / Prove / Account, with enforcement framed as real enforcement.
- **California AB 316**, not SB 53, cited consistently.
- SIEM list is the canonical five everywhere: Datadog, Splunk, Sumo Logic, Microsoft Sentinel, Slack.
- ForcedLeak shown as before/after; the Claude Mythos incident is removed.
- Detector math stated explicitly: 10 OWASP Agentic + 3 OWASP LLM + 3 AIR-native = 16; ASI04 footnoted as a detector, not "full coverage."
- HIPAA framing is exactly "HIPAA audit trail requirements (45 CFR 164.312(b))."
- Python shown as 3.12+ to match PyPI. Stripe named as processor.
- No em dashes anywhere.
- The "why now" statistics from the old site were dropped on purpose; add them back only with verifiable sources.

## REQUIRED deploy hygiene (from the pressure test — do this with the deploy)

A redesign that still renders unstyled to a cold visitor undercuts everything. Two fixes
belong with the deploy, both in CloudFront, not in this code:

1. **Stop the stale-chunk hydration crash.** Serve `*.html` with `no-cache` (short TTL),
   keep hashed assets in `_app/immutable/` long-cached, retain previous asset hashes for
   at least one deploy instead of hard-purging, and issue a CloudFront invalidation on the
   HTML on every deploy. Optionally add SvelteKit stale-chunk reload recovery in a
   `src/hooks.client.js` `handleError` that reloads on "Failed to fetch dynamically
   imported module."

2. **Add security headers** via a CloudFront response-headers policy: HSTS,
   `X-Content-Type-Options: nosniff`, a frame policy, `Referrer-Policy`, and a baseline CSP.
   A security vendor with an F on securityheaders.io is an easy thing for a diligence
   reviewer to screenshot.

## Open items for a later pass

- Wire FlightDeck to the real console (the separate `projectair-console-sveltekit` build, renamed).
- Replace placeholder blog/press entries with real content.
- Hook the contact form to a real endpoint.
- Legal review of Terms.
