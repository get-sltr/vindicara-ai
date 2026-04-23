---
title: "Privacy Policy"
subtitle: "Vindicara, Inc. · Project AIR™"
last_updated: "2026-04-22"
effective_date: "2026-04-22"
version: "1.0"
---

# Privacy Policy

> **Version 1.0 · Draft under counsel review.** This document describes Vindicara, Inc.'s current privacy practices and is under active legal review. Vindicara may amend this document in accordance with Section 15 (Changes to This Privacy Policy). For privacy-related inquiries, contact Kevin.Minn@vindicara.io.

**Effective Date:** April 22, 2026
**Last Updated:** April 22, 2026

---

## 1. Who We Are

Vindicara, Inc. ("**Vindicara**," "**we**," "**us**," or "**our**") is a California corporation operating the website at https://vindicara.io (the "**Site**"), the open-source `projectair` Python package (including the `air` command-line interface and `airsdk` library, collectively the "**OSS Software**"), the AIR Cloud hosted service (the "**Team Tier**"), and the AIR Enterprise offering (the "**Enterprise Tier**"; collectively with the Team Tier, the "**Paid Services**"). This Privacy Policy explains how we collect, use, disclose, store, and protect Personal Information about you.

For privacy inquiries, contact us at **privacy@vindicara.io** or at the address in Section 16.

## 2. Scope of This Policy

This Privacy Policy applies to Personal Information we collect:

- When you visit or interact with the Site;
- When you download, install, or use the OSS Software (note: the OSS Software is designed to operate locally and does not transmit data to Vindicara by default);
- When you create an account, subscribe to, or use any Paid Service;
- When you communicate with us by email, support request, or other channel;
- When you attend events, respond to surveys, or apply for employment with us;
- From third-party sources, such as our payment processor (Square), cloud infrastructure providers, analytics providers, and publicly available sources.

This Privacy Policy **does not apply** to third-party websites, products, or services linked from the Site, including but not limited to GitHub, PyPI, LangChain, OpenAI, Anthropic, Slack, PagerDuty, Datadog, Splunk, or any other third-party platform. Those third parties have their own privacy policies, which we recommend you review.

## 3. Personal Information We Collect

The categories of Personal Information we collect depend on how you interact with Vindicara.

### 3.1 Information You Provide Directly

**Account and subscription information (Paid Services).**
- Full name
- Business email address
- Billing contact information
- Company name and role
- Payment information (processed by Square; we do not store full payment card numbers — see Section 3.5)

**Communications and support.**
- Email content, message body, and any attachments you send us
- Phone numbers, if you provide them for support
- Records of support tickets and their resolution

**Agent registries, signing keys, and custom configuration.**
- For Paid Services, identifiers you declare in your agent registry (agent IDs, signing public keys, permitted tools, privilege tiers). We treat these as Customer Data under the Terms of Service.

**Job applications and recruiting.**
- Name, email, phone, résumé, CV, cover letter, work-authorization status
- Interview notes and evaluations
- Information you provide during interviews

**Event attendance.**
- Name, email, company, and job title for events we host or attend

### 3.2 Information Collected Automatically (Site Visitors)

When you visit the Site, we may automatically collect:

- IP address and approximate geolocation derived from IP
- Browser type and version, operating system, device type, screen resolution
- Referring URL, pages visited, time spent on pages, links clicked
- Date and time of visits
- Cookies and similar tracking technologies (see Section 7)
- For purposes of DDoS protection and security logging, connection metadata routed through our CDN / WAF provider

We use commercial analytics products that are configured with IP anonymization where supported. We do not use behavioral advertising trackers or cross-site ad pixels.

### 3.3 Information Collected from the OSS Software

The `projectair` OSS Software is designed as a **privacy-respecting local tool**. By default it:
- Does not transmit any data to Vindicara
- Does not phone home
- Does not collect telemetry or usage statistics
- Does not require registration or an account

If you voluntarily report a bug via GitHub issues or email, the content you include in that report is treated under Section 3.1 (Communications and support).

### 3.4 Customer Data (Paid Services)

When you use the Paid Services, you upload or transmit Customer Data to our systems, which may include:

- Signed Intent Capsule chains (`.log` files)
- Agent registries (YAML / JSON)
- Forensic reports
- Integration configurations (SIEM endpoints, alerting channels)
- Any data contained within the Intent Capsules you upload, which may include: prompts, LLM responses, tool names, tool arguments, tool outputs, user intents, source and target agent identifiers, message content, and related payload fields

