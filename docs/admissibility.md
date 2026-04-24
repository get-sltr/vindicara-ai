---
title: "Admissibility by Design"
subtitle: "How Project AIR produces court-admissible forensic records for AI agents"
description: "The cryptographic architecture behind Project AIR's signed forensic chain, mapped to US Federal Rules of Evidence 901/902/803/1001-1004, EU eIDAS Regulation 910/2014, and EU AI Act Article 72."
---

# Admissibility by Design

**Project AIR™ writes a signed forensic record for every action an AI agent takes. This document maps that record to the evidentiary frameworks a court, regulator, auditor, or insurer will actually apply.**

*Technical documentation, not legal advice. Admissibility is decided by the court hearing the matter. Consult qualified counsel before relying on Project AIR records in any legal proceeding.*

---

## Why this document exists

AI agents take actions at machine speed. When something goes wrong (a wire transfer that should not have happened, a data exfiltration, a customer harmed by a recommendation), the question that matters is not "did the agent misbehave?" It is "can you prove what the agent did, prove the record has not been tampered with, and get that proof accepted as evidence?"

Prevention tools answer "did we try to stop bad things?" They do not answer "what actually happened?" or "can we prove it?"

Project AIR is designed from the ground up so that every agent action produces a record that clears the four bars evidence has to clear to be useful:

1. **Authenticity**: can you prove the record is what you say it is?
2. **Integrity**: can you prove nothing has been altered since it was written?
3. **Attribution**: can you prove which system, and which key holder, produced it?
4. **Procedural admissibility**: does the process that produced the record meet the formal requirements a court, regulator, or auditor will apply?

Project AIR provides cryptographic primitives that satisfy 1, 2, and 3 by construction. Bar 4 is a joint responsibility: Project AIR supplies the architecture and a certification template; the operator supplies the chain of custody. This document explains exactly where that line sits.

---

## The architecture

Every Project AIR record is a **Signed Intent Capsule**, a structured envelope that binds an agent's declared goal, the step taken, the timestamp, and the cryptographic identity of the signer.

The on-disk record shape (AgDR format, v0.2):

```json
{
  "version":      "0.2",
  "step_id":      "UUIDv7, monotonic timestamp prefix",
  "timestamp":    "ISO 8601 UTC",
  "kind":         "llm_start | llm_end | tool_start | tool_end | agent_finish | agent_message",
  "payload":      { "...": "kind-specific contents" },
  "prev_hash":    "hex(BLAKE3 of previous record's canonical payload), or 64 zero chars for genesis",
  "content_hash": "hex(BLAKE3 of this record's canonical payload)",
  "signature":    "hex(Ed25519(prev_hash || content_hash))",
  "signer_key":   "hex(Ed25519 public key), for offline verification"
}
```

Three primitives combine to produce the integrity guarantee:

**BLAKE3 content hashing.** Each record's payload is canonicalised (sorted keys, no extraneous whitespace, UTF-8 encoded) and hashed with BLAKE3 to produce a 256-bit digest. BLAKE3 is a cryptographic hash function with 128-bit collision resistance and 256-bit preimage resistance, specified at the [BLAKE3 reference](https://github.com/BLAKE3-team/BLAKE3-specs). Canonicalisation matters: two parties hashing the same logical payload must produce the same digest. Project AIR uses a deterministic encoding so the hash is reproducible offline.

