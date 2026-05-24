import { defineStore } from "pinia";
import type { LoginResponse, UserPublic, UserRole } from "~/types/api";

/**
 * Auth store — owns the access token and the current user.
 *
 * Tokens are mirrored to localStorage so the session survives a hard
 * browser refresh. The backend also sets an httpOnly refresh cookie on
 * /auth/login, but in cross-origin dev (frontend on :8308, API on :8307)
 * the cookie isn't reliably preserved across reloads — we therefore
 * keep both pieces and send the refresh_token in the request body if
 * the cookie ever fails to come back. Backend's /auth/refresh resolver
 * accepts either source.
 */

const ACCESS_KEY = "monografiya:auth:access";
const REFRESH_KEY = "monografiya:auth:refresh";

function readStore(key: string): string | null {
  if (!import.meta.client) return null;
  try { return window.localStorage.getItem(key); }
  catch { return null; }
}
function writeStore(key: string, value: string | null) {
  if (!import.meta.client) return;
  try {
    if (value === null) window.localStorage.removeItem(key);
    else window.localStorage.setItem(key, value);
  }
  catch { /* quota or private mode */ }
}

export const useAuthStore = defineStore("auth", () => {
  const user = ref<UserPublic | null>(null);
  const accessToken = ref<string | null>(null);
  const refreshToken = ref<string | null>(null);

  const isAuthenticated = computed(
    () => !!accessToken.value && !!user.value,
  );
  const isVerified = computed(() => !!user.value?.email_verified);

  function hasRole(role: UserRole): boolean {
    if (!user.value) return false;
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
    refreshToken.value = payload.refresh_token;
    user.value = payload.user;
    writeStore(ACCESS_KEY, payload.access_token);
    writeStore(REFRESH_KEY, payload.refresh_token);
  }

  function clear() {
    accessToken.value = null;
    refreshToken.value = null;
    user.value = null;
    writeStore(ACCESS_KEY, null);
    writeStore(REFRESH_KEY, null);
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
      await api("/auth/logout", {
        method: "POST",
        body: refreshToken.value ? { refresh_token: refreshToken.value } : {},
      });
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
      const stored = refreshToken.value ?? readStore(REFRESH_KEY);
      const body = await api<{ access_token: string; refresh_token: string; expires_in: number } | null>(
        "/auth/refresh",
        {
          method: "POST",
          // Send the stored refresh_token in the body so we don't depend
          // on the httpOnly cookie surviving cross-origin reloads.
          body: stored ? { refresh_token: stored } : undefined,
        },
      );
      if (!body || !body.access_token) {
        clear();
        return false;
      }
      accessToken.value = body.access_token;
      refreshToken.value = body.refresh_token;
      writeStore(ACCESS_KEY, body.access_token);
      writeStore(REFRESH_KEY, body.refresh_token);
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

  /** Run once on app boot: restore tokens from localStorage, validate with
   *  /me, fall back to /refresh if the access token has expired. */
  async function bootstrap() {
    if (!import.meta.client) return;
    const storedAccess = readStore(ACCESS_KEY);
    const storedRefresh = readStore(REFRESH_KEY);
    if (!storedAccess && !storedRefresh) return;

    accessToken.value = storedAccess;
    refreshToken.value = storedRefresh;

    if (storedAccess) {
      try {
        await fetchMe();
        return;
      } catch {
        // Access token expired or invalid — try a refresh below.
      }
    }
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
    refreshToken,
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