**Customer Data may contain Personal Information about you and about third parties (including your end users, employees, or customers).** You are the controller of Personal Information contained in Customer Data. Vindicara acts as a processor and handles that Personal Information in accordance with our Terms of Service, this Privacy Policy, and any Data Processing Agreement you execute with us.

### 3.5 Payment Information

Payments for the Team Tier are processed by **Square, Inc.** ("Square"). Square is a PCI-compliant payment processor. Vindicara does not store full credit or debit card numbers, CVVs, or PINs. We may receive a tokenized reference to your payment method, the last four digits of your card, expiration date, and billing ZIP code from Square for receipt and invoice purposes. Your payment data is governed by Square's Privacy Notice (https://squareup.com/legal/privacy).

### 3.6 Sensitive Personal Information

Vindicara does not knowingly solicit or collect sensitive Personal Information such as Social Security Numbers, government-issued identification numbers, precise geolocation, biometric data, racial or ethnic origin, religious or philosophical beliefs, union membership, sexual orientation, health data, or genetic data.

If you include sensitive Personal Information in Customer Data (for example, by uploading an agent trace that happens to contain such information), you are solely responsible for the lawfulness of that processing and for obtaining any consents required. Vindicara recommends that you redact or avoid uploading sensitive Personal Information.

### 3.7 Information from Third Parties

We may receive Personal Information from:

- Our cloud infrastructure provider (Amazon Web Services) and CDN / DNS providers
- Our payment processor (Square) for payment confirmation and invoicing
- Our email delivery provider for transactional email status (delivery, bounce, complaint)
- Event and marketing platforms when you register for events we participate in
- Publicly available sources (LinkedIn profiles, company websites) in the course of ordinary business development

### 3.8 Aggregated and De-Identified Information

We may aggregate or de-identify Personal Information so that it no longer reasonably identifies any individual. Aggregated and de-identified information is not subject to this Privacy Policy and may be used for any lawful business purpose, including detector research, public reporting, and product development. We maintain aggregated and de-identified information without attempting to re-identify it.

## 4. How We Use Personal Information

We use Personal Information for the following purposes:

### 4.1 Provide and Operate the Services
- Create and maintain your account
- Authenticate you and secure your access
- Process subscriptions and payments
- Deliver Team Tier features, including ingestion, dashboard rendering, SIEM export, alerting
- Verify chain integrity and generate forensic reports
- Support agent-registry management and Zero-Trust enforcement

### 4.2 Communicate With You
- Respond to support requests, contract inquiries, and account questions
- Send transactional messages (receipts, renewal notices, security notices, feature announcements directly tied to your account)
- Send product announcements and newsletters you have subscribed to (subject to opt-out rights)

### 4.3 Improve and Develop the Services
- Understand how the Site is used and where users get stuck
- Debug issues and improve reliability
- Develop new detector logic, new features, and new products, including with de-identified and aggregated Customer Data

### 4.4 Secure the Services
- Monitor for abuse, unauthorized access, fraud, and attacks
- Enforce our Terms of Service and Acceptable Use Policy
- Investigate and respond to security incidents
- Retain audit logs required for our own compliance obligations

### 4.5 Comply With Legal Obligations
- Respond to subpoenas, court orders, regulatory requests, and other legal process
- Retain records required by tax, accounting, and employment law
- Cooperate with government authorities on matters we are legally required to address

### 4.6 Business Development
- Evaluate new business opportunities
- Manage contracts, vendor relationships, and partnerships
- Conduct due diligence in connection with financings or corporate transactions

### 4.7 Recruiting and Employment
- Evaluate applications and conduct interviews
- Retain applicant records for a reasonable period after application or hire
- Comply with employment, tax, and immigration law

### 4.8 Legal Bases (EEA / UK / Swiss Residents)

If you are located in the European Economic Area, the United Kingdom, or Switzerland, we process your Personal Information based on one or more of the following legal bases:

- **Performance of a contract**: to provide Services you have requested.
- **Legitimate interests**: to secure and improve the Services, conduct business development, and comply with reasonable commercial obligations, balanced against your rights and freedoms.
- **Compliance with a legal obligation**: to comply with applicable law.
- **Consent**: where required (e.g., non-essential cookies, marketing emails); you may withdraw consent at any time without affecting the lawfulness of prior processing.
- **Vital interests or public interest**: in rare circumstances where required.

## 5. How We Share Personal Information

We share Personal Information only in the circumstances described below.

### 5.1 Service Providers

We share Personal Information with third-party service providers that help us operate the Services. These providers are contractually bound to process Personal Information only as instructed by Vindicara and to apply reasonable technical and organizational security measures. Current categories include:

- **Cloud infrastructure and hosting** (Amazon Web Services) — provides the compute, storage, and network infrastructure for the Team Tier
- **Payment processing** (Square) — processes subscription payments
- **Email delivery** (transactional email provider) — sends receipts, support replies, security notices
- **Customer support tooling** (help-desk and ticketing platforms)
- **Analytics** (commercial web analytics with IP anonymization)
- **CDN and DDoS protection** (edge-network provider for Site delivery and security)
- **Version control and source distribution** (GitHub, PyPI) — for the OSS Software
- **Identity and authentication** (for Enterprise customers, SSO / SAML providers as configured)
- **Internal tools** (productivity, communications, and engineering workflows)

A current list of our subprocessors is available upon request. We will provide reasonable advance notice of material changes to our subprocessor list where required under a Data Processing Agreement.

### 5.2 Business Transfers

If Vindicara is involved in a merger, acquisition, financing, reorganization, bankruptcy, receivership, asset sale, or similar transaction, Personal Information may be transferred as part of that transaction. We will provide notice of any such transfer and describe any changes to this Privacy Policy that result from it.

### 5.3 Compliance With Law and Protection of Rights

We may disclose Personal Information when we believe in good faith that disclosure is necessary to:

- Comply with a law, regulation, subpoena, court order, or government request;
- Enforce our Terms of Service or investigate suspected violations;
- Detect, prevent, or address fraud, abuse, or security issues;
- Protect the rights, property, or safety of Vindicara, our users, or the public;
- Exercise or defend legal claims.

Where legally permissible, we will attempt to provide notice to affected individuals and narrow the scope of the disclosure.

### 5.4 With Your Consent

We share Personal Information with third parties with your consent or at your direction, including when you configure the Team Tier to export forensic records to a third-party SIEM, alerting platform, or integration endpoint.

### 5.5 Aggregated or De-Identified Information

We share aggregated or de-identified information that does not reasonably identify you, including in research publications, detector-accuracy reports, and marketing content.

### 5.6 No Sale of Personal Information

Vindicara **does not sell Personal Information** as "sale" is defined under California law (Cal. Civ. Code § 1798.140(ad)) or analogous laws. Vindicara does not share Personal Information for cross-context behavioral advertising.

## 6. International Transfers

Vindicara is headquartered in the United States and processes Personal Information in the United States and, through our cloud infrastructure provider, in other countries where infrastructure is hosted. If you are located in the European Economic Area, the United Kingdom, Switzerland, or another jurisdiction that restricts transfers of Personal Information to the United States, your Personal Information will be transferred internationally only where we have implemented appropriate safeguards.

For transfers from the EEA, UK, or Switzerland, we rely on:

- **Standard Contractual Clauses (SCCs)** issued by the European Commission on 4 June 2021, incorporated into our subprocessor agreements; and
- Supplementary measures including encryption in transit (TLS 1.3) and at rest, strict access controls, pseudonymization where practicable, and transparency regarding government access requests.

You may request a copy of the relevant safeguards applicable to your data by contacting us at **privacy@vindicara.io**.

## 7. Cookies and Similar Technologies

### 7.1 What We Use

We use a minimal set of cookies and similar tracking technologies on the Site:

- **Strictly necessary cookies**: required to operate the Site (for example, session management, load balancing, security). These cookies are not optional and do not require consent under most frameworks.
- **Functional cookies**: remember preferences such as UI state.
- **Analytics cookies**: help us understand how the Site is used, with IP anonymization where supported.

We do **not** use third-party advertising cookies, retargeting pixels, or cross-site tracking cookies.

### 7.2 Your Choices

You can control cookies through your browser settings. Blocking strictly necessary cookies may make parts of the Site inoperable. Where required by applicable law (including the EU ePrivacy Directive and CCPA regulations), we present a cookie banner with options to accept or reject non-essential cookies.

### 7.3 Do Not Track

The Site does not currently respond to Do Not Track signals because no common industry standard for responding to Do Not Track has been established.

## 8. Data Retention

We retain Personal Information only as long as necessary for the purposes described in this Privacy Policy or as required by law.