**Ed25519 digital signatures.** Each record is signed with Ed25519, the EdDSA variant specified in [RFC 8032](https://www.rfc-editor.org/rfc/rfc8032). Ed25519 provides approximately 128 bits of security, produces deterministic signatures (no nonce reuse attack surface), and supports fast batch verification. The signed material is the concatenation `prev_hash || content_hash`, binding each record to its predecessor.

**Forward-chained integrity.** Because each signature covers the previous record's content hash, altering any record in the chain invalidates the signatures of every subsequent record. Verification walks forward from the genesis record; a single broken link surfaces the exact step that was altered, corrupted, or inserted.

The `air` CLI verifies the chain independently of any Project AIR service. Given only the log file and the operator's public key, any party (the operator's SOC, an opposing counsel's expert witness, a regulator, an insurance loss adjuster) can confirm integrity using standard, open-source cryptography. **There is no Project AIR server in the verification loop.** The evidence stands on its own.

---

## Mapping to the United States Federal Rules of Evidence

### FRE 901(a): the general authentication requirement

> "To satisfy the requirement of authenticating or identifying an item of evidence, the proponent must produce evidence sufficient to support a finding that the item is what the proponent claims it is."

Project AIR satisfies this by construction. A record claims to have been produced by the holder of a specific Ed25519 keypair at a specific point in a signed chain. The record's signature, the public key embedded in the record, and the chain linkage together constitute "evidence sufficient to support" that finding. Any verifier can confirm the claim offline.

### FRE 901(b)(9): authentication by process or system

> "Evidence describing a process or system and showing that it produces an accurate result."

Project AIR's logging process is fully documented (see this page, [RFC 8032](https://www.rfc-editor.org/rfc/rfc8032) for Ed25519, the [BLAKE3 specification](https://github.com/BLAKE3-team/BLAKE3-specs), and the [airsdk source](https://github.com/vindicara-inc/projectair/tree/main/packages/projectair)). The process is deterministic: the same inputs produce the same hashes and the same signatures. An expert witness can describe it, demonstrate it, and have their demonstration independently reproduced.

This is the strongest authentication hook for Project AIR. It is also the hook used for almost all machine-generated business records in federal court.

### FRE 902(13): certified records generated by an electronic process or system

Added December 2017. Allows self-authentication of electronic records when accompanied by a qualifying certification:

> "A record generated by an electronic process or system that produces an accurate result, as shown by a certification of a qualified person that complies with the certification requirements of Rule 902(11) or (12)."

This rule exists precisely for systems like Project AIR. A record from a cryptographically integrity-protected log, accompanied by a certification describing the system, is self-authenticating. It does not require a live witness to authenticate.

A **sample certification template for Project AIR records is provided at the end of this document**. Operators should adapt it to their facts and have it signed by a qualified custodian under oath or declaration.

### FRE 803(6): the business records exception to hearsay

> "Records of Regularly Conducted Activity."

Project AIR records are admissible over a hearsay objection when they are created in the regular course of the operator's business, near the time of the events they describe, by (or from information transmitted by) someone with knowledge, and kept in the course of a regularly conducted activity.

This is a procedural bar, not a cryptographic one. To satisfy it, the operator must:

- Deploy Project AIR as part of normal operations, not as a one-off logging instance spun up for litigation.
- Write Project AIR records at the time the agent acts, not reconstructed after the fact.
- Retain records per a documented retention policy.

Project AIR's design assumes this deployment pattern (continuous instrumentation of production agents). Operators who instrument for one-off compliance exercises do not meet the bar.

### FRE 1001-1004: the best evidence rule

FRE 1001(d) defines "original" for electronically stored information as "any printout, or other output readable by sight, if it accurately reflects the information." FRE 1003 makes duplicates admissible to the same extent as originals unless a genuine question is raised about authenticity.

Project AIR's forensic report (`forensic-report.json`) is an accurate, human-readable reflection of the underlying signed chain. The chain itself is the original; the report is a duplicate. Both are admissible under FRE 1003 provided the chain is preserved and verifiable.

---

## Mapping to European and international frameworks

### eIDAS Regulation (EU) No 910/2014: legal effect of electronic signatures

**Article 25(1)** (legal effect):

> "An electronic signature shall not be denied legal effect and admissibility as evidence in legal proceedings solely on the grounds that it is in an electronic form or that it does not meet the requirements for qualified electronic signatures."

Project AIR's Ed25519 signatures qualify as "electronic signatures" under Article 3(10). Under Article 25(1), they cannot be refused admissibility purely because they are electronic.

**Article 26** defines the requirements for **advanced electronic signatures**:

> (a) uniquely linked to the signatory;
> (b) capable of identifying the signatory;
> (c) created using electronic signature creation data that the signatory can, with a high level of confidence, use under their sole control; and
> (d) linked to the data signed therewith in such a way that any subsequent change in the data is detectable.

Project AIR meets requirement (d) by construction (any alteration breaks the chain). Requirements (a), (b), and (c) depend on the operator's key management procedure. If the operator holds the signing key under sole control, documented in a key management policy, Project AIR produces **advanced electronic signatures** as defined by eIDAS.

**Qualified electronic signatures** (Article 3(12), Article 25(2)) have additional legal force equivalent to handwritten signatures under EU law. A qualified signature requires a qualified certificate issued by a **Qualified Trust Service Provider (QTSP)** from the EU Trusted List. Project AIR as shipped does not produce qualified signatures. Operators that require qualified status should obtain a qualified certificate from a QTSP and use it as the signing key. Project AIR is cryptographically agnostic to the source of the Ed25519 key.

### EU AI Act: Article 72 post-market monitoring

Article 72 of the EU AI Act (Regulation (EU) 2024/1689) requires providers of high-risk AI systems to:

> "establish and document a post-market monitoring system in a manner that is proportionate to the nature of the AI technologies and the risks of the high-risk AI system."

The monitoring system must "actively and systematically collect, document and analyse relevant data...on the performance of high-risk AI systems throughout their lifetime."

Project AIR's signed chain is this collection mechanism. Every agent step is recorded, integrity-protected, and verifiable. The `air report --article-72` command produces a post-market monitoring report template populated from the chain (incident timeline, severity roll-up, corrective actions placeholder, signature-integrity attestation). This is covered separately in the Article 72 documentation.

### GDPR Article 30: records of processing activities

Where an AI agent processes personal data, the controller or processor must maintain records of processing activities under Article 30. Project AIR's chain serves as such a record for agent-mediated processing: it documents purpose (user_intent), categories of data (tool arguments and outputs), data processors (agent identities), and timing.

This is not a substitute for a controller's broader Article 30 register. It is evidence that agent-mediated processing was logged, traceable, and verifiable.

### Jurisdictional scope and limitations

The frameworks above (US FRE, EU eIDAS, EU AI Act, GDPR) are the ones Project AIR is most directly designed against. Other jurisdictions have analogous but not identical rules:

- **United Kingdom**: Civil Evidence Act 1995 and the Criminal Procedure Rules apply. Electronic signatures are covered by the Electronic Communications Act 2000. UK eIDAS (as retained EU law post-Brexit) is substantially similar to EU eIDAS.
- **Canada**: Canada Evidence Act ss. 31.1 to 31.8 on electronic documents. Similar authentication framework.
- **Singapore**: Electronic Transactions Act. Evidence Act on computer output.
- **Australia**: Evidence Act 1995 (Cth) Part 2.3 on electronic records.

In all of these, the cryptographic primitives Project AIR uses (Ed25519, BLAKE3, signed hash chains) satisfy the technical bar for authentication. The procedural bars (chain of custody, business records, certification format) vary by jurisdiction and must be handled locally.

**Project AIR does not guarantee admissibility in any specific case.** Courts decide case-by-case based on the facts, the applicable rules, and the quality of the operator's procedural documentation.

---

## Chain of custody: what Project AIR provides and what operators must provide

Admissibility requires more than cryptographic integrity. A court will ask: who had the signing key? Where was the log stored? Who could have tampered with it? Who preserved it between the event and the trial?

Project AIR's cryptographic chain prevents **in-file** tampering. It does **not** prevent **whole-file** substitution or loss. That is the operator's procedural responsibility.

### What Project AIR provides

- **Integrity**: any alteration within a chain breaks verification. Detected deterministically by `air trace`.
- **Authentication**: each record carries the signer's public key. Any party can verify the signature offline.
- **Chain linkage**: each record is cryptographically bound to its predecessor. Records cannot be reordered or silently deleted without detection.
- **Forensic report**: `forensic-report.json` is an auditor-readable artifact that includes verification status, detected findings, and record count.
- **Open-source verifier**: `air trace` and `airsdk.verify_chain` are MIT-licensed. No dependency on Project AIR infrastructure.

### What operators must provide

- **Key management**: who generates the signing key, where it is stored (HSM, KMS, operator laptop), who has access, how it is rotated, how revocation is handled. Document this in a key management policy.
- **Log storage and preservation**: where records are written, what retention policy applies, whether WORM storage is used, how logs are backed up. For high-stakes deployments, operators should write to append-only storage (AWS S3 Object Lock, GCS retention locks, or WORM hardware).
- **Access control**: who can read logs, who can write logs, who can delete logs. Segregation of duties matters here.
- **Timestamp verification (optional, recommended for litigation posture)**: Project AIR's timestamps come from the host clock. For strong timestamp admissibility, operators should countersign chain checkpoints with a [RFC 3161](https://www.rfc-editor.org/rfc/rfc3161) trusted timestamp authority (TSA) or an eIDAS Article 42 qualified timestamp service.
- **Custodian identification**: who is the qualified person (FRE 902(13)) who can sign a certification attesting to the system? Usually a security engineer, compliance officer, or designated records custodian.
- **Deployment regularity**: Project AIR must be running continuously in production for the business-records exception to apply. One-off deployment for litigation defeats FRE 803(6).

Project AIR's default deployment pattern (continuous instrumentation, per-agent or per-operator signing keys, structured log files) satisfies most of these when followed. The responsibility is operator-side because the operator controls their own infrastructure.

---

## Cryptographic primitive references

The security claims in this document depend on the following primitives. Operators relying on Project AIR records as evidence should be familiar with them.

| Primitive | Specification | Security |
|---|---|---|
| Ed25519 (EdDSA) | [RFC 8032](https://www.rfc-editor.org/rfc/rfc8032) | ~128 bits. Deterministic signatures, batch verification, wide deployment (SSH, TLS 1.3, Signal, Git). |
| BLAKE3 | [BLAKE3 specification](https://github.com/BLAKE3-team/BLAKE3-specs) | 128-bit collision resistance, 256-bit preimage resistance. Default 256-bit output. |
| Canonical JSON | [RFC 8785 (JCS)](https://www.rfc-editor.org/rfc/rfc8785) (compatible) | Deterministic encoding: sorted keys, no extraneous whitespace, UTF-8, no floating-point surprises. Reproducible hash inputs. |
| UUIDv7 | [RFC 9562](https://www.rfc-editor.org/rfc/rfc9562) | 48-bit millisecond Unix timestamp prefix, random tail. Timestamp-sortable, globally unique. |

No pre-image attack, collision attack, or signature forgery is known against Ed25519 or BLAKE3 at the time of this writing. Both are conservative, audited, widely deployed choices.

---

## Sample certification template

**The following is a template adapted from the form contemplated by FRE 902(13) and FRE 902(11). Adapt it to your facts. Have it signed by a qualified custodian under oath or declaration. It is not a court filing; it is the declaration that accompanies the Project AIR log when produced as evidence.**

---

> ### Certification of Records Generated by an Electronic Process or System
>
> **Pursuant to Federal Rule of Evidence 902(13) and Rule 902(11)**
>
> I, **[Full Name]**, hereby certify the following:
>
> 1. I am the **[Custodian of Records / Security Engineer / Compliance Officer]** for **[Operator Entity]**. I am a qualified person with personal knowledge of the electronic process and system described below.
>
> 2. The attached records are true and correct copies of records generated by the Project AIR logging system operated by **[Operator Entity]** in the regular course of business.
>
> 3. The records are stored in the **AgDR (AI Decision Record) v0.2 format**, a structured append-only log in which each record contains:
>
>    a. a UUIDv7 step identifier and ISO 8601 timestamp;
>    b. the kind of agent step (``llm_start``, ``llm_end``, ``tool_start``, ``tool_end``, ``agent_finish``, or ``agent_message``);
>    c. a structured payload describing the step;
>    d. the BLAKE3 hash of the preceding record's payload (``prev_hash``);
>    e. the BLAKE3 hash of this record's canonicalised payload (``content_hash``); and
>    f. an Ed25519 digital signature (RFC 8032) over the concatenation of ``prev_hash`` and ``content_hash``, produced with a private key held under sole control of **[Operator Entity]**.
>
> 4. Each record is cryptographically linked to the preceding record by its hash. Any alteration, insertion, deletion, or reordering of records is detected deterministically by signature verification using the open-source Project AIR verifier (``air trace``), which reports the exact record at which the chain breaks.
>
> 5. The records were written at or near the time of the events they describe by the Project AIR instrumentation deployed in the regular course of **[Operator Entity]'s** operations. The records have been retained and preserved according to **[Operator Entity]'s** records retention policy.
>
> 6. The Ed25519 public key corresponding to the signing key used to produce the attached records is:
>
>    ``[64 hex character public key]``
>
> 7. The attached records have been verified using the ``air trace`` command. The verification output is attached as **Exhibit A** to this certification. The chain verified with status **"ok"** for **[N]** records.
>
> 8. The cryptographic primitives used are industry-standard, open, and independently reproducible. Ed25519 is specified in RFC 8032. BLAKE3 is specified in the BLAKE3 reference specification. The Project AIR verifier source code is MIT-licensed and available at https://github.com/vindicara-inc/projectair.
>
> I declare under penalty of perjury under the laws of **[Jurisdiction]** that the foregoing is true and correct.
>
> Executed on **[Date]** at **[Location]**.
>
> \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
> **[Full Name]**
> **[Title]**
> **[Operator Entity]**

---

## Limitations and honest disclosures

1. **Admissibility is case-specific.** No cryptographic architecture guarantees a record will be admitted in any given proceeding. Courts apply the rules to the facts. Project AIR is designed to clear the technical bars; it cannot predetermine a court's ruling.
2. **Timestamps are host-clock timestamps.** For the strongest timestamp admissibility, countersign with a trusted timestamp authority (RFC 3161) or an eIDAS qualified timestamp service.
3. **Project AIR's Ed25519 signatures are "advanced" not "qualified" under eIDAS** as shipped. Operators requiring qualified-signature status must obtain a qualified certificate from a Qualified Trust Service Provider and use that certificate's key as the Project AIR signing key.
4. **Chain of custody is procedural.** Project AIR gives you the cryptographic primitives. You give the chain of custody. Both are required.
5. **Jurisdictional variance.** The mapping in this document is strongest for US federal court (FRE) and EU (eIDAS, AI Act, GDPR). Other jurisdictions have analogous rules; consult local counsel.
6. **Key compromise.** If an operator's signing key is compromised, past signatures remain cryptographically valid (the attacker cannot retroactively forge signatures on historical data they never had). However, records produced after the compromise and before the operator detects and revokes the key may be attacker-controlled. Standard operational security applies: protect the key with an HSM or KMS; rotate regularly; document the rotation schedule.
7. **This document is technical, not legal.** It describes the architecture and its mapping to published evidentiary frameworks. It is not a substitute for advice from counsel qualified in the relevant jurisdiction.

---

## Summary

Project AIR writes a Signed Intent Capsule for every agent action. Each capsule is BLAKE3-hashed, Ed25519-signed, and linked to its predecessor. The chain is tamper-evident by construction, verifiable offline by any party using open-source tools, and designed to clear the technical bars established by FRE 901, 902(13), 803(6), 1001-1004, eIDAS Article 25/26, EU AI Act Article 72, and GDPR Article 30.

The cryptographic primitives are industry-standard, audited, and widely deployed. The verifier is open-source. The certification template is provided. The only thing Project AIR cannot do for you is procedural chain of custody, which depends on your key management and log retention practices.

Admissibility by Design means the architecture does not stand in your way. Everything that could be automated has been. The rest is operations.

---

*Project AIR is maintained by Vindicara. The ``projectair`` package is MIT-licensed. Source code at https://github.com/vindicara-inc/projectair. For questions about this document, contact eng@vindicara.io.*

*Last reviewed: [date]. This document will be updated as rules evolve; subscribe at vindicara.io for notifications.*
