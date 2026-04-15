import { writable } from "svelte/store";

const getPathname = () => {
  if (typeof window === "undefined") return "/";
  return window.location.pathname || "/";
};

export const currentPath = writable(getPathname());

if (typeof window !== "undefined") {
  window.addEventListener("popstate", () => {
    currentPath.set(getPathname());
  });
}

export function navigate(path, { replace = false } = {}) {
  if (typeof window === "undefined") return;

  if (replace) window.history.replaceState({}, "", path);
  else window.history.pushState({}, "", path);

  currentPath.set(getPathname());
}
