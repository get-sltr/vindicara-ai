<script>
  import AppShell from '$components/AppShell.svelte';
</script>

<svelte:head>
  <title>Acute Myeloid Leukemia in 2026: Symptoms, Diagnosis, Classification, Treatment | Vindicara Blog</title>
  <meta name="description" content="A physician-grade guide to acute myeloid leukemia: symptoms, the MICM diagnostic workup, why WHO 2022 and ICC 2022 classify the same patient differently, and the 2026 treatment landscape." />
  <meta property="og:type" content="article" />
  <meta property="og:url" content="https://vindicara.io/blog/acute-myeloid-leukemia-guide" />
  <meta property="og:title" content="Acute Myeloid Leukemia in 2026: Symptoms, Diagnosis, Classification, Treatment" />
  <meta property="og:description" content="Why WHO 2022 and ICC 2022 can classify the same AML patient differently, and what that means for diagnosis and treatment." />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="Acute Myeloid Leukemia in 2026: Symptoms, Diagnosis, Classification, Treatment" />
  <meta name="twitter:description" content="Why WHO 2022 and ICC 2022 can classify the same AML patient differently, and what that means for diagnosis and treatment." />
  <meta name="keywords" content="acute myeloid leukemia, AML symptoms, AML diagnosis, AML treatment, AML classification, WHO 2022 AML, ICC 2022 AML, NPM1 mutation, FLT3 mutation, AML survival rate" />
  {@html `<script type="application/ld+json">${JSON.stringify({
    "@context": "https://schema.org",
    "@type": "MedicalWebPage",
    "headline": "Acute Myeloid Leukemia in 2026: Symptoms, Diagnosis, Classification, Treatment",
    "description": "A physician-grade guide to acute myeloid leukemia: symptoms, the MICM diagnostic workup, WHO 2022 vs ICC 2022 classification, and the 2026 treatment landscape.",
    "datePublished": "2026-07-01",
    "dateModified": "2026-07-01",
    "author": { "@type": "Person", "name": "Kevin Minn", "url": "https://vindicara.io" },
    "publisher": {
      "@type": "Organization",
      "name": "Vindicara",
      "url": "https://vindicara.io",
      "logo": { "@type": "ImageObject", "url": "https://vindicara.io/vindicara-logo.png" }
    },
    "mainEntityOfPage": "https://vindicara.io/blog/acute-myeloid-leukemia-guide",
    "medicalAudience": "Patient"
  })}</script>`}
</svelte:head>

