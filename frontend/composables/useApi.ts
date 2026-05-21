/**
 * Thin wrapper around Nuxt's $fetch that points at the backend API.
 *
 * Adds three pieces of glue:
 * - swaps the base URL between the in-Docker hostname (server-side SSR)
 *   and the host-mapped port (browser) — the frontend container can't
 *   reach ``localhost:8307``, so SSR must call ``backend:8000`` instead;
 * - sends ``credentials: "include"`` so the httpOnly refresh cookie
 *   travels on every browser request automatically;
 * - attaches the in-memory access token from the auth store as a Bearer
 *   header when one is present.
 *
 * Automatic 401 → refresh → retry is intentionally deferred to Phase 6 —
 * each composable handles 401 explicitly for now so failure modes stay
 * obvious during the early phases.
 */
export function useApi() {
  const config = useRuntimeConfig();
  const baseURL = import.meta.server
    ? (config.apiBaseInternal as string) || config.public.apiBase
    : config.public.apiBase;
  const auth = useAuthStore();

  return $fetch.create({
    baseURL,
    credentials: "include",
    onRequest({ options }) {
      const headers = new Headers(options.headers);
      if (auth.accessToken) {
        headers.set("Authorization", `Bearer ${auth.accessToken}`);
      }
      options.headers = headers;
    },
  });
}
