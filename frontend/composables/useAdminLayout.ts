const STORAGE_KEY = "admin:sidebar:collapsed";

export function useAdminLayout() {
  const collapsed = useState<boolean>("admin:sidebar:collapsed", () => false);
  const mobileDrawerOpen = useState<boolean>("admin:sidebar:drawer", () => false);

  if (import.meta.client) {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored !== null && collapsed.value !== (stored === "1")) {
      collapsed.value = stored === "1";
    }
  }

  function setCollapsed(v: boolean) {
    collapsed.value = v;
    if (import.meta.client) {
      window.localStorage.setItem(STORAGE_KEY, v ? "1" : "0");
    }
  }

  function toggleCollapsed() {
    setCollapsed(!collapsed.value);
  }

  return {
    collapsed: readonly(collapsed),
    mobileDrawerOpen,
    toggleCollapsed,
    setCollapsed,
  };
}
