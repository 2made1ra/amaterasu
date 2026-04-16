<script>
  import { onDestroy } from "svelte";

  import api from "../lib/api";

  export let documentId = null;
  export let title = "";

  let previewUrl = "";
  let isLoading = false;
  let errorMessage = "";

  async function loadPreview() {
    if (!documentId) return;

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      previewUrl = "";
    }

    isLoading = true;
    errorMessage = "";

    try {
      const res = await api.get(`/documents/${documentId}/preview`, {
        responseType: "blob"
      });
      previewUrl = URL.createObjectURL(res.data);
    } catch (err) {
      errorMessage = err.response?.data?.detail || "Could not load the contract preview.";
    } finally {
      isLoading = false;
    }
  }

  $: if (documentId) {
    loadPreview();
  }

  onDestroy(() => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
  });
</script>

<section class="flex min-h-0 flex-col border-b border-slate-200 bg-slate-50 xl:border-b-0 xl:border-r">
  <div class="border-b border-slate-200 bg-white px-5 py-4">
    <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">Preview</p>
    <h3 class="mt-1 text-lg font-semibold text-slate-900">{title}</h3>
  </div>

  <div class="flex-1 p-4">
    {#if isLoading}
      <div class="flex h-full items-center justify-center rounded-[24px] border border-dashed border-slate-300 bg-white px-4 py-8 text-sm text-slate-500">
        Loading preview...
      </div>
    {:else if errorMessage}
      <div class="flex h-full items-center justify-center rounded-[24px] border border-rose-200 bg-rose-50 px-6 py-10 text-center text-sm text-rose-700">
        {errorMessage}
      </div>
    {:else if previewUrl}
      <iframe title={title} src={previewUrl} class="h-full w-full rounded-[24px] border border-slate-200 bg-white"></iframe>
    {:else}
      <div class="flex h-full items-center justify-center rounded-[24px] border border-dashed border-slate-300 bg-white px-4 py-8 text-sm text-slate-500">
        No preview available.
      </div>
    {/if}
  </div>
</section>
