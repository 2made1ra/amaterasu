<script>
  import { createEventDispatcher, onDestroy, onMount } from "svelte";
  import api from "../lib/api";

  const dispatch = createEventDispatcher();

  let files = null;
  let isUploading = false;
  let documents = [];

  // HitL Modal State
  let showConfirmModal = false;
  let showSuccessModal = false;
  let pendingDoc = null;
  let editedDeadline = "";
  let isConfirming = false;
  let successTimer = null;

  onMount(async () => {
    fetchDocuments();
  });

  onDestroy(() => {
    if (successTimer) {
      clearTimeout(successTimer);
    }
  });

  async function fetchDocuments() {
    try {
      const res = await api.get("/documents/");
      documents = res.data;
    } catch (e) {
      console.error(e);
    }
  }

  async function uploadDocument() {
    if (!files || files.length === 0) return;

    isUploading = true;
    const formData = new FormData();
    formData.append("file", files[0]);

    try {
      const res = await api.post("/documents/upload", formData);
      pendingDoc = res.data;
      if (pendingDoc.extracted_deadline) {
        // Format for input type="date"
        editedDeadline = new Date(pendingDoc.extracted_deadline).toISOString().split("T")[0];
      } else {
        editedDeadline = "";
      }
      showConfirmModal = true;
    } catch (e) {
      alert("Upload failed: " + (e.response?.data?.detail || e.message));
    } finally {
      isUploading = false;
      files = null;
    }
  }

  function clearPendingDocument() {
    pendingDoc = null;
    editedDeadline = "";
  }

  function closeConfirmModal() {
    if (isConfirming) return;

    showConfirmModal = false;
    clearPendingDocument();
  }

  function showSuccessState() {
    showSuccessModal = true;

    if (successTimer) {
      clearTimeout(successTimer);
    }

    successTimer = setTimeout(() => {
      showSuccessModal = false;
      successTimer = null;
    }, 2200);
  }

  async function confirmDocument() {
    if (!pendingDoc || isConfirming) return;

    isConfirming = true;

    try {
      const formData = new FormData();
      if (editedDeadline) {
        // Need to send valid datetime
        formData.append("deadline", new Date(editedDeadline).toISOString());
      }

      await api.post(`/documents/${pendingDoc.document_id}/confirm`, formData);
      showConfirmModal = false;
      clearPendingDocument();
      await fetchDocuments();
      showSuccessState();
    } catch (e) {
      alert("Confirmation failed: " + (e.response?.data?.detail || e.message));
    } finally {
      isConfirming = false;
    }
  }
</script>

<div class="mb-6">
  <h3 class="text-lg font-medium text-gray-900 mb-2">Upload Contract</h3>
  <div class="flex items-center space-x-2">
    <input type="file" accept=".pdf" bind:files class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"/>
    <button on:click={uploadDocument} disabled={isUploading || !files} class="px-4 py-2 bg-blue-600 text-white rounded-md disabled:bg-gray-400">
      {isUploading ? "Uploading..." : "Upload"}
    </button>
  </div>
</div>

<div class="mt-4">
  <h3 class="text-lg font-medium text-gray-900 mb-2">My Documents</h3>
  <div class="space-y-2">
    <button
      type="button"
      class="w-full p-3 rounded-md border border-gray-200 bg-white hover:bg-gray-50 flex justify-between text-left"
      on:click={() => dispatch("documentSelected", null)}
    >
      <span class="font-medium text-blue-600">Global Context (All Docs)</span>
    </button>
    {#each documents as doc}
      <button
        type="button"
        class="w-full p-3 rounded-md border border-gray-200 bg-white hover:bg-gray-50 flex flex-col text-left"
        on:click={() => dispatch("documentSelected", doc.id)}
      >
        <span class="font-medium text-gray-800">{doc.title}</span>
        <span class="text-xs text-gray-500">Status: {doc.status}</span>
        {#if doc.extracted_deadline}
          <span class="text-xs text-red-500">Deadline: {new Date(doc.extracted_deadline).toLocaleDateString()}</span>
        {/if}
      </button>
    {/each}
  </div>
</div>

{#if showConfirmModal}
<div class="fixed inset-0 z-[100] bg-slate-900/45 backdrop-blur-sm flex items-center justify-center p-4">
  <div class="bg-white rounded-lg p-6 max-w-md w-full shadow-2xl border border-slate-200">
    <h3 class="text-lg font-medium text-gray-900 mb-4">Confirm Document Details</h3>
    <p class="text-sm text-gray-500 mb-4">{pendingDoc.message}</p>

    <div class="mb-4">
      <label for="extracted-deadline" class="block text-sm font-medium text-gray-700">Extracted Deadline</label>
      <input id="extracted-deadline" type="date" bind:value={editedDeadline} class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm p-2 border" />
    </div>

    <div class="mt-5 sm:mt-6 flex space-x-3">
      <button on:click={confirmDocument} disabled={isConfirming} class="flex-1 justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:text-sm disabled:bg-blue-300 disabled:cursor-not-allowed">
        {isConfirming ? "Saving..." : "Confirm & Save"}
      </button>
      <button on:click={closeConfirmModal} disabled={isConfirming} class="flex-1 justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed">
        Cancel
      </button>
    </div>
  </div>
</div>
{/if}

{#if showSuccessModal}
<div class="fixed inset-0 z-[110] bg-slate-900/25 flex items-center justify-center p-4 pointer-events-none">
  <div class="max-w-sm w-full rounded-xl bg-white shadow-2xl border border-emerald-100 px-5 py-4">
    <p class="text-sm font-semibold text-emerald-700">Upload complete</p>
    <p class="mt-1 text-sm text-slate-600">The document was confirmed successfully. Returning to the usual workspace.</p>
  </div>
</div>
{/if}
