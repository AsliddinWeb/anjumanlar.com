/**
 * Site-wide presentation state — color theme + ornament motif, both
 * controlled from /admin/settings.
 *
 * On app boot the client plugin loads the cached values from
 * localStorage for an instant paint, then refreshes from /settings in
 * the background. Admins call `setTheme(name)` / `setOrnament(name)`
 * which PATCHes the backend and updates local state.
 */
import { applyTheme, DEFAULT_THEME, THEMES } from "~/utils/themes";
import { DEFAULT_ORNAMENT, ORNAMENTS } from "~/utils/ornaments";

const THEME_KEY = "monografiya:theme";
const ORNAMENT_KEY = "monografiya:ornament";

export function useTheme() {
  const themeState = useState<string>("site:theme", () => DEFAULT_THEME);
  const ornamentState = useState<string>("site:ornament", () => DEFAULT_ORNAMENT);
  const api = useApi();

  function setLocalTheme(name: string) {
    if (!THEMES[name]) return;
    themeState.value = name;
    applyTheme(name);
    if (import.meta.client) {
      try { localStorage.setItem(THEME_KEY, name); }
      catch { /* ignore */ }
    }
  }

  function setLocalOrnament(name: string) {
    if (!ORNAMENTS[name]) return;
    ornamentState.value = name;
    if (import.meta.client) {
      try { localStorage.setItem(ORNAMENT_KEY, name); }
      catch { /* ignore */ }
    }
  }

  async function setTheme(name: string): Promise<void> {
    setLocalTheme(name);
    await api("/admin/settings", { method: "PATCH", body: { theme_name: name } });
  }

  async function setOrnament(name: string): Promise<void> {
    setLocalOrnament(name);
    await api("/admin/settings", { method: "PATCH", body: { ornament_name: name } });
  }

  async function loadFromServer(): Promise<void> {
    try {
      const data = await api<{ theme_name: string; ornament_name: string }>("/settings");
      if (data?.theme_name && THEMES[data.theme_name]) setLocalTheme(data.theme_name);
      if (data?.ornament_name && ORNAMENTS[data.ornament_name]) setLocalOrnament(data.ornament_name);
    }
    catch { /* keep cached / defaults */ }
  }

  function loadFromCache(): void {
    if (!import.meta.client) return;
    try {
      const t = localStorage.getItem(THEME_KEY);
      if (t && THEMES[t]) setLocalTheme(t);
      const o = localStorage.getItem(ORNAMENT_KEY);
      if (o && ORNAMENTS[o]) setLocalOrnament(o);
    }
    catch { /* ignore */ }
  }

  return {
    current: computed(() => themeState.value),
    currentOrnament: computed(() => ornamentState.value),
    setTheme,
    setOrnament,
    setLocal: setLocalTheme,
    setLocalOrnament,
    loadFromServer,
    loadFromCache,
  };
}
