/**
 * Admin-only guard. Apply alongside the ``auth`` middleware::
 *
 *     definePageMeta({ middleware: ["auth", "admin"] })
 *
 * The order matters — ``auth`` runs first so unauthenticated visitors get
 * the login redirect; logged-in but non-admin users hit ``admin`` and
 * land on the homepage (no leaked existence info, no 403 page to bypass).
 *
 * Client-only for the same reason as ``auth``: SSR has no httpOnly cookie
 * visibility so the bootstrap plugin can't restore the session there.
 */
export default defineNuxtRouteMiddleware(() => {
  if (import.meta.server) return;
  const auth = useAuthStore();
  if (!auth.isAuthenticated) {
    const localePath = useLocalePath();
    return navigateTo(localePath("/auth/login"));
  }
  if (!auth.hasRole("admin")) {
    const localePath = useLocalePath();
    return navigateTo(localePath("/"));
  }
});
