<script>
  import { Router, Route, link } from "svelte-routing";
  import Login from "./pages/Login.svelte";
  import Dashboard from "./pages/Dashboard.svelte";

  export let url = "";
</script>

<Router {url}>
  <Route path="/" component={Login} />
  <Route path="/dashboard" component={Dashboard} />
</Router>
