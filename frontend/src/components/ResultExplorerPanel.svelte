<script>
  import { createEventDispatcher } from "svelte";

  import ResultTreeNode from "./ResultTreeNode.svelte";

  export let snapshot = {
    result_tree: [],
    selected_node_id: null,
    expanded_node_ids: [],
    view_mode: "flat"
  };
  export let isLoading = false;
  export let errorMessage = "";

  const dispatch = createEventDispatcher();
</script>

<section class="flex h-full flex-col rounded-[28px] border border-slate-200/80 bg-white/90 p-4 shadow-[0_18px_40px_rgba(15,23,42,0.05)]">
  <div class="mb-4 flex items-start justify-between gap-3">
    <div>
      <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">Results explorer</p>
      <h2 class="mt-1 text-lg font-semibold text-slate-900">Contracts and folders</h2>
    </div>
    <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
      {snapshot.view_mode || "flat"}
    </span>
  </div>

  {#if errorMessage}
    <div class="mb-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
      {errorMessage}
    </div>
  {/if}

  {#if isLoading}
    <div class="flex flex-1 items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-8 text-sm text-slate-500">
      Restoring explorer state...
    </div>
  {:else if !snapshot.result_tree || snapshot.result_tree.length === 0}
    <div class="flex flex-1 flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-[linear-gradient(180deg,rgba(248,250,252,1),rgba(241,245,249,0.8))] px-6 py-10 text-center">
      <p class="text-sm font-medium text-slate-700">No results saved in this session.</p>
      <p class="mt-2 max-w-sm text-sm text-slate-500">
        Ask the agent a question and matching contracts will appear here as a reusable workspace snapshot.
      </p>
    </div>
  {:else}
    <div class="flex-1 overflow-y-auto rounded-2xl border border-slate-200 bg-slate-50/70 p-3">
      {#each snapshot.result_tree as node}
        <ResultTreeNode
          {node}
          selectedNodeId={snapshot.selected_node_id}
          expandedNodeIds={snapshot.expanded_node_ids || []}
          on:selectNode={(event) => dispatch("selectNode", event.detail)}
          on:toggleNode={(event) => dispatch("toggleNode", event.detail)}
          on:openContract={(event) => dispatch("openContract", event.detail)}
        />
      {/each}
    </div>
  {/if}
</section>
