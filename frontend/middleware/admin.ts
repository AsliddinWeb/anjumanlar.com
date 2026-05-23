/**
 * Admin-only guard. Apply alongside the ``auth`` middleware::
 *
 *     definePageMeta({ middleware: ["auth", "admin"] })
 *
 * The order matters — ``auth`` runs first so unauthenticated visitors get
 * the login redirect; logged-in but non-admin users hit ``admin`` and
 * land on the homepage (no leaked existence info, no 403 page to bypass).
 */
export default defineNuxtRouteMiddleware(() => {
  const auth = useAuthStore();
  if (!auth.isAuthenticated) {
    // ``auth`` middleware should have caught this; defensive belt-and-braces
    // in case a page forgets to declare it.
    const localePath = useLocalePath();
    return navigateTo(localePath("/auth/login"));
  }
  if (!auth.hasRole("admin")) {
    const localePath = useLocalePath();
    return navigateTo(localePath("/"));
  }
});
