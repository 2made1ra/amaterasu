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
      dispatch("documentsChanged", { count: documents.length, documents });
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

<div class="grid gap-4 lg:grid-cols-[minmax(0,1.1fr)_minmax(280px,0.9fr)]">
  <section class="rounded-[24px] border border-slate-200 bg-slate-50/80 p-4">
    <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">Import</p>
    <h3 class="mt-1 text-lg font-semibold text-slate-900">Upload a contract PDF</h3>
    <p class="mt-2 text-sm text-slate-500">
      Contracts added here become available to future workspace searches after confirmation.
    </p>

    <div class="mt-4 flex flex-col gap-3">
      <input
        type="file"
        accept=".pdf"
        bind:files
        class="block w-full rounded-2xl border border-slate-200 bg-white p-3 text-sm text-slate-500 file:mr-4 file:rounded-full file:border-0 file:bg-sky-50 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-sky-700 hover:file:bg-sky-100"
      />
      <button
        on:click={uploadDocument}
        disabled={isUploading || !files}
        class="w-fit rounded-full bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
      >
        {isUploading ? "Uploading..." : "Upload contract"}
      </button>
    </div>
  </section>

  <section class="rounded-[24px] border border-slate-200 bg-white p-4">
    <div class="flex items-center justify-between gap-3">
      <div>
        <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">Library</p>
        <h3 class="mt-1 text-lg font-semibold text-slate-900">Available contracts</h3>
      </div>
      <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">{documents.length}</span>
    </div>

    <div class="mt-4 max-h-64 space-y-2 overflow-y-auto pr-1">
      {#if documents.length === 0}
        <div class="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-6 text-center text-sm text-slate-500">
          No contracts uploaded yet.
        </div>
      {:else}
        {#each documents as doc}
          <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
            <div class="flex items-start justify-between gap-3">
              <div>
                <p class="text-sm font-medium text-slate-800">{doc.title}</p>
                <p class="mt-1 text-xs text-slate-500">Status: {doc.status}</p>
              </div>
              <span class={`rounded-full px-2 py-1 text-[11px] font-medium ${doc.status === "CONFIRMED" ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>
                {doc.status}
              </span>
            </div>
            {#if doc.extracted_deadline}
              <p class="mt-2 text-xs text-rose-600">
                Deadline: {new Date(doc.extracted_deadline).toLocaleDateString()}
              </p>
            {/if}
          </div>
        {/each}
      {/if}
    </div>
  </section>
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
