<script>
  import Login from "./pages/Login.svelte";
  import Dashboard from "./pages/Dashboard.svelte";
  import { currentPath, navigate } from "./lib/router";

  // Redirect unknown routes to login.
  $: if ($currentPath !== "/" && $currentPath !== "/dashboard") {
    navigate("/", { replace: true });
  }
</script>

{#if $currentPath === "/dashboard"}
  <Dashboard />
{:else}
  <Login />
{/if}
