<script>
  import { createEventDispatcher } from "svelte";

  export let node;
  export let selectedNodeId = null;
  export let expandedNodeIds = [];
  export let depth = 0;

  const dispatch = createEventDispatcher();

  $: hasChildren = Boolean(node?.has_children || node?.children?.length);
  $: isExpanded = expandedNodeIds.includes(node?.id);
  $: isSelected = selectedNodeId === node?.id;

  function selectNode() {
    dispatch("selectNode", { node });
  }

  function toggleNode() {
    dispatch("toggleNode", { nodeId: node.id });
  }

  function openContract() {
    dispatch("openContract", { node });
  }
</script>

<div class="mb-1 last:mb-0">
  <div
    class={`flex items-center gap-2 rounded-xl border px-3 py-2 transition ${
      isSelected ? "border-sky-200 bg-sky-50" : "border-transparent hover:border-slate-200 hover:bg-white"
    }`}
    style={`margin-left: ${depth * 14}px;`}
  >
    {#if hasChildren}
      <button
        type="button"
        class="flex h-6 w-6 items-center justify-center rounded-full bg-white text-slate-500 shadow-sm"
        on:click|stopPropagation={toggleNode}
      >
        {isExpanded ? "−" : "+"}
      </button>
    {:else}
      <span class="flex h-6 w-6 items-center justify-center rounded-full bg-white text-xs text-slate-400 shadow-sm">
        {node.type === "contract" ? "PDF" : "•"}
      </span>
    {/if}

    <button type="button" class="min-w-0 flex-1 text-left" on:click={selectNode}>
      <p class="truncate text-sm font-medium text-slate-800">{node.title}</p>
      {#if node.badges?.length}
        <div class="mt-1 flex flex-wrap gap-1">
          {#each node.badges as badge}
            <span class="rounded-full bg-slate-200 px-2 py-0.5 text-[11px] font-medium text-slate-600">
              {badge}
            </span>
          {/each}
        </div>
      {/if}
    </button>

    {#if node.type === "contract" && node.preview_available}
      <button
        type="button"
        class="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-700 transition hover:border-sky-200 hover:text-sky-700"
        on:click|stopPropagation={openContract}
      >
        Open
      </button>
    {/if}
  </div>

  {#if hasChildren && isExpanded}
    <div class="mt-1">
      {#each node.children as child}
        <svelte:self
          node={child}
          {selectedNodeId}
          {expandedNodeIds}
          depth={depth + 1}
          on:selectNode
          on:toggleNode
          on:openContract
        />
      {/each}
    </div>
  {/if}
</div>
