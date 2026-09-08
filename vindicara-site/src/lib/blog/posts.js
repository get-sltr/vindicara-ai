// Single source of truth for the blog index and the /rss.xml feed. Dates are
// ISO (YYYY-MM-DD); display formatting happens at the call site. Newest first.
export const posts = [
  {
    title: 'Acute Myeloid Leukemia in 2026: Symptoms, Diagnosis, Classification, Treatment',
    description: 'Why WHO 2022 and ICC 2022 can classify the same AML patient differently, the MICM diagnostic workup, and the 2026 treatment landscape from 7+3 to menin inhibitors.',
    tag: 'Clinical',
    href: '/blog/acute-myeloid-leukemia-guide',
    date: '2026-07-01'
  },
  {
    title: 'An NVIDIA-backed second opinion, signed',
    description: 'How NemoGuard NIM classifier verdicts become signed detector findings in the AIR evidence chain.',
    tag: 'Engineering',
    href: '/blog/nvidia-inception-nemoguard-second-opinion',
    date: '2026-06-10'
  },
  {
    title: '88% of AI Agent Deployments Had a Security Incident. 6% Have a Budget to Fix It.',
    description: 'The state of AI agent accountability in 2026: the incidents, the converging regulatory deadlines, and the evidence infrastructure gap.',
    tag: 'Strategy',
    href: '/blog/ai-agent-accountability-crisis-2026',
    date: '2026-05-27'
  },
  {
    title: 'Introducing Project AIR',
    description: 'Evidence-grade infrastructure for accountable AI agents: signed intent capsules, 16 OWASP-mapped detectors, causal explanation, Auth0 containment, and cross-agent chain of custody.',
    tag: 'Launch',
    href: '/blog/introducing-project-air',
    date: '2026-05-26'
  },
  {
    title: 'They Check Messages. We Check Missions.',
    description: 'Structural Verification: a deterministic floor that checks whether the agent’s actual trajectory served its declared intent, and cannot be prompt-injected.',
    tag: 'Engineering',
    href: '/blog/structural-verification',
    date: '2026-05-13'
  },
  {
    title: 'The New HIPAA AI Audit Problem (and How to Solve It)',
    description: 'The HIPAA Security Rule NPRM makes audit controls mandatory. AI agents touching PHI need cryptographic evidence chains, not application logs.',
    tag: 'Compliance',
    href: '/blog/hipaa-ai-audit-problem',
    date: '2026-05-12'
  },
  {
    title: 'Forensic Evidence for NemoClaw: HIPAA Audit Trails for Sandboxed Clinical AI',
    description: 'NVIDIA NemoClaw controls what clinical AI agents can do. Project AIR proves what they did. Prevention plus evidence for regulated healthcare.',
    tag: 'Engineering',
    href: '/blog/nemoclaw-forensic-evidence',
    date: '2026-05-12'
  },
  {
    title: 'What happens after an AI agent does something it shouldn’t?',
    description: 'A map of AI agent security tooling, and the post-incident forensic layer most teams don’t realize they’re missing.',
    tag: 'Strategy',
    href: '/blog/forensic-layer-market-map',
    date: '2026-05-02'
  },
  {
    title: 'Implementing Trustworthy Agents: A Forensic Evidence Layer for Production',
    description: 'Anthropic’s paper on trustworthy agents names three ecosystem gaps. Project AIR is our answer to evidence sharing and open standards.',
    tag: 'Strategy',
    href: '/blog/trustworthy-agents-forensic-evidence',
    date: '2026-04-24'
  },
  {
    title: 'Run your first air trace in 5 minutes',
    description: 'From pip install projectair to a signed forensic timeline of your LangChain agent in under five minutes.',
    tag: 'Engineering',
    href: '/blog/secure-ai-agents-5-minutes',
    date: '2026-04-02'
  },
  {
    title: 'EU AI Act Article 72: A Developer’s Guide to Post-Market Monitoring',
    description: 'What post-market monitoring evidence actually has to contain by August 2, 2026, and how to automate producing it.',
    tag: 'Compliance',
    href: '/blog/eu-ai-act-article-72-guide',
    date: '2026-04-02'
  },
  {
    title: 'The State of MCP Security in 2026',
    description: '92% of MCP servers lack proper OAuth. We scanned real configurations and found critical vulnerabilities across authentication and authorization.',
    tag: 'Engineering',
    href: '/blog/mcp-security-2026',
    date: '2026-04-02'
  }
];

/**
 * Format an ISO date (YYYY-MM-DD) as "Month D, YYYY" for display, in UTC so the
 * output does not shift with the server's local timezone.
 * @param {string} iso
 */
export function displayDate(iso) {
  return new Date(`${iso}T00:00:00Z`).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    timeZone: 'UTC'
  });
}
