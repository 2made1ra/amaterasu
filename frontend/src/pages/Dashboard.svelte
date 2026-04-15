<script>
  import { onMount } from "svelte";
  import { navigate } from "../lib/router";
  import api from "../lib/api";
  import Chat from "../components/Chat.svelte";
  import DocumentUpload from "../components/DocumentUpload.svelte";

  let user = null;
  let activeDocumentId = null;

  onMount(async () => {
    try {
      const res = await api.get("/auth/me");
      user = res.data;
    } catch (err) {
      localStorage.removeItem("token");
      navigate("/", { replace: true });
    }
  });

  function handleLogout() {
    localStorage.removeItem("token");
    navigate("/", { replace: true });
  }
</script>

{#if user}
<div class="h-screen flex overflow-hidden bg-gray-100">
  <!-- Sidebar for Documents -->
  <div class="w-1/3 max-w-sm bg-white border-r flex flex-col">
    <div class="p-4 border-b flex justify-between items-center bg-gray-50">
      <div class="font-bold text-gray-800">AI Assistant</div>
      <button on:click={handleLogout} class="text-sm text-red-600 hover:text-red-800">Logout</button>
    </div>

    <div class="flex-1 overflow-y-auto p-4">
      <DocumentUpload on:documentSelected={(e) => activeDocumentId = e.detail} />
    </div>
  </div>

  <!-- Chat Area -->
  <div class="flex-1 flex flex-col">
    <Chat {activeDocumentId} />
  </div>
</div>
{/if}
