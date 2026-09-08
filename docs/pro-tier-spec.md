# Pro AIR — canonical tier spec (LOCKED 2026-06-23)

This is the single source of truth for the Pro tier. `issuer.py` feature
bundles, the pricing page, Stripe prices, and the FlightDeck console gating all
mirror this document. Do not change the tier contents without updating this file
first.

## Pro AIR — $30/month, single seat (was $25 on 2026-09-07, $99 before that; capabilities unchanged)

### Capabilities (entitlement features in `issuer.py`)

- `air-cloud-client`
- `premium-detectors`
- `anchor` — BLAKE3, Ed25519, RFC 3161, Sigstore Rekor
- Audit + Prove (the first two of the APPM pillars: Audit, Prove, Protect, Monitor)
- `evidence-packs` — exportable, third-party verifiable
- `report-nist-ai-rmf`
- hosted FlightDeck, single-operator scope

### Quotas and limits (pricing card)

- 25,000 signed actions / month included — billed on the action, not records
- Overage: soft auto-bill beyond 25k if Stripe metered billing is live;
  otherwise hard-stop with an upgrade prompt
- Retention: 30 days hosted history, cycle-aligned with the monthly meter
  (corrected down from 90)
- Standard storage
- Watermark removed (Free is watermarked and expiring)
- 1 seat

### Retention framing (why 30 days is not thin)

The Rekor anchor is permanent and exported evidence packs are the user's to keep
forever. The 30-day window governs only the hosted, queryable history in
FlightDeck, not the proof itself. Long queryable retention is the Enterprise
sell, where the real obligation lives (HIPAA six-year, EU AI Act Article 12).

### Not in Pro (protects the ladder)

- `report-soc2-ai` -> Enterprise
- Monitor, Protect -> Team and Enterprise
- SIEM (all five: Datadog, Splunk, Sumo Logic, Microsoft Sentinel, Slack) -> Team and up
- multi-seat, dual-control, cohort and fleet scope -> Team
- ML-DSA-65 post-quantum, Agent IAM, dedicated IR -> Enterprise and Air-Gapped

## Implementation deltas (completed 2026-06-23; price figure refreshed 2026-09-08)

These landed with the 1.3.0 tier work. Kept as the record of what changed,
and because item 3 is the standing procedure for every later price change.

1. **`src/vindicara/licensing/issuer.py`** — rebuild `_INDIVIDUAL_FEATURES` to:
   `air-cloud-client`, `premium-detectors`, `anchor`, `audit`, `prove`,
   `evidence-packs`, `report-nist-ai-rmf`, `flightdeck-hosted` (single-operator).
   Remove `report-soc2-ai` from individual. Add the Pro Price ID to
   `_PRICE_TO_PLAN`. Keep `report-soc2-ai`, SIEM, monitor/protect, multi-seat out
   of the individual bundle.
2. **Pricing page (`vindicara-site/src/routes/pricing/+page.svelte`)** — Pro:
   `$45 -> $99` (the figure in the header above is current);
   `1M records/mo -> 25,000 signed actions/mo (billed per action)`;
   `90-day -> 30-day` retention; add "watermark removed", "1 seat"; reflect the
   capability list above; add the retention framing line.
3. **Stripe**, the standing procedure for any Pro price change: create a new
   monthly price at the figure in the header above (plus the metered overage
   component if used), point the Pro Payment Link at it, put the new link in
   `vindicara-site/src/routes/pricing/+page.svelte`, and add the new Price ID to
   `_PRICE_TO_PLAN` *alongside* the outgoing one, never replacing it. Renewal
   invoices carry the Price ID the subscriber originally bought at, and
   `plan_for_price_id` raises on anything unmapped, so deleting a retired ID
   hard-fails license reissue for existing subscribers. A Payment Link never
   exposes its Price ID (the checkout page ships only `plink_...` and the
   display amount), so read the ID off the price in the Stripe Dashboard.
4. **FlightDeck console** — gate surfaces by these features (see the separate
   console-ungating decision: persist entitlement on the Stripe webhook so the
   hosted console reflects the purchase, vs SDK-token-only ungating).
