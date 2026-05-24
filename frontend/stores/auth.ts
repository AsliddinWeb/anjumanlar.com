import { defineStore } from "pinia";
import type { LoginResponse, UserPublic, UserRole } from "~/types/api";

/**
 * Auth store — owns the access token (in memory) and the current user.
 *
 * The refresh token lives in an httpOnly cookie that the backend sets on
 * /auth/login + /auth/refresh; we never touch it from JS. On app boot we
 * call ``bootstrap()`` which tries one refresh — if the cookie is valid we
 * end up authenticated without the user having to re-enter credentials.
 *
 * The httpOnly refresh cookie is invisible to JS, so we mirror its
 * presence via a non-sensitive flag in localStorage and only attempt
 * /auth/refresh when the flag is set — otherwise every visitor would
 * hit a 401 on first paint and the browser would log a red error.
 */

const SESSION_FLAG_KEY = "monografiya:auth:session";

function setSessionFlag() {
  if (import.meta.client) {
    try { window.localStorage.setItem(SESSION_FLAG_KEY, "1"); } catch { /* quota */ }
  }
}
function clearSessionFlag() {
  if (import.meta.client) {
    try { window.localStorage.removeItem(SESSION_FLAG_KEY); } catch { /* quota */ }
  }
}
function hasSessionFlag(): boolean {
  if (!import.meta.client) return false;
  try { return window.localStorage.getItem(SESSION_FLAG_KEY) === "1"; }
  catch { return false; }
}

export const useAuthStore = defineStore("auth", () => {
  const user = ref<UserPublic | null>(null);
  const accessToken = ref<string | null>(null);

  const isAuthenticated = computed(
    () => !!accessToken.value && !!user.value,
  );
  const isVerified = computed(() => !!user.value?.email_verified);

  function hasRole(role: UserRole): boolean {
    if (!user.value) return false;
    // admin inherits author rights; superadmin inherits both — match the
    // backend's require_admin / require_author aliases.
    const hierarchy: Record<UserRole, UserRole[]> = {
      reader: ["reader"],
      author: ["reader", "author"],
      admin: ["reader", "author", "admin"],
      superadmin: ["reader", "author", "admin", "superadmin"],
    };
    return hierarchy[user.value.role].includes(role);
  }

  function _setSession(payload: LoginResponse) {
    accessToken.value = payload.access_token;
    user.value = payload.user;
    setSessionFlag();
  }

  function clear() {
    accessToken.value = null;
    user.value = null;
    clearSessionFlag();
  }

  async function login(email: string, password: string) {
    const api = useApi();
    const body = await api<LoginResponse>("/auth/login", {
      method: "POST",
      body: { email, password },
    });
    _setSession(body);
  }

  async function register(payload: {
    email: string;
    password: string;
    full_name: string;
    preferred_locale?: string;
  }) {
    const api = useApi();
    return api<UserPublic>("/auth/register", {
      method: "POST",
      body: payload,
    });
  }

  async function logout() {
    const api = useApi();
    try {
      await api("/auth/logout", { method: "POST" });
    } finally {
      clear();
    }
  }

  async function logoutAll() {
    const api = useApi();
    try {
      await api("/auth/logout-all", { method: "POST" });
    } finally {
      clear();
    }
  }

  async function refresh(): Promise<boolean> {
    const api = useApi();
    try {
      const body = await api<{ access_token: string; expires_in: number }>(
        "/auth/refresh",
        { method: "POST" },
      );
      accessToken.value = body.access_token;
      setSessionFlag();
      return true;
    } catch {
      clear();
      return false;
    }
  }

  async function fetchMe() {
    const api = useApi();
    user.value = await api<UserPublic>("/auth/me");
  }

  /** Run once on app boot: try a silent refresh, then load /me. Skipped
   *  entirely when the session flag is absent — saves an inevitable 401
   *  for every anonymous visitor. */
  async function bootstrap() {
    if (!hasSessionFlag()) return;
    const refreshed = await refresh();
    if (refreshed) {
      try {
        await fetchMe();
      } catch {
        clear();
      }
    }
  }

  return {
    user,
    accessToken,
    isAuthenticated,
    isVerified,
    hasRole,
    login,
    register,
    logout,
    logoutAll,
    refresh,
    fetchMe,
    bootstrap,
    clear,
  };
});
