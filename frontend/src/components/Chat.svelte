<script>
  import api from "../lib/api";

  export let activeDocumentId = null;

  let messages = [
    { role: 'assistant', content: 'Hello! How can I help you with your contracts today?' }
  ];
  let inputQuery = "";
  let isSending = false;

  async function sendMessage() {
    if (!inputQuery.trim() || isSending) return;

    const query = inputQuery.trim();
    messages = [...messages, { role: 'user', content: query }];
    inputQuery = "";
    isSending = true;

    try {
      const res = await api.post("/chat/", {
        query: query,
        document_id: activeDocumentId
      });
      messages = [...messages, { role: 'assistant', content: res.data.answer }];
    } catch (e) {
      messages = [...messages, { role: 'assistant', content: "Sorry, I encountered an error. Please try again." }];
    } finally {
      isSending = false;
    }
  }

  function handleKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }
</script>

<div class="flex-1 flex flex-col h-full bg-white relative">
  <!-- Chat Header -->
  <div class="p-4 border-b bg-white shadow-sm z-10 flex justify-between items-center">
    <h2 class="text-lg font-semibold text-gray-800">
      {activeDocumentId ? `Document Chat (ID: ${activeDocumentId})` : 'Global Knowledge Base'}
    </h2>
    <span class="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded-full">
      {activeDocumentId ? 'Local Search' : 'Global Search'}
    </span>
  </div>

  <!-- Messages -->
  <div class="flex-1 overflow-y-auto p-4 space-y-4">
    {#each messages as msg}
      <div class="flex {msg.role === 'user' ? 'justify-end' : 'justify-start'}">
        <div class="max-w-3xl rounded-lg px-4 py-2 {msg.role === 'user' ? 'bg-blue-600 text-white rounded-br-none' : 'bg-gray-100 text-gray-800 rounded-bl-none'}">
          <p class="whitespace-pre-wrap">{msg.content}</p>
        </div>
      </div>
    {/each}
    {#if isSending}
      <div class="flex justify-start">
        <div class="max-w-3xl rounded-lg px-4 py-2 bg-gray-100 text-gray-800 rounded-bl-none">
          <p class="animate-pulse">Thinking...</p>
        </div>
      </div>
    {/if}
  </div>

  <!-- Input -->
  <div class="p-4 border-t bg-white">
    <div class="flex space-x-2">
      <textarea
        bind:value={inputQuery}
        on:keydown={handleKeydown}
        placeholder="Ask a question about your contracts..."
        class="flex-1 border border-gray-300 rounded-md p-2 focus:ring-blue-500 focus:border-blue-500 resize-none h-12"
        rows="1"
      ></textarea>
      <button
        on:click={sendMessage}
        disabled={isSending || !inputQuery.trim()}
        class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400"
      >
        Send
      </button>
    </div>
  </div>
</div>
