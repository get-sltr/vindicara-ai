<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>Vindicara | Runtime Security for Autonomous AI</title>
	<meta name="description" content="The control plane for AI agents in production. Intercept every input and output, enforce policies in real time, secure MCP connections, and generate compliance evidence automatically. Developer-first. Model-agnostic. Independent." />
	<meta name="keywords" content="AI security, AI guardrails, MCP security, agent security, runtime security, AI compliance, EU AI Act, prompt injection defense, LLM security, agentic AI, AI governance" />

	<!-- Open Graph -->
	<meta property="og:type" content="website" />
	<meta property="og:url" content="https://vindicara.io" />
	<meta property="og:title" content="Vindicara | Runtime Security for Autonomous AI" />
	<meta property="og:description" content="The control plane for AI agents in production. Enforce policies, secure MCP connections, detect behavioral drift, and generate compliance evidence. pip install vindicara." />
	<meta property="og:site_name" content="Vindicara" />

	<!-- Twitter / X -->
	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:site" content="@vindicara" />
	<meta name="twitter:title" content="Vindicara | Runtime Security for Autonomous AI" />
	<meta name="twitter:description" content="The control plane for AI agents in production. Enforce policies, secure MCP connections, detect behavioral drift, and generate compliance evidence." />

	<!-- Canonical -->
	<link rel="canonical" href="https://vindicara.io" />

	<!-- Theme -->
	<meta name="theme-color" content="#0a0a0f" />
</svelte:head>

{@render children()}
