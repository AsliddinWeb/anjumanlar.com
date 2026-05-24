/**
 * Sugar over the Pinia auth store. Pages that just need user state can use
 * ``const { user, isAuthenticated, logout } = useAuth()`` without reaching
 * for the store directly.
 */
export function useAuth() {
  const store = useAuthStore();
  const { user, accessToken, isAuthenticated, isVerified } = storeToRefs(store);
  return {
    user,
    accessToken,
    isAuthenticated,
    isVerified,
    hasRole: store.hasRole,
    login: store.login,
    register: store.register,
    logout: store.logout,
    logoutAll: store.logoutAll,
    refresh: store.refresh,
    fetchMe: store.fetchMe,
    bootstrap: store.bootstrap,
  };
}

/**
 * Turn an ofetch/API failure into a localized message. Tries (in order):
 *
 *   1. ``data.error.details.code`` — backend's specific code (e.g.
 *      "invalid_credentials") mapped via the ``errors.<code>`` i18n
 *      namespace. This is the path that keeps user-visible errors in the
 *      site language regardless of backend locale.
 *   2. ``data.error.code`` — generic class code ("unauthorized", "not_found").
 *   3. The raw ``data.error.message`` — only as a last resort, since it's
 *      always English on this backend.
 *   4. The supplied ``fallback`` (already a translated string from the
 *      caller).
 */
export function apiErrorMessage(err: unknown, fallback: string): string {
  const i18n = useNuxtApp().$i18n;
  const t = i18n?.t?.bind(i18n);

  const data = (err as { data?: { error?: { code?: string; message?: string; details?: { code?: string } } } })?.data;
  const detailCode = data?.error?.details?.code;
  const classCode = data?.error?.code;

  function tryKey(key: string): string | null {
    if (!t) return null;
    const translated = t(key);
    return translated === key ? null : translated;
  }

  if (detailCode) {
    const hit = tryKey(`errors.${detailCode}`);
    if (hit) return hit;
  }
  if (classCode) {
    const hit = tryKey(`errors.${classCode}`);
    if (hit) return hit;
  }
  if (data?.error?.message) return data.error.message;
  return fallback;
}
