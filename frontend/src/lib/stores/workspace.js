import { writable } from "svelte/store";

export function createEmptySnapshot() {
  return {
    result_tree: [],
    selected_node_id: null,
    expanded_node_ids: [],
    view_mode: "flat"
  };
}

export const sessions = writable([]);
export const activeSessionId = writable(null);
export const activeSessionTitle = writable("New workspace");
export const activeSessionMessages = writable([]);
export const workspaceSnapshot = writable(createEmptySnapshot());

export function resetWorkspaceState() {
  sessions.set([]);
  activeSessionId.set(null);
  activeSessionTitle.set("New workspace");
  activeSessionMessages.set([]);
  workspaceSnapshot.set(createEmptySnapshot());
}
