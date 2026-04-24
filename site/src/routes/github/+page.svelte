<script lang="ts">
  import { onMount } from 'svelte';

  // Canonical GitHub destination. Change this single line whenever the repo moves.
  // The site, blog posts, README badges, and external CTAs all point at /github,
  // so a repo transfer (or a future trademark-recovered org rename) needs no
  // content sweep. GitHub also auto-redirects transferred repos for inbound
  // links that bypassed this shortcut, so dual-redirection is safe.
  const GITHUB_URL = 'https://github.com/vindicara-inc/projectair';

  onMount(() => {
    window.location.replace(GITHUB_URL);
  });
</script>

<svelte:head>
  <title>Redirecting to GitHub | Vindicara</title>
  <meta name="robots" content="noindex" />
  <meta http-equiv="refresh" content="0; url=https://github.com/vindicara-inc/projectair" />
  <link rel="canonical" href="https://github.com/vindicara-inc/projectair" />
</svelte:head>

<section class="py-24">
  <div class="max-w-screen-md mx-auto px-6 text-center">
    <p class="text-brand-red text-sm font-semibold uppercase tracking-wider mb-3">Redirecting</p>
    <h1 class="text-2xl sm:text-3xl font-bold tracking-tight">Opening the Project AIR repository on GitHub.</h1>
    <p class="mt-4 text-zinc-400">
      If your browser does not redirect automatically, continue to
      <a href={GITHUB_URL} class="text-brand-red underline hover:text-brand-red/80">{GITHUB_URL}</a>.
    </p>
  </div>
</section>
