---
title: "Responsible Security Disclosure Policy"
subtitle: "Vindicara, Inc. · Project AIR™"
last_updated: "2026-04-22"
effective_date: "2026-04-22"
version: "1.0"
---

# Responsible Security Disclosure Policy

> **Version 1.0 · Draft under counsel review.** This document provides safe-harbor protections for good-faith security researchers investigating Vindicara systems and the Project AIR™ codebase.

**Effective Date:** April 22, 2026
**Last Updated:** April 22, 2026

---

## 1. Commitment

**Vindicara, Inc.** ("**Vindicara**") takes the security of its products and users seriously. Project AIR™ is a security product that produces evidence used in real legal, regulatory, and insurance proceedings; a vulnerability in Vindicara's systems directly impacts customers and the parties who rely on their records. We welcome coordinated, good-faith security research into our systems and the Project AIR™ codebase.

This Responsible Security Disclosure Policy ("**Policy**") describes:
- What systems are in scope for security research.
- How to report a suspected vulnerability.
- What we promise in exchange for good-faith, responsible disclosure (the "**safe harbor**").
- Our process and timeline for response.

This Policy does not modify the Terms of Service or the Acceptable Use Policy except as expressly stated.

## 2. Scope

### 2.1 In Scope

The following are in scope for security research under this Policy:

- The Vindicara website at https://vindicara.io and all subdomains under vindicara.io.
- The Vindicara API endpoints used by the AIR Cloud / Team Tier.
- The Vindicara dashboard (when generally available).
- The `projectair` Python package distributed on PyPI, including the `air` CLI and the `airsdk` library.
- The Project AIR™ source code hosted at https://github.com/get-sltr/vindicara-ai.
- Published cryptographic design and primitives as described in the Admissibility by Design architecture document at https://vindicara.io/admissibility/.

### 2.2 Out of Scope

The following are explicitly out of scope. Testing against these is not protected under this Policy and may violate law, third-party terms, or the Acceptable Use Policy:

- Any system operated by a Vindicara customer, including customer-hosted AIR deployments and customer-managed agent traces. Customer systems are not Vindicara's to authorize testing on.
- Third-party services and infrastructure used by Vindicara (AWS, Square, GitHub, PyPI, Cloudflare, email providers, analytics providers, etc.). Research those systems through the third party's own security-disclosure program.
- Open-source dependencies of the Services (e.g., `cryptography`, `blake3`, `pydantic`, `typer`, `PyYAML`, `langchain-core`, `fpdf2`, `anthropic`, `openai`). Report those upstream.
- The physical, network, and corporate infrastructure of Vindicara or any Vindicara employee, including employee devices, homes, and personal accounts.
- Social engineering attacks against Vindicara employees, customers, or partners.
- Denial of service (DoS), distributed denial of service (DDoS), or any form of volumetric or resource-exhaustion attack.
- Spam, phishing, or mass-email campaigns directed at any party.

### 2.3 Low-Severity Findings

The following categories are generally considered low-severity or non-reportable. Vindicara appreciates the research effort, but these findings typically will not receive acknowledgment beyond a polite note:

- Missing security headers without a demonstrated exploit (e.g., missing `X-Content-Type-Options` where no content-sniffing risk exists).
- Outdated software versions with no demonstrable vulnerability affecting the deployed configuration.
- TLS configuration issues that do not enable an active attack (e.g., support for an older cipher that is not actively exploitable).
- Rate-limiting absence on endpoints that do not meaningfully affect availability or cost.
- CSRF on actions that do not cause meaningful state change (e.g., logout).
- Issues only reproducible in unsupported or heavily customized browser configurations.
- Publicly exposed but intended-to-be-public information (e.g., `security.txt`, `humans.txt`, OSS source code).
- Self-XSS that requires the victim to paste code into the browser console.
- Issues in third-party libraries where Vindicara is not the vulnerable component.

## 3. Safe Harbor

### 3.1 Commitment

Vindicara commits, subject to the conditions in Section 3.2, that we will not:

- Initiate or support legal action against you for good-faith security research conducted within the scope and rules of this Policy, including under the U.S. Computer Fraud and Abuse Act (CFAA), the U.S. Digital Millennium Copyright Act (DMCA) anti-circumvention provisions, California Penal Code § 502, the UK Computer Misuse Act 1990, the EU Directive on Attacks Against Information Systems (2013/40/EU), or analogous laws in any jurisdiction.
- File complaints with your employer or university unless you ask us to.
- Disclose your identity or contact information to third parties (including law enforcement) without a legal requirement or your explicit consent.

### 3.2 Conditions

The safe harbor applies only if you:

(a) Conduct your research in good faith for the purpose of identifying and reporting vulnerabilities.

(b) Stay within the scope defined in Section 2.1 and avoid activities listed as out of scope in Section 2.2.

(c) Do not access, modify, exfiltrate, retain, or destroy more data than is reasonably necessary to demonstrate the vulnerability.

(d) Do not access, store, transmit, or share the Personal Information of any third party beyond what is reasonably necessary to demonstrate the vulnerability. Redact or hash any sensitive data in your report.