- **Site visitor analytics**: retained for up to 25 months in aggregated form.
- **Account information**: retained for the duration of your subscription and for up to seven (7) years after termination to comply with tax, accounting, and audit obligations.
- **Customer Data (Paid Services)**: retained during your subscription and for up to ninety (90) days after termination for the purpose of restoration, except as required by legal hold or as agreed in writing.
- **Billing and payment records**: retained for up to seven (7) years to comply with tax and accounting law.
- **Support communications**: retained for up to three (3) years after the ticket is resolved.
- **Job applications**: retained for up to two (2) years after the position is filled or the application is withdrawn, unless you request earlier deletion.
- **Legal holds**: information subject to a legal hold, pending investigation, or active litigation may be retained longer.

Where we aggregate or de-identify Personal Information, we may retain the resulting information indefinitely.

## 9. Security

We implement reasonable technical and organizational measures designed to protect Personal Information against unauthorized access, disclosure, alteration, or destruction. These measures include:

- Encryption in transit (TLS 1.3) for data transmitted to and from the Services
- Encryption at rest for Customer Data stored in the Paid Services
- Access controls based on least privilege and role-based access
- Multi-factor authentication on employee administrative accounts
- Audit logging of administrative actions
- Regular security reviews, third-party dependency monitoring, and vulnerability patching
- Network segmentation and firewalls
- Incident response procedures

**No security measure is perfect.** Despite our safeguards, we cannot guarantee absolute security. You are responsible for maintaining the security of your account credentials, signing keys, and the endpoint devices through which you access the Services.

In the event of a security incident affecting your Personal Information, we will notify you and relevant authorities as required by applicable law (for example, GDPR Article 33-34 notification, California Civil Code § 1798.82, HIPAA notification if a BAA is in place, or other applicable breach-notification regimes).

## 10. Your Privacy Rights

Your rights depend on your location and the applicable law. Below are the most common frameworks. If you are not covered by one of these, please contact us; we will respond to reasonable privacy requests consistent with applicable law and our legitimate business interests.

### 10.1 California Residents (CCPA / CPRA)

If you are a California resident, you have the following rights under the California Consumer Privacy Act of 2018 as amended by the California Privacy Rights Act of 2020 (together, "**CCPA**"):

**Right to Know.** You may request that we disclose:
- The categories of Personal Information we have collected about you
- The categories of sources from which we collected it
- The business or commercial purpose for collecting, using, or disclosing it
- The categories of third parties with whom we shared it
- The specific pieces of Personal Information we have collected about you

**Right to Delete.** You may request that we delete Personal Information we have collected about you, subject to exceptions (including records required by law and information needed to secure the Services or detect fraud).

**Right to Correct.** You may request that we correct inaccurate Personal Information we maintain about you.

**Right to Opt-Out of Sale or Sharing.** Vindicara does not sell Personal Information or share it for cross-context behavioral advertising, so there is nothing to opt out of, but you retain the right to request confirmation of this.

**Right to Limit Use and Disclosure of Sensitive Personal Information.** Vindicara does not knowingly collect sensitive Personal Information for purposes other than those permitted under Cal. Code Regs. tit. 11 § 7027(m).

**Right to Non-Discrimination.** We will not discriminate against you for exercising any CCPA right. We will not deny Services, charge different prices, or provide a different level of quality because you exercised rights.

**Authorized Agents.** You may designate an authorized agent to make requests on your behalf. We may require verification of the agent's authority and your identity.

**How to Exercise.** Email **privacy@vindicara.io** with your request. We will verify your identity before responding by confirming information we have on file. We will respond within forty-five (45) days (extendable once by an additional forty-five (45) days with notice to you) per Cal. Code Regs. tit. 11 § 7021.

### 10.2 EEA, UK, and Swiss Residents (GDPR / UK GDPR)

If you are in the European Economic Area, the United Kingdom, or Switzerland, you have the following rights under GDPR, UK GDPR, and the Swiss Federal Act on Data Protection, to the extent they apply:

- **Right of access** (GDPR Article 15)
- **Right to rectification** (Article 16)
- **Right to erasure / "right to be forgotten"** (Article 17), subject to exceptions
- **Right to restrict processing** (Article 18)
- **Right to data portability** (Article 20)
- **Right to object to processing** based on legitimate interests or direct marketing (Article 21)
- **Rights related to automated decision-making and profiling** (Article 22)
- **Right to withdraw consent** where processing is based on consent
- **Right to lodge a complaint** with your local supervisory authority

**How to Exercise.** Email **privacy@vindicara.io**. We will respond within one (1) month, extendable by two (2) months for complex requests with notice to you.

**EU / UK Representative.** Vindicara has not currently appointed an EU Representative under GDPR Article 27 or a UK Representative under UK GDPR Article 27. Vindicara's current processing activities are below the thresholds that, in Vindicara's good-faith assessment, require such appointment. Vindicara will re-evaluate this designation as its processing activities and EU/UK-facing customer base expand.

