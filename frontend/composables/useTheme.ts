/**
 * Active site theme — singleton state shared across the app.
 *
 * The plugin (`plugins/01.theme.client.ts`) fetches the value from
 * `/settings` once on app start and applies it. The admin theme picker
 * calls `setTheme(name)` to change it, which:
 *   - PATCHes /admin/settings on the backend
 *   - re-applies the CSS variables locally
 *   - mirrors to localStorage so a refresh doesn't flash the old palette
 */
import { applyTheme, DEFAULT_THEME, THEMES } from "~/utils/themes";

const STORAGE_KEY = "monografiya:theme";

export function useTheme() {
  const state = useState<string>("site:theme", () => DEFAULT_THEME);
  const api = useApi();

  function setLocal(name: string) {
    if (!THEMES[name]) return;
    state.value = name;
    applyTheme(name);
    if (import.meta.client) {
      try {
        localStorage.setItem(STORAGE_KEY, name);
      }
      catch {
        // localStorage blocked — no-op
      }
    }
  }

  async function setTheme(name: string): Promise<void> {
    setLocal(name);
    await api("/admin/settings", { method: "PATCH", body: { theme_name: name } });
  }

  async function loadFromServer(): Promise<void> {
    try {
      const data = await api<{ theme_name: string }>("/settings");
      if (data?.theme_name && THEMES[data.theme_name]) {
        setLocal(data.theme_name);
      }
    }
    catch {
      // Fall back to whatever localStorage / default already gave us.
    }
  }

  function loadFromCache(): void {
    if (!import.meta.client) return;
    try {
      const cached = localStorage.getItem(STORAGE_KEY);
      if (cached && THEMES[cached]) {
        setLocal(cached);
      }
    }
    catch {
      // ignore
    }
  }

  return {
    current: computed(() => state.value),
    setTheme,
    setLocal,
    loadFromServer,
    loadFromCache,
  };
}
