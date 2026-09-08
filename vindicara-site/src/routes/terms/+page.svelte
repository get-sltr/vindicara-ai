<script>
  import AppShell from '$components/AppShell.svelte';
</script>
<svelte:head><title>Vindicara · Terms of Service</title></svelte:head>

<AppShell active="terms" title="terms" scroll={true}>
  <div class="prose">
    <div class="eyebrow">Terms &amp; conditions</div>
    <h1>Terms of Service.</h1>
    <p class="muted">Last updated: June 6, 2026</p>

    <p class="lede">These Terms of Service ("Terms") are a binding agreement between Vindicara, Inc., a Delaware corporation ("Vindicara," "we," "us," or "our"), and the individual or entity that accesses or uses our websites, software, or services ("you" or "Customer"). By accessing or using the Services, you agree to these Terms. If you are entering into these Terms on behalf of an organization, you represent that you have authority to bind that organization, and "you" refers to that organization.</p>

    <h2>1. Definitions</h2>
    <p>"Services" means, collectively, the Vindicara websites; the open-source <b>air</b> command-line interface and <b>airsdk</b> library ("Open-Source Software"); the hosted FlightDeck console and AIR Cloud offerings ("Hosted Services"); and any related documentation, APIs, and support. "Customer Data" means data, content, agent traces, decision records, and other materials you submit to, generate within, or process through the Services. "Evidence Chain" means the signed, hash-linked record (an AgDR / Signed Intent Capsule chain) produced by the Services. "Order" means an order form, online checkout, or written agreement referencing these Terms.</p>

    <h2>2. The Open-Source Software</h2>
    <p>The air CLI and airsdk are licensed to you under the Apache License 2.0, the full text of which is included in the source repository at github.com/vindicara-inc/projectair. Your rights to the Open-Source Software are governed solely by the Apache License 2.0, and nothing in these Terms limits, supersedes, or adds conditions to the rights granted under that license. To the maximum extent permitted by law, the Open-Source Software is provided "AS IS" without warranty of any kind, and Sections 11 and 12 apply to it.</p>

    <h2>3. The Hosted Services</h2>
    <p>The Hosted Services are made available on a subscription or design-partner basis as described in the applicable Order. We grant you a non-exclusive, non-transferable, non-sublicensable right to access and use the Hosted Services during the subscription term, solely for your internal business purposes and subject to these Terms and any usage limits in your Order. We may modify, enhance, or discontinue features of the Hosted Services, provided that we will not materially decrease the core functionality of a paid subscription during its then-current term.</p>

    <h2>4. Accounts, Authentication, and Signing Keys</h2>
    <p>Access to the Hosted Services requires an account authenticated through our identity provider (Auth0). You are responsible for (a) maintaining the confidentiality of your credentials and access tokens; (b) all activity occurring under your account; and (c) the generation, custody, rotation, and revocation of any cryptographic signing keys you use with the Services. Because Evidence Chains are signed with keys held under your sole control, you acknowledge that we cannot recover, reissue, or re-sign records on your behalf, and that the integrity guarantees of the Services depend on your key management. You must promptly notify us of any unauthorized use of your account at security@vindicara.io.</p>

    <h2>5. Beta and Design-Partner Features</h2>
    <p>Some features, including commercial tiers offered to design partners, may be identified as beta, preview, evaluation, or early access ("Beta Features"). Beta Features are provided "AS IS," may be changed or withdrawn at any time, may not be supported, and are excluded from any service-level commitment and from the warranties in these Terms. We may use aggregated, de-identified information about your use of Beta Features to improve the Services.</p>

    <h2>6. Fees, Billing, and Taxes</h2>
    <p>Fees for paid Hosted Services are stated in your Order. Unless otherwise specified: (a) subscriptions are billed in advance through our payment processor (Stripe) and are non-refundable except as required by law; (b) subscriptions renew automatically for successive terms unless cancelled before the end of the then-current term; (c) we may change fees effective at the start of a renewal term with prior notice; and (d) fees are exclusive of taxes, and you are responsible for all applicable taxes other than taxes on our income. Late or failed payments may result in suspension of the Hosted Services. We do not store full payment card numbers; payment information is handled by Stripe under its terms and privacy policy.</p>

    <h2>7. Acceptable Use</h2>
    <p>You agree not to, and not to permit any third party to: (a) use the Services in violation of any law or third-party right; (b) reverse engineer, decompile, or attempt to derive source code from the Hosted Services (except as permitted for the Open-Source Software under the Apache License 2.0 or by applicable law); (c) resell, sublicense, or provide the Hosted Services to third parties except as expressly permitted; (d) interfere with or disrupt the integrity or performance of the Services, circumvent usage limits, or attempt to gain unauthorized access; (e) upload malware or use the Services to develop a competing product by copying its non-open-source components; or (f) submit Customer Data that you do not have the right to submit. We may suspend access to address a material violation of this Section, a security risk, or a legal requirement, with notice where practicable.</p>

    <h2>8. Customer Data, Evidence, and Ownership</h2>
    <p>As between the parties, you retain all right, title, and interest in and to Customer Data, and we claim no ownership of it. You grant us a limited, worldwide, non-exclusive license to host, process, transmit, display, and otherwise use Customer Data solely to provide, secure, and support the Services and as otherwise instructed by you. You are responsible for the accuracy, legality, and appropriateness of Customer Data and for obtaining all rights and consents necessary for us to process it.</p>
    <p><b>Redaction.</b> The Services apply default-deny redaction to published Evidence Chains: non-whitelisted payload fields are replaced with cryptographic hashes, so that method, path, status, and similar metadata may pass through while underlying content is hashed rather than disclosed. You are responsible for configuring redaction and retention to meet your obligations.</p>
    <p><b>Public transparency log.</b> You acknowledge that, where you enable anchoring, chain roots and hashed identifiers are published to independent public transparency logs and timestamp authorities (including Sigstore Rekor and an RFC 3161 timestamp authority). These public entries contain hashes and metadata, not cleartext Customer Data, but they are immutable and cannot be deleted, modified, or recalled once published. Do not enable anchoring for data whose hashes or existence you are not permitted to disclose.</p>
    <p><b>Storage and access.</b> We do not access raw Customer Data payloads outside the scope necessary to provide the Services or as you instruct, except as required by law. Where offered, you may elect customer-controlled (in-VPC) storage of Evidence Chains.</p>

    <h2>9. Intellectual Property</h2>
    <p>Except for the rights expressly granted to you, we and our licensors retain all right, title, and interest in and to the Services, including all software, models, designs, and documentation, and all intellectual property rights therein. "Vindicara," "Project AIR," and related marks are our trademarks. If you provide suggestions or feedback, you grant us a perpetual, irrevocable, royalty-free license to use it without restriction or obligation to you.</p>

    <h2>10. Confidentiality</h2>
    <p>"Confidential Information" means non-public information disclosed by one party to the other that is designated confidential or that reasonably should be understood to be confidential. The receiving party will use the disclosing party's Confidential Information only to perform under these Terms, protect it with at least reasonable care, and not disclose it except to personnel and contractors with a need to know who are bound by confidentiality obligations. This Section does not apply to information that is or becomes public through no fault of the receiving party, was lawfully known prior to disclosure, or is independently developed.</p>

    <h2>11. Disclaimers</h2>
    <p><b>The Services are forensic and evidentiary tooling, not legal advice and not a certification.</b> Project AIR produces technical evidence inputs and detector findings. It does not determine, and does not guarantee, the admissibility, sufficiency, or legal effect of any record in any proceeding; admissibility is decided by the court, regulator, or other authority hearing the matter. The detectors are heuristics that will produce false positives and false negatives and do not guarantee detection or prevention of any particular event. You are responsible for obtaining your own legal, regulatory, and compliance advice.</p>
    <p>EXCEPT AS EXPRESSLY STATED IN THESE TERMS, THE SERVICES ARE PROVIDED "AS IS" AND "AS AVAILABLE," AND VINDICARA DISCLAIMS ALL WARRANTIES, WHETHER EXPRESS, IMPLIED, STATUTORY, OR OTHERWISE, INCLUDING IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE, AND NON-INFRINGEMENT, AND ANY WARRANTY THAT THE SERVICES WILL BE UNINTERRUPTED, ERROR-FREE, OR SECURE.</p>

    <h2>12. Limitation of Liability</h2>
    <p>TO THE MAXIMUM EXTENT PERMITTED BY LAW, NEITHER PARTY WILL BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, EXEMPLARY, OR PUNITIVE DAMAGES, OR FOR ANY LOSS OF PROFITS, REVENUE, DATA, GOODWILL, OR BUSINESS, ARISING OUT OF OR RELATED TO THESE TERMS, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGES. EXCEPT FOR (A) YOUR PAYMENT OBLIGATIONS, (B) A PARTY'S INDEMNIFICATION OBLIGATIONS, AND (C) A PARTY'S BREACH OF ITS CONFIDENTIALITY OBLIGATIONS, EACH PARTY'S TOTAL AGGREGATE LIABILITY ARISING OUT OF OR RELATED TO THESE TERMS WILL NOT EXCEED THE AMOUNTS PAID OR PAYABLE BY YOU TO VINDICARA FOR THE HOSTED SERVICES IN THE TWELVE MONTHS PRECEDING THE EVENT GIVING RISE TO THE CLAIM, OR ONE HUNDRED U.S. DOLLARS (USD 100) IF YOU USE ONLY THE OPEN-SOURCE SOFTWARE OR FREE TIER. THESE LIMITATIONS APPLY IN THE AGGREGATE AND REGARDLESS OF THE THEORY OF LIABILITY.</p>

    <h2>13. Indemnification</h2>
    <p>You will defend, indemnify, and hold harmless Vindicara from and against third-party claims, damages, and reasonable costs (including reasonable attorneys' fees) arising out of (a) Customer Data, (b) your use of the Services in violation of these Terms or applicable law, or (c) your infringement or misappropriation of a third party's rights. We will defend, indemnify, and hold you harmless from third-party claims alleging that the Hosted Services, as provided by us and used in accordance with these Terms, infringe that third party's intellectual property rights. The indemnifying party's obligations are conditioned on prompt notice, sole control of the defense, and reasonable cooperation.</p>

    <h2>14. Term, Suspension, and Termination</h2>
    <p>These Terms apply for as long as you use the Services. Either party may terminate a subscription for the other party's material breach not cured within thirty (30) days of written notice. We may suspend or terminate access immediately for non-payment, a material acceptable-use or security violation, or as required by law. Upon termination of a paid subscription, you may export your Evidence Chains and Customer Data for a period of thirty (30) days, after which we may delete them in the ordinary course, subject to retention required by law. Sections that by their nature should survive termination (including 8, 9, 10, 11, 12, 13, and 16) will survive.</p>

    <h2>15. Third-Party Services and Subprocessors</h2>
    <p>The Services rely on third-party infrastructure and subprocessors, including Amazon Web Services (hosting), Auth0 (identity), Stripe (payments), and Sigstore Rekor and a trusted timestamp authority (public anchoring). Your use of features that depend on these providers is subject to their terms, and we are not responsible for the acts or omissions of third-party providers. A current list of subprocessors is available on request and is described further in our Privacy Policy.</p>

    <h2>16. Governing Law and Disputes</h2>
    <p>These Terms are governed by the laws of the State of Delaware, without regard to its conflict-of-laws rules. The parties will first attempt to resolve any dispute informally by contacting legal@vindicara.io. Any dispute not resolved informally will be subject to the exclusive jurisdiction of the state and federal courts located in Delaware, and each party consents to personal jurisdiction and venue there, except that either party may seek injunctive relief in any court of competent jurisdiction to protect its intellectual property or Confidential Information.</p>

    <h2>17. Export, Sanctions, and Compliance</h2>
    <p>You represent that you are not located in, and will not use the Services in or for the benefit of, any jurisdiction or person subject to comprehensive U.S. sanctions or export restrictions, and that you will comply with all applicable export-control and sanctions laws.</p>

    <h2>18. Changes to the Services and These Terms</h2>
    <p>We may update these Terms from time to time. If we make a material change, we will provide reasonable notice (for example, by posting the updated Terms with a new "Last updated" date or by notifying account holders). Changes are effective when posted unless stated otherwise, and your continued use of the Services after the effective date constitutes acceptance.</p>

    <h2>19. General</h2>
    <p>These Terms, together with any Order and our Privacy Policy, are the entire agreement between the parties regarding the Services and supersede prior agreements on that subject. You may not assign these Terms without our prior written consent, except to a successor in connection with a merger or sale of substantially all assets; we may assign these Terms to an affiliate or successor. If any provision is held unenforceable, the remaining provisions remain in effect. A party's failure to enforce a provision is not a waiver. Nothing in these Terms creates an agency, partnership, or joint venture. Notices to Vindicara must be sent to legal@vindicara.io.</p>

    <h2>20. Contact</h2>
    <p>Questions about these Terms: <a href="mailto:legal@vindicara.io">legal@vindicara.io</a>. General support: <a href="mailto:support@vindicara.io">support@vindicara.io</a>.</p>

    <h2>Legal &amp; compliance documents</h2>
    <p>The agreements and evidentiary templates that support a deployment:</p>
    <div class="docs">
      <a class="doc" href="/privacy"><span class="dn">Privacy Policy</span><span class="dm">how we collect and handle data</span></a>
      <a class="doc" href="/legal/ProjectAIR-BAA-v1.1.docx" download><span class="dn">Business Associate Agreement (BAA) v1.1</span><span class="dm">HIPAA · .docx download</span></a>
      <a class="doc" href="/dpa"><span class="dn">Data Processing Addendum (DPA)</span><span class="dm">GDPR / CCPA · read or execute</span></a>
      <a class="doc" href="/security"><span class="dn">Security &amp; responsible disclosure</span><span class="dm">practices and how to report</span></a>
      <a class="doc" href="/admissibility"><span class="dn">FRE 902(13) certification generator</span><span class="dm">self-authenticating evidence records</span></a>
      <a class="doc" href="https://github.com/vindicara-inc/projectair" target="_blank" rel="noopener"><span class="dn">Apache License 2.0</span><span class="dm">air CLI and airsdk · source repository</span></a>
    </div>

    <div class="links">
      <a href="/privacy">Privacy Policy</a><a href="/contact">Contact</a><a href="https://github.com/vindicara-inc/projectair" target="_blank" rel="noopener">Source · Apache 2.0</a>
    </div>
  </div>
</AppShell>

<style>
  .prose h1{font-size:36px;margin:14px 0 0}
  .prose h2{font-size:18px;margin:26px 0 0}
  .lede{font-size:15px;color:var(--white);line-height:1.65;margin:16px 0 4px;font-family:var(--display)}
  .muted{color:var(--faint);font-family:var(--mono);font-size:12px;margin-top:8px}
  .prose p{font-size:13.5px;color:var(--soft);line-height:1.7;margin-top:8px}
  .prose a{color:var(--air2);text-decoration:none} .prose a:hover{text-decoration:underline}
  .docs{display:grid;gap:8px;margin:12px 0 4px}
  .doc{display:flex;justify-content:space-between;align-items:center;gap:14px;border:1px solid var(--line);background:var(--navy1);padding:12px 14px;text-decoration:none}
  .doc:hover{border-color:rgba(230,57,70,.4)}
  .doc .dn{font-size:13px;font-weight:600;color:var(--white)}
  .doc .dm{font-family:var(--mono);font-size:10.5px;color:var(--faint);text-align:right}
  .links{display:flex;gap:18px;margin-top:28px;font-family:var(--mono);font-size:12px}
</style>
