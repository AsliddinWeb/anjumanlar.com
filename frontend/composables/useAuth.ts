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

/** Extract a human-readable error message from an ofetch/API failure. */
export function apiErrorMessage(err: unknown, fallback = "common.error"): string {
  if (typeof err === "object" && err !== null) {
    const data = (err as { data?: { error?: { message?: string } } }).data;
    if (data?.error?.message) return data.error.message;
  }
  return fallback;
}