(e) Do not intentionally degrade the performance, reliability, or availability of the Services.

(f) Do not publicly disclose the vulnerability before Vindicara has had a reasonable opportunity to investigate and remediate, subject to Section 5.

(g) Do not use the vulnerability to extort, blackmail, pressure, or coerce Vindicara or any other party.

(h) Do not violate applicable law.

(i) Report the vulnerability to Vindicara through the channel in Section 4.

If you are uncertain whether a particular activity is covered, **ask first** by emailing **security@vindicara.io**.

### 3.3 Limitations

This safe harbor is a commitment from Vindicara to you. It does not, and cannot, bind:

- Third parties whose systems you may incidentally touch.
- Law-enforcement agencies or prosecutors who may independently decide to investigate activity.
- Civil claimants who may allege harm from your research.

**You remain responsible for complying with applicable law.** The safe harbor does not create an attorney-client relationship, does not constitute legal advice, and does not guarantee immunity from investigation or prosecution by third parties.

## 4. How to Report

### 4.1 Reporting Channel

Report suspected vulnerabilities to **security@vindicara.io**. PGP-encrypted email is encouraged for sensitive reports; our public key is available at https://vindicara.io/security.txt (when published) or on request.

If security@vindicara.io is unreachable or if the vulnerability involves a risk you believe is imminent and severe, contact **Kevin.Minn@vindicara.io** directly.

### 4.2 What to Include

A useful report includes:

1. **Summary.** One or two sentences describing the issue.
2. **Affected component.** Which URL, endpoint, package version, or source file.
3. **Reproduction steps.** A clear, minimal, step-by-step reproduction.
4. **Impact.** What an attacker can do with the vulnerability, with a realistic impact assessment.
5. **Suggested remediation.** Optional but appreciated.
6. **Your contact information** and preferred name for acknowledgment (or "anonymous").
7. **Any evidence** (screenshots, HTTP captures, minimal code) that supports the report. Redact personal data where possible.

### 4.3 Language

Reports may be submitted in English. Vindicara will respond in English.

## 5. Vindicara's Response Process

### 5.1 Acknowledgment

Vindicara will acknowledge receipt of your report within **three (3) business days** by email.

### 5.2 Triage

Within **ten (10) business days** of acknowledgment, Vindicara will provide an initial triage assessment, including:

- Whether the report is in scope.
- The initial severity assessment (Critical / High / Medium / Low / Informational).
- Estimated remediation timeline.
- Follow-up questions, if any.

### 5.3 Remediation

Vindicara will use commercially reasonable efforts to remediate confirmed vulnerabilities on the following target timeline, measured from the triage assessment:

| Severity | Target Remediation |
|---|---|
| Critical | 14 days |
| High | 30 days |
| Medium | 60 days |
| Low | 90 days |

These targets are aspirational. Actual timelines depend on complexity, dependencies, and operational constraints. Vindicara will keep you informed of progress.

### 5.4 Coordinated Disclosure

Vindicara practices **90-day coordinated disclosure**. After you report a vulnerability, we will work with you to agree on a disclosure timeline. Our default is:

- Quiet period: 90 days from acknowledgment.
- Public disclosure: Vindicara will publish a security advisory (CVE where appropriate, GitHub Security Advisory for the `projectair` repository) at or before the agreed disclosure date.
- You may publish your own disclosure coordinated with Vindicara's advisory, crediting Vindicara's response where appropriate.

If a vulnerability is being actively exploited in the wild or presents an imminent risk to user safety, we may accelerate disclosure. If Vindicara needs more than 90 days (for example, due to complex upstream dependencies or deployment constraints), we will discuss an extension with you in good faith.

### 5.5 Acknowledgment and Recognition

Vindicara will credit researchers who report valid, in-scope vulnerabilities in:

- The security advisory for the vulnerability.
- A hall of fame or acknowledgments page on vindicara.io (when published), with your consent.

You may also request anonymity.

## 6. Bug Bounty

Vindicara **does not currently operate a paid bug bounty program**. This Policy provides safe-harbor protections and public acknowledgment but not monetary rewards. Vindicara reserves the right to establish a paid bounty program in the future, and this Policy does not promise retroactive payment for prior reports.

## 7. Contact

Vindicara, Inc.
Reporting: **security@vindicara.io**
Direct (if security@ unreachable): **Kevin.Minn@vindicara.io**
Website: **https://vindicara.io**

## 8. Changes to This Policy

Vindicara may update this Policy to reflect changes to the Services, to adopt emerging disclosure norms, or to respond to legal developments. Material changes will take effect thirty (30) days after notice on vindicara.io, with the "Last Updated" date updated accordingly.

---

### Appendix A — `security.txt` (RFC 9116)

Vindicara will publish a `security.txt` file at https://vindicara.io/.well-known/security.txt conforming to RFC 9116 with at minimum:

```
Contact: mailto:security@vindicara.io
Contact: mailto:Kevin.Minn@vindicara.io
Expires: [one year forward of publication, refresh annually]
Policy: https://vindicara.io/security
Preferred-Languages: en
Canonical: https://vindicara.io/.well-known/security.txt
```
