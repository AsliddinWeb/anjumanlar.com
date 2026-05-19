/**
 * Thin wrapper around Nuxt's $fetch that points at the backend API.
 *
 * Adds two pieces of glue:
 * - sends ``credentials: "include"`` so the httpOnly refresh cookie travels
 *   on every request automatically;
 * - attaches the in-memory access token from the auth store as a Bearer
 *   header when one is present.
 *
 * Automatic 401 → refresh → retry is intentionally deferred to Phase 6 —
 * each composable handles 401 explicitly for now so failure modes stay
 * obvious during Phase 1 dev.
 */
import type { $Fetch } from "ofetch";

export function useApi(): $Fetch {
  const { apiBase } = useRuntimeConfig().public;
  const auth = useAuthStore();

  return $fetch.create({
    baseURL: apiBase,
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
