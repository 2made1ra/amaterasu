<script>
  import { createEventDispatcher, onMount } from "svelte";
  import api from "../lib/api";

  const dispatch = createEventDispatcher();

  let files = null;
  let isUploading = false;
  let documents = [];

  // HitL Modal State
  let showConfirmModal = false;
  let pendingDoc = null;
  let editedDeadline = "";

  onMount(async () => {
    fetchDocuments();
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
        editedDeadline = new Date(pendingDoc.extracted_deadline).toISOString().split('T')[0];
      }
      showConfirmModal = true;
    } catch (e) {
      alert("Upload failed: " + (e.response?.data?.detail || e.message));
    } finally {
      isUploading = false;
      files = null;
    }
  }

  async function confirmDocument() {
    try {
      const formData = new FormData();
      if (editedDeadline) {
        // Need to send valid datetime
        formData.append("deadline", new Date(editedDeadline).toISOString());
      }

      await api.post(`/documents/${pendingDoc.document_id}/confirm`, formData);
      showConfirmModal = false;
      pendingDoc = null;
      await fetchDocuments();
    } catch (e) {
      alert("Confirmation failed: " + (e.response?.data?.detail || e.message));
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
  <div class="space-y-2 cursor-pointer">
    <div
      class="p-3 rounded-md border border-gray-200 bg-white hover:bg-gray-50 flex justify-between"
      on:click={() => dispatch("documentSelected", null)}
    >
      <span class="font-medium text-blue-600">Global Context (All Docs)</span>
    </div>
    {#each documents as doc}
      <div
        class="p-3 rounded-md border border-gray-200 bg-white hover:bg-gray-50 flex flex-col"
        on:click={() => dispatch("documentSelected", doc.id)}
      >
        <span class="font-medium text-gray-800">{doc.title}</span>
        <span class="text-xs text-gray-500">Status: {doc.status}</span>
        {#if doc.extracted_deadline}
          <span class="text-xs text-red-500">Deadline: {new Date(doc.extracted_deadline).toLocaleDateString()}</span>
        {/if}
      </div>
    {/each}
  </div>
</div>

{#if showConfirmModal}
<div class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4">
  <div class="bg-white rounded-lg p-6 max-w-md w-full shadow-xl">
    <h3 class="text-lg font-medium text-gray-900 mb-4">Confirm Document Details</h3>
    <p class="text-sm text-gray-500 mb-4">{pendingDoc.message}</p>

    <div class="mb-4">
      <label class="block text-sm font-medium text-gray-700">Extracted Deadline</label>
      <input type="date" bind:value={editedDeadline} class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm p-2 border" />
    </div>

    <div class="mt-5 sm:mt-6 flex space-x-3">
      <button on:click={confirmDocument} class="flex-1 justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:text-sm">
        Confirm & Save
      </button>
      <button on:click={() => {showConfirmModal = false; pendingDoc = null;}} class="flex-1 justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:text-sm">
        Cancel
      </button>
    </div>
  </div>
</div>
{/if}