<AppShell active="blog" title="blog" scroll={true}>
  <article class="prose">
    <div class="eyebrow">Clinical</div>
    <h1>Acute Myeloid Leukemia: Symptoms, Diagnosis, Classification, and Treatment in 2026</h1>
    <p class="sub">What AML actually is, how two competing 2022 classification systems can disagree on the same patient, and where AI-assisted diagnosis honestly stands today.</p>
    <p class="muted">July 1, 2026 · Kevin Minn</p>

    <p>Acute myeloid leukemia starts in the bone marrow, where a myeloid stem cell picks up a mutation, stops maturing, and starts copying itself. The result is a marrow flooded with immature blast cells that crowd out the red cells, platelets, and functioning white cells a person needs. It moves fast, days to a few weeks in many cases, which is why it is treated as a medical urgency the moment it is suspected. We wrote the guide we wish existed when we started: sourced, current, and honest about what is settled and what is not.</p>

    <h2>Who it affects</h2>
    <p>An estimated 22,720 Americans will be diagnosed with AML in 2026, about 1.1% of all new cancer cases, per the National Cancer Institute's SEER program. It is a disease of older adults: median age at diagnosis is 70, and nearly 52% of cases occur in people 65 and older. Men are diagnosed more often than women, 5.2 versus 3.7 per 100,000 per year. The overall five-year relative survival rate is 33.4%, a number that blends a much younger, more favorable-risk population with a much older, higher-risk one, and should never be read as a prediction for an individual patient.</p>

    <h2>Symptoms that get missed</h2>
    <p>Almost every AML symptom traces back to blast cells crowding out one of the three things healthy marrow makes: fatigue, pallor, and shortness of breath from too few red cells; easy bruising, petechiae, and bleeding gums from too few platelets; fever and recurrent infection from white cells that no longer function. The problem is that all of this overlaps with viral illness, iron deficiency, or ordinary overwork. The known risk factors, prior chemotherapy, radiation, antecedent MDS, benzene exposure, smoking, only explain about 20% of cases. The other 80% arise with no identifiable external cause. Persistent, unexplained versions of these symptoms warrant a same-week complete blood count, not a wait-and-see approach.</p>

    <h2>How it is actually diagnosed</h2>
    <p>No hematologist-oncologist diagnoses AML from one test. The standard is a coordinated four-part workup on a bone marrow sample, often abbreviated MICM: <b>Morphology</b>, a hematopathologist reading blast percentage and cell appearance under a microscope; <b>Immunophenotype</b>, multiparameter flow cytometry reading surface markers; <b>Cytogenetics</b>, karyotyping and FISH reading chromosomal abnormalities; and <b>Molecular</b> testing, next-generation sequencing reading mutations in genes like NPM1, FLT3, IDH1, IDH2, and TP53. Each rung answers a question the others cannot, and the four together are what a modern diagnosis actually rests on.</p>

    <h2>Two classifications, one patient, two different answers</h2>
    <p>In 2022, two expert bodies each rewrote how AML is classified: the WHO's fifth edition and a competing framework, the International Consensus Classification (ICC). Both moved toward classifying AML more by genetics and less by a fixed blast count, but they did not converge, and the gap is not academic. Take NPM1, one of the most common and most treatable mutations in AML. WHO 2022 removed the 20% blast threshold entirely for NPM1-mutated disease: a patient can be called AML at any blast percentage. ICC 2022 instead requires at least 10% blasts; below that, the same patient is classified as a myelodysplastic syndrome, a different diagnosis with different urgency. Both systems still agree on one exception: AML with a BCR::ABL1 fusion keeps the 20% threshold under either framework, to avoid overlapping with chronic myeloid leukemia. Some centers now report both classifications on the same pathology report. The blast percentage on that report is genuinely worth a direct conversation with the treating oncologist, not a number to skim past.</p>

    <h2>Treatment in 2026</h2>
    <p>Fit patients have historically started with "7+3" induction, seven days of cytarabine plus three days of an anthracycline, followed by consolidation chemotherapy or an allogeneic stem cell transplant depending on risk group. Older or unfit patients are treated with a hypomethylating agent plus venetoclax, a BCL-2 inhibitor, an established regimen with meaningfully less toxicity. Data presented at ASH 2025 has started to question whether azacitidine plus venetoclax might outperform intensive chemotherapy in some fit patients too, early evidence worth tracking, not yet a settled standard.</p>
    <p>The bigger shift is that AML treatment is now genuinely mutation-driven. FLT3 mutations, present in roughly a quarter of cases, are targeted with midostaurin up front or gilteritinib in relapse, where the Phase 3 ADMIRAL trial showed a survival benefit over salvage chemotherapy. IDH1 and IDH2 mutations are targeted with ivosidenib and enasidenib. And KMT2A-rearranged or NPM1-mutated relapsed disease now has revumenib, the first FDA-approved menin inhibitor: approved for KMT2A translocations in November 2024, then expanded to NPM1-mutated relapsed or refractory AML in October 2025 on a 23% complete remission rate in a heavily pretreated population. Three approvals with real trial data behind them, in under two years, in a disease that moved slowly for decades.</p>

    <h2>Where AI fits, honestly</h2>
    <p>The premise behind multimodal AI here is not new: Eckardt et al. (<i>Leukemia</i>, 2022) trained a deep learning model on bone marrow smears and predicted NPM1 mutation status from image data alone at an AUROC of 0.92, evidence that morphology carries more genetic signal than a century of human reading assumed, not that it lacked the signal. What no model in this category is today, is a replacement for the workup above; tools here remain research-use triage and enrichment that still require confirmatory sequencing. Any AI tool claiming otherwise this early in the field's development is worth real skepticism, including from us.</p>

    <div class="card callout">
      <h3>Building in this space?</h3>
      <p>We are looking for clinical and pharma design partners in hematology. If you run AML trials or hold aligned multimodal data, we would like to talk.</p>
      <div class="ctas">
        <a class="btn" href="/contact">Talk to us</a>
      </div>
    </div>

    <p class="disclaimer">This article is educational and is not medical advice. AML is diagnosed and managed by a hematologist-oncologist based on a patient's complete clinical picture. If you or someone you know has symptoms consistent with AML, seek prompt evaluation with a complete blood count.</p>
    <p class="sources">Sources: <a href="https://seer.cancer.gov/statfacts/html/amyl.html" target="_blank" rel="noopener">NCI SEER Cancer Stat Facts</a> · <a href="https://www.cancer.org/cancer/types/acute-myeloid-leukemia/causes-risks-prevention/risk-factors.html" target="_blank" rel="noopener">American Cancer Society</a> · <a href="https://www.cap.org/member-resources/articles/whats-new-in-aml-classification-who-2022-vs-international-consensus-classification" target="_blank" rel="noopener">College of American Pathologists</a> · <a href="https://www.fda.gov/drugs/resources-information-approved-drugs/fda-approves-revumenib-relapsed-or-refractory-acute-myeloid-leukemia-susceptible-npm1-mutation" target="_blank" rel="noopener">FDA</a> · <a href="https://www.nature.com/articles/s41375-021-01408-w" target="_blank" rel="noopener">Eckardt et al., Leukemia (2022)</a></p>
  </article>
</AppShell>

<style>
  .prose h1{font-size:34px;margin:14px 0 0;line-height:1.15}
  .prose .sub{font-size:17px;font-weight:500;color:var(--white);margin:10px 0 8px;line-height:1.45}
  .prose .muted{font-size:13px;color:var(--soft);margin:0 0 10px}
  .prose a{color:var(--air2)}
  .prose b{color:var(--white)}
  .callout{padding:18px 20px;margin:24px 0}
  .callout h3{margin-top:0}
  .callout p{font-size:13px;color:var(--soft);line-height:1.55}
  .ctas{display:flex;flex-wrap:wrap;gap:10px;margin-top:14px}
  .disclaimer{font-size:12px;color:var(--soft);line-height:1.55;border-top:1px solid var(--line);padding-top:14px;margin-top:22px}
  .sources{font-size:12px;color:var(--soft);line-height:1.7;margin-top:10px}
</style>
