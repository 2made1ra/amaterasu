<script>
  import { createEventDispatcher } from "svelte";

  export let sessionTitle = "New workspace";
  export let messages = [];
  export let hasActiveSession = false;
  export let isLoading = false;
  export let isSending = false;
  export let errorMessage = "";

  const dispatch = createEventDispatcher();

  let inputQuery = "";

  function submit() {
    if (!inputQuery.trim() || isSending) return;
    dispatch("send", { query: inputQuery.trim() });
    inputQuery = "";
  }

  function handleKeydown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  }
</script>

<section class="flex h-full flex-col rounded-[28px] border border-slate-200/80 bg-white/90 shadow-[0_18px_40px_rgba(15,23,42,0.05)]">
  <div class="border-b border-slate-200/80 px-5 py-4">
    <div class="flex items-center justify-between gap-3">
      <div>
        <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">Agent chat</p>
        <h2 class="mt-1 text-lg font-semibold text-slate-900">{sessionTitle}</h2>
      </div>
      <span class="rounded-full bg-emerald-100 px-3 py-1 text-xs font-medium text-emerald-700">
        Main session
      </span>
    </div>
  </div>

  <div class="flex-1 overflow-y-auto px-5 py-4">
    {#if isLoading}
      <div class="flex h-full items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-8 text-sm text-slate-500">
        Loading conversation...
      </div>
    {:else if messages.length === 0}
      <div class="flex h-full flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-[linear-gradient(180deg,rgba(248,250,252,1),rgba(241,245,249,0.8))] px-6 py-10 text-center">
        <p class="text-sm font-medium text-slate-700">{hasActiveSession ? "This session is ready for a new search." : "Create or continue a session to begin."}</p>
        <p class="mt-2 max-w-sm text-sm text-slate-500">
          Ask for contracts, deadlines, suppliers, or anything else you want the workspace to capture.
        </p>
      </div>
    {:else}
      <div class="space-y-4">
        {#each messages as msg}
          <div class={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              class={`max-w-3xl rounded-3xl px-4 py-3 text-sm shadow-sm ${
                msg.role === "user"
                  ? "rounded-br-md bg-slate-900 text-white"
                  : "rounded-bl-md bg-slate-100 text-slate-800"
              }`}
            >
              <p class="whitespace-pre-wrap">{msg.content}</p>
            </div>
          </div>
        {/each}

        {#if isSending}
          <div class="flex justify-start">
            <div class="max-w-3xl rounded-3xl rounded-bl-md bg-slate-100 px-4 py-3 text-sm text-slate-500 shadow-sm">
              Working through the workspace...
            </div>
          </div>
        {/if}
      </div>
    {/if}
  </div>

  <div class="border-t border-slate-200/80 px-5 py-4">
    {#if errorMessage}
      <div class="mb-3 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
        {errorMessage}
      </div>
    {/if}

    <div class="flex items-end gap-3">
      <textarea
        bind:value={inputQuery}
        rows="3"
        placeholder="Ask about contracts, deadlines, suppliers, or a previous result set..."
        class="min-h-[76px] flex-1 rounded-3xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 outline-none transition focus:border-sky-300 focus:ring-4 focus:ring-sky-100"
        on:keydown={handleKeydown}
      ></textarea>
      <button
        type="button"
        class="rounded-3xl bg-sky-600 px-5 py-3 text-sm font-medium text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-slate-300"
        disabled={isSending || !inputQuery.trim()}
        on:click={submit}
      >
        Send
      </button>
    </div>
  </div>
</section>
