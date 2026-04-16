<script>
  import { get } from "svelte/store";
  import { onMount } from "svelte";

  import AgentChatPanel from "../components/AgentChatPanel.svelte";
  import ChatSessionSidebar from "../components/ChatSessionSidebar.svelte";
  import ContractViewerModal from "../components/ContractViewerModal.svelte";
  import ResultExplorerPanel from "../components/ResultExplorerPanel.svelte";
  import WorkspaceToolbar from "../components/WorkspaceToolbar.svelte";
  import api from "../lib/api";
  import { navigate } from "../lib/router";
  import {
    activeSessionId,
    activeSessionMessages,
    activeSessionTitle,
    createEmptySnapshot,
    resetWorkspaceState,
    sessions,
    workspaceSnapshot
  } from "../lib/stores/workspace";

  let user = null;
  let isBootstrapping = true;
  let isSessionListLoading = false;
  let isSessionLoading = false;
  let isSending = false;
  let sessionError = "";
  let agentError = "";
  let explorerError = "";
  let documentsCount = 0;
  let activeContract = null;

  onMount(async () => {
    try {
      const res = await api.get("/auth/me");
      user = res.data;
      await refreshSessions();
    } catch (err) {
      localStorage.removeItem("token");
      navigate("/", { replace: true });
    } finally {
      isBootstrapping = false;
    }
  });

  function applySessionDetail(detail) {
    activeSessionId.set(detail.id);
    activeSessionTitle.set(detail.title);
    activeSessionMessages.set(detail.messages || []);
    workspaceSnapshot.set(detail.snapshot || createEmptySnapshot());
    agentError = "";
    explorerError = "";
  }

  function upsertSessionSummary(detail, fallbackCount = 0) {
    sessions.update((items) => {
      const summary = {
        id: detail.id,
        title: detail.title,
        created_at: detail.created_at,
        updated_at: detail.updated_at,
        last_message_at: detail.last_message_at,
        message_count: detail.messages?.length ?? fallbackCount
      };

      const next = [...items];
      const index = next.findIndex((item) => item.id === detail.id);
      if (index >= 0) {
        next[index] = { ...next[index], ...summary };
      } else {
        next.unshift(summary);
      }
      return next.sort((left, right) => new Date(right.last_message_at) - new Date(left.last_message_at));
    });
  }

  async function refreshSessions() {
    isSessionListLoading = true;
    sessionError = "";

    try {
      const res = await api.get("/chat-sessions/");
      sessions.set(res.data);

      const currentId = get(activeSessionId);
      if (!currentId && res.data.length > 0) {
        await loadSession(res.data[0].id);
      }
    } catch (err) {
      sessionError = err.response?.data?.detail || "Could not load chat sessions.";
    } finally {
      isSessionListLoading = false;
    }
  }

  async function loadSession(sessionId) {
    if (!sessionId) return;

    isSessionLoading = true;
    sessionError = "";

    try {
      const res = await api.get(`/chat-sessions/${sessionId}`);
      applySessionDetail(res.data);
      upsertSessionSummary(res.data);
    } catch (err) {
      sessionError = err.response?.data?.detail || "Could not load the selected session.";
    } finally {
      isSessionLoading = false;
    }
  }

  async function createSession({ activate = true } = {}) {
    const res = await api.post("/chat-sessions/", { title: null });
    upsertSessionSummary(res.data);

    if (activate) {
      applySessionDetail(res.data);
    }

    return res.data;
  }

  async function ensureActiveSession() {
    const currentId = get(activeSessionId);
    if (currentId) {
      return currentId;
    }

    const created = await createSession({ activate: true });
    return created.id;
  }

  async function handleCreateSession() {
    sessionError = "";

    try {
      await createSession({ activate: true });
    } catch (err) {
      sessionError = err.response?.data?.detail || "Could not create a new session.";
    }
  }

  async function handleSendMessage(event) {
    const query = event.detail.query?.trim();
    if (!query || isSending) return;

    isSending = true;
    agentError = "";

    try {
      const sessionId = await ensureActiveSession();
      const optimisticUserMessage = {
        id: `local-user-${Date.now()}`,
        role: "user",
        content: query,
        created_at: new Date().toISOString()
      };

      activeSessionMessages.update((items) => [...items, optimisticUserMessage]);

      const res = await api.post(`/chat-sessions/${sessionId}/messages`, { query });
      activeSessionMessages.update((items) => [...items, res.data.assistant_message]);
      activeSessionTitle.set(res.data.session_title);
      workspaceSnapshot.set(res.data.snapshot || createEmptySnapshot());

      sessions.update((items) =>
        items
          .map((item) =>
            item.id === sessionId
              ? {
                  ...item,
                  title: res.data.session_title,
                  last_message_at: res.data.assistant_message.created_at,
                  updated_at: res.data.assistant_message.created_at,
                  message_count: (item.message_count || 0) + 2
                }
              : item
          )
          .sort((left, right) => new Date(right.last_message_at) - new Date(left.last_message_at))
      );
    } catch (err) {
      activeSessionMessages.update((items) => items.slice(0, -1));
      agentError = err.response?.data?.detail || "The agent could not answer right now.";
    } finally {
      isSending = false;
    }
  }

  async function persistSnapshot(nextSnapshot) {
    const currentId = get(activeSessionId);
    if (!currentId) return;

    workspaceSnapshot.set(nextSnapshot);

    try {
      await api.patch(`/chat-sessions/${currentId}/snapshot`, nextSnapshot);
      explorerError = "";
    } catch (err) {
      explorerError = err.response?.data?.detail || "Could not save the results pane state.";
    }
  }

  async function handleSelectNode(event) {
    const nodeId = event.detail.node?.id || null;
    const nextSnapshot = {
      ...get(workspaceSnapshot),
      selected_node_id: nodeId
    };
    await persistSnapshot(nextSnapshot);
  }

  async function handleToggleNode(event) {
    const nodeId = event.detail.nodeId;
    const snapshot = get(workspaceSnapshot);
    const expanded = snapshot.expanded_node_ids || [];
    const nextExpanded = expanded.includes(nodeId)
      ? expanded.filter((id) => id !== nodeId)
      : [...expanded, nodeId];

    await persistSnapshot({
      ...snapshot,
      expanded_node_ids: nextExpanded
    });
  }

  function handleOpenContract(event) {
    activeContract = event.detail.node;
  }

  function handleCloseContractModal() {
    activeContract = null;
  }

  function handleDocumentsChanged(event) {
    documentsCount = event.detail.count || 0;
  }

  async function handleLogout() {
    localStorage.removeItem("token");
    resetWorkspaceState();
    navigate("/", { replace: true });
  }