### 10.3 Other U.S. States

Several U.S. states (including Colorado, Connecticut, Virginia, Utah, Texas, Oregon, Montana, Delaware, Iowa, Indiana, Tennessee, New Jersey, New Hampshire, Kentucky, Minnesota, and others) have enacted consumer-privacy laws similar in structure to CCPA. If you are a resident of one of these states, you may have substantially similar rights (access, correction, deletion, opt-out of targeted advertising or sale). Vindicara will honor qualifying requests in accordance with each applicable state law. Email **privacy@vindicara.io** to exercise rights.

### 10.4 Other Jurisdictions

If your jurisdiction provides additional privacy rights (for example, Canada PIPEDA, Brazil LGPD, Australia Privacy Act, Japan APPI, South Korea PIPA, Singapore PDPA), contact us and we will respond in good faith consistent with applicable law.

## 11. Children's Privacy

The Services are not directed to children under the age of sixteen (16), and we do not knowingly collect Personal Information from children. If you become aware that a child has provided Personal Information to Vindicara, please contact **privacy@vindicara.io** and we will take steps to delete it.

## 12. Automated Decision-Making

Vindicara does not use Personal Information to make solely automated decisions that produce legal or similarly significant effects concerning you. Detector findings produced by the Services are informational signals for human review; they do not constitute automated legal, employment, credit, or similarly significant decisions.

## 13. Third-Party Sites and Services

The Site and documentation may contain links to third-party sites, services, and integrations. This Privacy Policy does not apply to those third parties. We encourage you to review the privacy policies of any third party before providing Personal Information to them.

## 14. California "Shine the Light" Law

California Civil Code § 1798.83 permits California residents to request a notice disclosing the categories of Personal Information we have shared with third parties for their direct-marketing purposes in the preceding calendar year. Because we do not share Personal Information with third parties for their direct-marketing purposes, there is no such notice to provide. If you wish to confirm this, email **privacy@vindicara.io**.

## 15. Changes to This Privacy Policy

We may update this Privacy Policy to reflect changes to our practices, to comply with law, or to improve clarity. If we make a material change, we will provide notice through the Services, by email to the address associated with your account (if any), or by updating the "Last Updated" date at the top of this Policy. Material changes take effect thirty (30) days after notice is provided, unless they must take effect sooner to comply with legal requirements. Continued use after the effective date of the updated Privacy Policy constitutes acceptance.

## 16. How to Contact Us

**Vindicara, Inc.**
Attn: Privacy / Data Protection
- Privacy requests: **privacy@vindicara.io**
- Legal notices: **legal@vindicara.io**
- Security disclosures: **security@vindicara.io**
- General inquiries: **Kevin.Minn@vindicara.io**
- Website: **https://vindicara.io**
- Registered office: 696 S New Hampshire Ave, Los Angeles, CA 90005, United States

**Data Protection Officer (DPO).** Vindicara is not required under GDPR Article 37 to appoint a Data Protection Officer based on its current size and processing activities, in Vindicara's good-faith assessment. Vindicara will re-evaluate this designation as its processing activities expand.

**EU Representative.** Not appointed. See Section 10.2.

**UK Representative.** Not appointed. See Section 10.2.

---

### Appendix A — Plain-English Summary (Non-Binding)

The following summary is provided for readability. In the event of any conflict between this summary and the main body of this Privacy Policy, the main body controls.

1. **The OSS Software does not send anything to Vindicara.** If you only use the `projectair` command-line tool and library, we do not see your data. Full stop.

2. **The Site has minimal analytics.** We count pageviews. We do not run advertising cookies. We do not sell your data.

3. **If you subscribe to AIR Cloud, we process the data you upload.** That includes agent traces, which may contain sensitive content. We encrypt it, we use it only to give you the service, and we delete it (subject to backups) when you leave. You own it; we handle it.

4. **We use standard service providers.** Amazon Web Services for hosting. Square for payments. Standard stuff. Each has its own privacy terms.

5. **We do not sell your Personal Information.** We have no interest in doing so.

6. **We give you real control.** If you are in California, the EU, the UK, or most US states, you have rights to see, correct, and delete your data. Email privacy@vindicara.io and we will respond within the legal deadline.

7. **Children should not use the Services.** The Services are not for users under 16.

8. **If we are ever breached, we will tell you.** We hope that never happens. If it does, you will hear from us within the legal deadline (72 hours under GDPR; without unreasonable delay under California law).

---

