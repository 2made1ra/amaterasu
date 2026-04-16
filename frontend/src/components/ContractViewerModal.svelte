<script>
  import { createEventDispatcher } from "svelte";

  import ContractChatPanel from "./ContractChatPanel.svelte";
  import ContractPreviewPane from "./ContractPreviewPane.svelte";

  export let open = false;
  export let node = null;

  const dispatch = createEventDispatcher();

  function handleKeydown(event) {
    if (open && event.key === "Escape") {
      dispatch("close");
    }
  }
</script>

<svelte:window on:keydown={handleKeydown} />

{#if open && node}
  <div class="fixed inset-0 z-[120] flex items-center justify-center bg-slate-950/45 p-3 backdrop-blur-sm md:p-6">
    <div class="flex h-[92vh] w-full max-w-7xl flex-col overflow-hidden rounded-[32px] border border-white/60 bg-white shadow-[0_30px_120px_rgba(15,23,42,0.3)]">
      <div class="flex items-center justify-between border-b border-slate-200 px-5 py-4">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">Contract workspace</p>
          <h2 class="mt-1 text-xl font-semibold text-slate-900">{node.title}</h2>
        </div>
        <button
          type="button"
          class="rounded-full border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
          on:click={() => dispatch("close")}
        >
          Close
        </button>
      </div>

      <div class="grid min-h-0 flex-1 gap-0 xl:grid-cols-[1.15fr_0.85fr]">
        <ContractPreviewPane documentId={node.document_id} title={node.title} />
        <ContractChatPanel documentId={node.document_id} title={node.title} />
      </div>
    </div>
  </div>
{/if}
