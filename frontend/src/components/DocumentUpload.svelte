<script>
  import { createEventDispatcher, onDestroy, onMount } from "svelte";
  import api from "../lib/api";

  const dispatch = createEventDispatcher();
  const REQUIRED_FACT_FIELDS = [
    { key: "company_name", label: "Company Name", type: "text", autocomplete: "organization" },
    { key: "signatory_name", label: "Signatory Name", type: "text", autocomplete: "name" },
    { key: "contact_phone", label: "Contact Phone", type: "text", autocomplete: "tel" },
    { key: "service_price", label: "Service Price", type: "text", autocomplete: "off" },
    { key: "service_subject", label: "Service Subject", type: "text", autocomplete: "off" },
    { key: "service_completion_date", label: "Service Completion Date", type: "date", autocomplete: "off" },
  ];

  let files = null;
  let isUploading = false;
  let documents = [];

  // HitL Modal State
  let showConfirmModal = false;
  let showSuccessModal = false;
  let pendingDoc = null;
  let editableFacts = {};
  let confirmErrors = {};
  let confirmStep = "processing";
  let confirmStatusMessage = "";
  let isConfirming = false;
  let successTimer = null;
  let pollingToken = 0;

  onMount(async () => {
    fetchDocuments();
  });

  onDestroy(() => {
    pollingToken += 1;
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
      await fetchDocuments();
      openConfirmationModal(res.data);
      await pollDocumentUntilReady(res.data.document_id);
    } catch (e) {
      alert("Upload failed: " + (e.response?.data?.detail || e.message));
    } finally {
      isUploading = false;
      files = null;
    }
  }

  function normalizeDateValue(value) {
    if (!value || typeof value !== "string") return "";

    const trimmed = value.trim();
    if (!trimmed) return "";
    if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) return trimmed;

    const dottedMatch = trimmed.match(/^(\d{1,2})\.(\d{1,2})\.(\d{4})$/);
    if (dottedMatch) {
      const [, day, month, year] = dottedMatch;
      return `${year}-${month.padStart(2, "0")}-${day.padStart(2, "0")}`;
    }

    const parsed = new Date(trimmed);
    if (Number.isNaN(parsed.getTime())) return "";
    return parsed.toISOString().split("T")[0];
  }

  function createEditableFacts(facts = {}) {
    const nextFacts = { ...facts };

    for (const field of REQUIRED_FACT_FIELDS) {
      const rawValue = facts[field.key];
      if (field.type === "date") {
        nextFacts[field.key] = normalizeDateValue(rawValue);
      } else {
        nextFacts[field.key] = typeof rawValue === "string" ? rawValue : "";
      }
    }

    nextFacts.missing_required_fields = Array.isArray(facts.missing_required_fields)
      ? facts.missing_required_fields
      : [];

    return nextFacts;
  }

  function openConfirmationModal(uploadResponse) {
    pendingDoc = uploadResponse;
    editableFacts = {};
    confirmErrors = {};
    confirmStep = "processing";
    confirmStatusMessage = "Extracting contract facts. This usually takes a few seconds.";
    showConfirmModal = true;
  }

  function clearPendingDocument() {
    pollingToken += 1;
    pendingDoc = null;
    editableFacts = {};
    confirmErrors = {};
    confirmStep = "processing";
    confirmStatusMessage = "";
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

  function setEditableFact(key, value) {
    editableFacts = {
      ...editableFacts,
      [key]: value,
    };

    if (confirmErrors[key]) {
      const nextErrors = { ...confirmErrors };
      delete nextErrors[key];
      confirmErrors = nextErrors;
    }
  }

  function validateEditableFacts() {
    const nextErrors = {};
    const missingFields = [];

    for (const field of REQUIRED_FACT_FIELDS) {
      const rawValue = editableFacts[field.key];
      const value = typeof rawValue === "string" ? rawValue.trim() : rawValue;
      if (!value) {
        nextErrors[field.key] = `${field.label} is required`;
        missingFields.push(field.key);
      }
    }

    editableFacts = {
      ...editableFacts,
      missing_required_fields: missingFields,
    };
    confirmErrors = nextErrors;
    return Object.keys(nextErrors).length === 0;
  }

  async function pollDocumentUntilReady(documentId) {
    const currentToken = ++pollingToken;

    for (let attempt = 0; attempt < 30; attempt += 1) {
      if (currentToken !== pollingToken || !showConfirmModal || pendingDoc?.document_id !== documentId) {
        return;
      }

      try {
        const res = await api.get(`/documents/${documentId}`);
        const documentDetail = res.data;
        pendingDoc = { ...pendingDoc, ...documentDetail };

        if (documentDetail.processing_status === "FAILED") {
          confirmStep = "error";
          confirmStatusMessage = documentDetail.last_error
            ? `Document processing failed: ${documentDetail.last_error}`
            : "Document processing failed before facts became available.";
          return;
        }

        if (
          documentDetail.processing_status === "FACTS_READY" &&
          documentDetail.review_status === "PENDING_REVIEW" &&
          documentDetail.facts?.facts
        ) {
          editableFacts = createEditableFacts(documentDetail.facts.facts);
          confirmErrors = {};
          confirmStep = "ready";
          confirmStatusMessage = "Review the extracted fields and fill in any missing required values before saving.";
          return;
        }

        if (documentDetail.review_status === "APPROVED") {
          showConfirmModal = false;
          clearPendingDocument();
          await fetchDocuments();
          showSuccessState();
          return;
        }
      } catch (e) {
        console.error(e);
      }

      await new Promise((resolve) => setTimeout(resolve, 1500));
    }

    if (currentToken !== pollingToken) return;

    confirmStep = "error";
    confirmStatusMessage = "The document is still processing. Close this dialog and try confirming again in a few seconds.";
  }

  async function confirmDocument() {
    if (!pendingDoc || isConfirming || confirmStep !== "ready") return;
    if (!validateEditableFacts()) return;

    isConfirming = true;

    try {
      const factsPayload = {
        ...editableFacts,
        missing_required_fields: [],
      };

      await api.post(`/documents/${pendingDoc.document_id}/confirm`, {
        facts: factsPayload,
      });
      showConfirmModal = false;
      clearPendingDocument();
      await fetchDocuments();
      showSuccessState();
    } catch (e) {
      if (e.response?.status === 409) {
        confirmStep = "processing";
        confirmStatusMessage = "The backend is still finalizing extracted facts. Waiting for the review form again.";
        await pollDocumentUntilReady(pendingDoc.document_id);
        return;
      }
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
    <h3 class="text-lg font-medium text-gray-900 mb-2">
      {#if confirmStep === "ready"}
        Confirm Document Details
      {:else if confirmStep === "error"}
        Processing Error
      {:else}
        Preparing Document Review
      {/if}
    </h3>

    {#if pendingDoc?.title}
      <p class="text-sm font-medium text-slate-700 mb-1">{pendingDoc.title}</p>
    {/if}
    <p class="text-sm text-gray-500 mb-4">{confirmStatusMessage || pendingDoc?.message}</p>

    {#if confirmStep === "processing"}
      <div class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-4">
        <div class="flex items-center gap-3 text-sm text-slate-600">
          <div class="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-slate-700"></div>
          <span>Waiting for extracted facts from the backend</span>
        </div>
      </div>
    {:else if confirmStep === "error"}
      <div class="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
        {confirmStatusMessage}
      </div>
    {:else}
      {#if editableFacts.missing_required_fields?.length}
        <div class="mb-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          Required fields still need review: {editableFacts.missing_required_fields.join(", ")}.
        </div>
      {/if}

      <div class="space-y-4">
        {#each REQUIRED_FACT_FIELDS as field}
          <div>
            <label for={field.key} class="block text-sm font-medium text-gray-700">
              {field.label}
            </label>
            <input
              id={field.key}
              type={field.type}
              value={editableFacts[field.key] ?? ""}
              autocomplete={field.autocomplete}
              on:input={(event) => setEditableFact(field.key, event.currentTarget.value)}
              class={`mt-1 block w-full rounded-md border p-2 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm ${
                confirmErrors[field.key] ? "border-rose-400 bg-rose-50" : "border-gray-300"
              }`}
            />
            {#if confirmErrors[field.key]}
              <p class="mt-1 text-xs text-rose-600">{confirmErrors[field.key]}</p>
            {/if}
          </div>
        {/each}
      </div>
    {/if}

    <div class="mt-5 sm:mt-6 flex space-x-3">
      {#if confirmStep === "ready"}
        <button on:click={confirmDocument} disabled={isConfirming} class="flex-1 justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:text-sm disabled:bg-blue-300 disabled:cursor-not-allowed">
          {isConfirming ? "Saving..." : "Confirm & Save"}
        </button>
      {/if}
      <button on:click={closeConfirmModal} disabled={isConfirming} class="flex-1 justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed">
        {confirmStep === "ready" ? "Cancel" : "Close"}
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
