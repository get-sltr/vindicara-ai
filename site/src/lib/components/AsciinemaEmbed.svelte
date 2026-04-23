<script lang="ts">
  import { onMount } from 'svelte';

  interface Props {
    src: string;
    autoPlay?: boolean;
    loop?: boolean;
    speed?: number;
    idleTimeLimit?: number;
    theme?: string;
  }

  let {
    src,
    autoPlay = false,
    loop = true,
    speed = 1.6,
    idleTimeLimit = 1,
    theme = 'asciinema',
  }: Props = $props();

  let container: HTMLDivElement | undefined = $state();

  onMount(async () => {
    if (!container) return;
    const AsciinemaPlayer = await import('asciinema-player');
    await import('asciinema-player/dist/bundle/asciinema-player.css');
    AsciinemaPlayer.create(src, container, {
      autoPlay,
      loop,
      speed,
      idleTimeLimit,
      theme,
      fit: 'width',
    });
  });
</script>

<div bind:this={container} class="asciinema-container"></div>

<style>
  .asciinema-container {
    width: 100%;
    max-width: 100%;
    overflow: hidden;
    border-radius: 0.5rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
    background: #000;
  }

  /* Asciinema player's default styling is fine, but we tighten a few things
     to fit the Vindicara dark theme. */
  .asciinema-container :global(.asciinema-player) {
    font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
  }
  .asciinema-container :global(.asciinema-terminal) {
    padding: 1rem !important;
  }
</style>
