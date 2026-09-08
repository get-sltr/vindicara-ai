<script lang="ts">
  import { page } from '$app/stores';
  import RunDetail from '$lib/console/screens/RunDetail.svelte';
</script>

{#key $page.params.run_id}
  <RunDetail runId={$page.params.run_id ?? ''} />
{/key}
