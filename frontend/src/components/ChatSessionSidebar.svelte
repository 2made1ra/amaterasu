<script>
  import { createEventDispatcher } from "svelte";

  export let sessions = [];
  export let activeSessionId = null;
  export let isLoading = false;
  export let errorMessage = "";
  export let deletingSessionId = null;
  export let disableActions = false;

  const dispatch = createEventDispatcher();

  function formatTimestamp(value) {
    if (!value) return "No activity yet";
    return new Intl.DateTimeFormat(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    }).format(new Date(value));
  }
</script>

<section class="flex h-full flex-col rounded-[28px] border border-slate-200/80 bg-white/90 p-4 shadow-[0_18px_40px_rgba(15,23,42,0.05)]">
  <div class="mb-4 flex items-center justify-between">
    <div>
      <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">Session history</p>
      <h2 class="mt-1 text-lg font-semibold text-slate-900">Manager chats</h2>
    </div>
    <button
      type="button"
      class="rounded-full border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-700 transition hover:border-sky-200 hover:text-sky-700"
      on:click={() => dispatch("createSession")}
    >
      New
    </button>
  </div>

  {#if errorMessage}
    <div class="mb-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
      {errorMessage}
    </div>
  {/if}

  {#if isLoading && sessions.length === 0}
    <div class="flex flex-1 items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-8 text-sm text-slate-500">
      Loading sessions...
    </div>
  {:else if sessions.length === 0}
    <div class="flex flex-1 flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-8 text-center">
      <p class="text-sm font-medium text-slate-700">No saved workspaces yet.</p>
      <p class="mt-2 text-sm text-slate-500">Create a session, then start asking about your contracts.</p>
    </div>
  {:else}
    <div class="flex-1 space-y-2 overflow-y-auto pr-1">
      {#each sessions as session}
        <div
          class={`flex items-start gap-2 rounded-2xl border px-3 py-3 transition ${
            session.id === activeSessionId
              ? "border-sky-200 bg-sky-50 shadow-[0_8px_18px_rgba(14,116,144,0.09)]"
              : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50"
          }`}
        >
          <button
            type="button"
            class="min-w-0 flex-1 text-left"
            disabled={disableActions}
            on:click={() => dispatch("selectSession", { sessionId: session.id })}
          >
            <div>
              <p class="line-clamp-2 text-sm font-semibold text-slate-900">{session.title}</p>
              <p class="mt-2 text-xs text-slate-500">{formatTimestamp(session.last_message_at)}</p>
            </div>
          </button>

          <div class="flex items-center gap-2">
            <span class="rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">
              {session.message_count || 0}
            </span>
            <button
              type="button"
              class="rounded-full border border-rose-200 bg-white px-3 py-1.5 text-xs font-medium text-rose-700 transition hover:bg-rose-50 disabled:cursor-not-allowed disabled:border-slate-200 disabled:text-slate-400"
              disabled={disableActions || deletingSessionId === session.id}
              on:click={() => dispatch("deleteSession", { sessionId: session.id, title: session.title })}
            >
              {#if deletingSessionId === session.id}
                Deleting...
              {:else}
                Delete
              {/if}
            </button>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</section>
