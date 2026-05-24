/**
 * Page-level guard. Apply with::
 *
 *     definePageMeta({ middleware: "auth" })
 *
 * Redirects unauthenticated visitors to /auth/login, preserving the page
 * they wanted via the ``redirect`` query param so /login can bounce them
 * back after success.
 *
 * Runs **client-side only** — the bootstrap plugin that restores the
 * session from the refresh cookie is also client-only (httpOnly cookies
 * aren't visible during SSR), so a server-side check would always see
 * the visitor as logged-out and bounce them away. By the time this
 * middleware runs in the browser, the awaited bootstrap plugin has
 * either authenticated the user or confirmed they're anonymous.
 */
export default defineNuxtRouteMiddleware((to) => {
  if (import.meta.server) return;
  const auth = useAuthStore();
  if (!auth.isAuthenticated) {
    const localePath = useLocalePath();
    return navigateTo({
      path: localePath("/auth/login"),
      query: { redirect: to.fullPath },
    });
  }
});
