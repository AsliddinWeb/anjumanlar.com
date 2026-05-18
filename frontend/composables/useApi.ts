/**
 * Thin wrapper around Nuxt's $fetch that points at the backend API.
 * Phase 1 will add the JWT interceptor + refresh handling.
 */
export function useApi() {
  const { apiBase } = useRuntimeConfig().public;

  return $fetch.create({
    baseURL: apiBase,
    onRequest({ options }) {
      // Placeholder for auth header — wired up in Phase 1.
      options.headers = options.headers || {};
    },
    onResponseError({ response }) {
      // eslint-disable-next-line no-console
      console.warn("[api] error", response.status, response._data);
    },
  });
}
