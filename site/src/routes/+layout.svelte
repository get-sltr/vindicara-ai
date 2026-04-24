<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<link rel="alternate" type="application/rss+xml" title="Vindicara AIR Blog" href="https://vindicara.io/rss.xml" />

	<!-- Site-wide OG/Twitter defaults. Per-page <svelte:head> blocks override title/description/url/image. -->
	<meta property="og:site_name" content="Vindicara" />
	<meta property="og:image" content="https://vindicara.io/og-image.png" />
	<meta property="og:image:width" content="1200" />
	<meta property="og:image:height" content="630" />

	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:site" content="@AIRbyVindicara" />
	<meta name="twitter:image" content="https://vindicara.io/og-image.png" />

	<meta name="theme-color" content="#0a0a0f" />

	<!-- Organization + WebSite graph. Per-page schemas live in their own <svelte:head>. -->
	{@html `<script type="application/ld+json">${JSON.stringify({
		'@context': 'https://schema.org',
		'@graph': [
			{
				'@type': 'Organization',
				'@id': 'https://vindicara.io/#organization',
				name: 'Vindicara',
				url: 'https://vindicara.io',
				logo: 'https://vindicara.io/og-image.png',
				sameAs: ['https://github.com/vindicara-inc/projectair', 'https://x.com/AIRbyVindicara', 'https://linkedin.com/company/vindicara-ai'],
			},
			{
				'@type': 'WebSite',
				'@id': 'https://vindicara.io/#website',
				url: 'https://vindicara.io',
				name: 'Vindicara',
				publisher: { '@id': 'https://vindicara.io/#organization' },
			},
		],
	})}<\/script>`}
</svelte:head>

{@render children()}
