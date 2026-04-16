<script>
  import { createEventDispatcher } from "svelte";

  import DocumentUpload from "./DocumentUpload.svelte";

  export let username = "";
  export let documentsCount = 0;
  export let activeSessionTitle = "New workspace";

  const dispatch = createEventDispatcher();

  let showImporter = false;

  function toggleImporter() {
    showImporter = !showImporter;
  }
</script>

<div class="rounded-[28px] border border-slate-200/70 bg-[linear-gradient(135deg,rgba(255,255,255,0.96),rgba(240,247,255,0.9))] px-4 py-4 shadow-[0_18px_40px_rgba(15,23,42,0.06)]">
  <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
    <div class="space-y-1">
      <p class="text-xs font-semibold uppercase tracking-[0.28em] text-sky-700">Amaterasu workspace</p>
      <div class="flex flex-col gap-1 lg:flex-row lg:items-center lg:gap-3">
        <h1 class="text-2xl font-semibold text-slate-900">Contracts cockpit</h1>
        <span class="inline-flex w-fit items-center rounded-full bg-sky-100 px-3 py-1 text-xs font-medium text-sky-800">
          {documentsCount} contracts in library
        </span>
      </div>
      <p class="text-sm text-slate-500">Active session: {activeSessionTitle}</p>
    </div>

    <div class="flex flex-wrap items-center gap-2">
      <span class="rounded-full border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600">
        {username}
      </span>
      <button
        type="button"
        class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-sky-200 hover:text-sky-700"
        on:click={() => dispatch("createSession")}
      >
        New session
      </button>
      <button
        type="button"
        class="rounded-full bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800"
        on:click={toggleImporter}
      >
        {showImporter ? "Close import" : "Import contract"}
      </button>
      <button
        type="button"
        class="rounded-full border border-rose-200 bg-rose-50 px-4 py-2 text-sm font-medium text-rose-700 transition hover:bg-rose-100"
        on:click={() => dispatch("logout")}
      >
        Logout
      </button>
    </div>
  </div>

  {#if showImporter}
    <div class="mt-4 border-t border-slate-200/80 pt-4">
      <DocumentUpload on:documentsChanged />
    </div>
  {/if}
</div>
