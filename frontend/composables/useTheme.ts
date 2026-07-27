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
const ANIMATIONS_KEY = "monografiya:animations";
const AUTHOR_UPLOADS_KEY = "monografiya:author-uploads";

export function useTheme() {
  const themeState = useState<string>("site:theme", () => DEFAULT_THEME);
  const ornamentState = useState<string>("site:ornament", () => DEFAULT_ORNAMENT);
  const animationsState = useState<boolean>("site:animations", () => true);
  // Defaults to true (unrestricted) so the UI doesn't flash a "paused"
  // state before the real value loads from /settings.
  const authorUploadsState = useState<boolean>("site:author-uploads", () => true);
  const api = useApi();

  function applyAnimationFlag(enabled: boolean) {
    if (typeof document === "undefined") return;
    document.documentElement.setAttribute("data-animations", enabled ? "on" : "off");
  }

  function setLocalAnimations(enabled: boolean) {
    animationsState.value = enabled;
    applyAnimationFlag(enabled);
    if (import.meta.client) {
      try { localStorage.setItem(ANIMATIONS_KEY, enabled ? "1" : "0"); }
      catch { /* ignore */ }
    }
  }

  function setLocalTheme(name: string) {
    if (!THEMES[name]) return;
    themeState.value = name;
    applyTheme(name);
    if (import.meta.client) {
      try { localStorage.setItem(THEME_KEY, name); }
      catch { /* ignore */ }
    }
  }

  function setLocalAuthorUploads(enabled: boolean) {
    authorUploadsState.value = enabled;
    if (import.meta.client) {
      try { localStorage.setItem(AUTHOR_UPLOADS_KEY, enabled ? "1" : "0"); }
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

  async function setAnimations(enabled: boolean): Promise<void> {
    setLocalAnimations(enabled);
    await api("/admin/settings", { method: "PATCH", body: { animations_enabled: enabled } });
  }

  async function setAuthorUploads(enabled: boolean): Promise<void> {
    setLocalAuthorUploads(enabled);
    await api("/admin/settings", { method: "PATCH", body: { author_uploads_enabled: enabled } });
  }

  async function loadFromServer(): Promise<void> {
    try {
      const data = await api<{
        theme_name: string;
        ornament_name: string;
        animations_enabled: boolean;
        author_uploads_enabled: boolean;
      }>("/settings");
      if (data?.theme_name && THEMES[data.theme_name]) setLocalTheme(data.theme_name);
      if (data?.ornament_name && ORNAMENTS[data.ornament_name]) setLocalOrnament(data.ornament_name);
      if (typeof data?.animations_enabled === "boolean") setLocalAnimations(data.animations_enabled);
      if (typeof data?.author_uploads_enabled === "boolean") setLocalAuthorUploads(data.author_uploads_enabled);
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
      const a = localStorage.getItem(ANIMATIONS_KEY);
      if (a !== null) setLocalAnimations(a === "1");
      const au = localStorage.getItem(AUTHOR_UPLOADS_KEY);
      if (au !== null) setLocalAuthorUploads(au === "1");
    }
    catch { /* ignore */ }
  }

  return {
    current: computed(() => themeState.value),
    currentOrnament: computed(() => ornamentState.value),
    animationsEnabled: computed(() => animationsState.value),
    authorUploadsEnabled: computed(() => authorUploadsState.value),
    setTheme,
    setOrnament,
    setAnimations,
    setAuthorUploads,
    setLocal: setLocalTheme,
    setLocalOrnament,
    setLocalAnimations,
    setLocalAuthorUploads,
    loadFromServer,
    loadFromCache,
  };
}
