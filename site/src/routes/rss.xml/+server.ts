import type { RequestHandler } from '@sveltejs/kit';

export const prerender = true;

const SITE = 'https://vindicara.io';

type Post = {
  slug: string;
  title: string;
  description: string;
  date: string;
  category: string;
};

const posts: Post[] = [
  {
    slug: 'trustworthy-agents-forensic-evidence',
    title: 'Implementing Trustworthy Agents: A Forensic Evidence Layer for Production',
    description:
      "Anthropic's April 9 paper on trustworthy agents names three ecosystem gaps. Project AIR is our answer to evidence sharing and open standards, and a concrete contribution to a problem no single company can solve alone.",
    date: '2026-04-24',
    category: 'Perspective',
  },
  {
    slug: 'secure-ai-agents-5-minutes',
    title: 'Run your first `air trace` in 5 minutes',
    description:
      'From pip install projectair to a signed forensic timeline of your LangChain agent in under five minutes. The air CLI and airsdk are MIT-licensed and open source today.',
    date: '2026-04-18',
    category: 'Quickstart',
  },
  {
    slug: 'eu-ai-act-article-72-guide',
    title: "EU AI Act Article 72: A Developer's Guide to Post-Market Monitoring",
    description:
      'The enforcement deadline is August 2, 2026. Article 72 requires continuous post-market monitoring for high-risk AI systems. Here is what your engineering team needs to build, and how to automate most of it.',
    date: '2026-04-02',
    category: 'Compliance',
  },
  {
    slug: 'mcp-security-2026',
    title: 'The State of MCP Security in 2026',
    description:
      '92% of MCP servers lack proper OAuth. We scanned real configurations and found critical vulnerabilities across authentication, authorization, and resource management.',
    date: '2026-04-02',
    category: 'Research',
  },
];

function escapeXml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

export const GET: RequestHandler = () => {
  const lastBuildDate = new Date(posts[0].date).toUTCString();
  const items = posts
    .map((post) => {
      const url = `${SITE}/blog/${post.slug}`;
      const pubDate = new Date(post.date).toUTCString();
      return `    <item>
      <title>${escapeXml(post.title)}</title>
      <link>${url}</link>
      <guid isPermaLink="true">${url}</guid>
      <pubDate>${pubDate}</pubDate>
      <category>${escapeXml(post.category)}</category>
      <description>${escapeXml(post.description)}</description>
    </item>`;
    })
    .join('\n');

  const body = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Vindicara AIR Blog</title>
    <link>${SITE}/blog</link>
    <atom:link href="${SITE}/rss.xml" rel="self" type="application/rss+xml" />
    <description>Forensic reconstruction and incident response for AI agents. Research, compliance guides, and engineering deep-dives from the team behind Project AIR™.</description>
    <language>en-us</language>
    <lastBuildDate>${lastBuildDate}</lastBuildDate>
${items}
  </channel>
</rss>
`;

  return new Response(body, {
    headers: {
      'Content-Type': 'application/xml; charset=utf-8',
      'Cache-Control': 'max-age=0, s-maxage=3600',
    },
  });
};
