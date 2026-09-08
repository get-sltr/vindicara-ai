# Licensing and tiers

`projectair` (the `air` CLI and the `airsdk` library) is published under the
[Apache License 2.0](LICENSE) from 1.4.0; versions through 1.3.1 remain MIT on PyPI.
Apache 2.0 is as permissive as MIT and adds an explicit patent grant, and it is the
license the Vindicara engine already uses, so the whole repository is under one license.
Read it, build it, run it in production, verify records with it, fork it.

What Vindicara sells is the hosted product and the artifacts around the record, the
same open-core split Langfuse and LangSmith use:

| Tier | Price | What it adds |
|---|---|---|
| Free | $0 | Everything in this package, on your own machine, forever: capture, signing, all 16 detectors, `air trace`, `air watch`, `air explain`, `air incident`, `air health`, every integration. |
| Pro | US $25 / month, single seat | Hosted FlightDeck, permanent RFC 3161 + Sigstore Rekor anchoring, evidence and incident packs, premium detectors, NIST AI RMF report. |
| Team | US $599 / month base | Five seats, 250k signed actions / month, one-year retention, SIEM export, alert routing, shared workspace. |
| Enterprise | Talk to us | Self-hosted or air-gapped unit, six-year retention, SSO / RBAC, BAA. |

The pricing page at [vindicara.io/pricing](https://vindicara.io/pricing) is the source of
truth; `air upgrade` mirrors it. The paid features ship in `projectair-pro` (`airsdk_pro`),
which carries its own commercial license and is not on PyPI. Questions: licensing@vindicara.io.
