<script>
  import api from "../lib/api";

  export let documentId = null;
  export let title = "";

  let messages = [];
  let inputQuery = "";
  let isSending = false;
  let errorMessage = "";
  let previousDocumentId = null;

  function resetConversation() {
    messages = [
      {
        role: "assistant",
        content: `Ask anything about "${title}". This modal chat is temporary and will not be saved to session history.`
      }
    ];
    inputQuery = "";
    errorMessage = "";
  }

  $: if (documentId && documentId !== previousDocumentId) {
    previousDocumentId = documentId;
    resetConversation();
  }

  async function sendMessage() {
    if (!inputQuery.trim() || isSending) return;

    const query = inputQuery.trim();
    messages = [...messages, { role: "user", content: query }];
    inputQuery = "";
    isSending = true;
    errorMessage = "";

    try {
      const res = await api.post(`/documents/${documentId}/chat`, { query });
      messages = [...messages, { role: "assistant", content: res.data.answer }];
    } catch (err) {
      errorMessage = err.response?.data?.detail || "The contract chat is unavailable right now.";
      messages = [
        ...messages,
        { role: "assistant", content: "I could not answer in this temporary contract view. Please try again." }
      ];
    } finally {
      isSending = false;
    }
  }

  function handleKeydown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }
</script>

<section class="flex min-h-0 flex-col bg-white">
  <div class="border-b border-slate-200 px-5 py-4">
    <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">Temporary contract chat</p>
    <h3 class="mt-1 text-lg font-semibold text-slate-900">{title}</h3>
  </div>

  <div class="flex-1 space-y-4 overflow-y-auto px-5 py-4">
    {#each messages as msg}
      <div class={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
        <div
          class={`max-w-2xl rounded-3xl px-4 py-3 text-sm shadow-sm ${
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
        <div class="max-w-2xl rounded-3xl rounded-bl-md bg-slate-100 px-4 py-3 text-sm text-slate-500 shadow-sm">
          Reviewing this contract...
        </div>
      </div>
    {/if}
  </div>

  <div class="border-t border-slate-200 px-5 py-4">
    {#if errorMessage}
      <div class="mb-3 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
        {errorMessage}
      </div>
    {/if}

    <div class="flex items-end gap-3">
      <textarea
        bind:value={inputQuery}
        rows="3"
        placeholder="Ask about this contract only..."
        class="min-h-[76px] flex-1 rounded-3xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 outline-none transition focus:border-sky-300 focus:ring-4 focus:ring-sky-100"
        on:keydown={handleKeydown}
      ></textarea>
      <button
        type="button"
        class="rounded-3xl bg-slate-900 px-5 py-3 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
        disabled={isSending || !inputQuery.trim()}
        on:click={sendMessage}
      >
        Ask
      </button>
    </div>
  </div>
</section>