</script>

{#if isBootstrapping}
  <div class="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.14),_transparent_45%),linear-gradient(180deg,#f8fbff_0%,#eef4ff_100%)] px-6 py-10">
    <div class="mx-auto flex max-w-7xl items-center justify-center rounded-[32px] border border-white/70 bg-white/70 px-8 py-24 shadow-[0_25px_80px_rgba(15,23,42,0.08)] backdrop-blur">
      <p class="text-sm font-medium text-slate-500">Loading workspace...</p>
    </div>
  </div>
{:else if user}
  <div class="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.14),_transparent_45%),linear-gradient(180deg,#f8fbff_0%,#eef4ff_100%)] p-4 text-slate-900 md:p-6">
    <div class="mx-auto flex min-h-[calc(100vh-2rem)] max-w-7xl flex-col gap-4 rounded-[32px] border border-white/70 bg-white/70 p-4 shadow-[0_25px_80px_rgba(15,23,42,0.08)] backdrop-blur md:min-h-[calc(100vh-3rem)] md:p-5">
      <WorkspaceToolbar
        username={user.username}
        documentsCount={documentsCount}
        activeSessionTitle={$activeSessionTitle}
        on:logout={handleLogout}
        on:createSession={handleCreateSession}
        on:documentsChanged={handleDocumentsChanged}
      />

      <div class="grid min-h-0 flex-1 gap-4 xl:grid-cols-[280px_minmax(0,1fr)_minmax(360px,460px)]">
        <div class="min-h-[260px] xl:min-h-0">
          <ChatSessionSidebar
            sessions={$sessions}
            activeSessionId={$activeSessionId}
            isLoading={isSessionListLoading}
            errorMessage={sessionError}
            on:createSession={handleCreateSession}
            on:selectSession={(event) => loadSession(event.detail.sessionId)}
          />
        </div>

        <div class="min-h-[320px] xl:min-h-0">
          <ResultExplorerPanel
            snapshot={$workspaceSnapshot}
            isLoading={isSessionLoading}
            errorMessage={explorerError}
            on:selectNode={handleSelectNode}
            on:toggleNode={handleToggleNode}
            on:openContract={handleOpenContract}
          />
        </div>

        <div class="min-h-[420px] xl:min-h-0">
          <AgentChatPanel
            sessionTitle={$activeSessionTitle}
            messages={$activeSessionMessages}
            hasActiveSession={Boolean($activeSessionId)}
            isLoading={isSessionLoading}
            isSending={isSending}
            errorMessage={agentError}
            on:send={handleSendMessage}
          />
        </div>
      </div>
    </div>
  </div>

  <ContractViewerModal
    open={Boolean(activeContract)}
    node={activeContract}
    on:close={handleCloseContractModal}
  />
{/if}
