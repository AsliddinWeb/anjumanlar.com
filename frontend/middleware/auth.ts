/**
 * Page-level guard. Apply with::
 *
 *     definePageMeta({ middleware: "auth" })
 *
 * Redirects unauthenticated visitors to /auth/login, preserving the page
 * they wanted via the ``redirect`` query param so /login can bounce them
 * back after success.
 */
export default defineNuxtRouteMiddleware((to) => {
  const auth = useAuthStore();
  if (!auth.isAuthenticated) {
    const localePath = useLocalePath();
    return navigateTo({
      path: localePath("/auth/login"),
      query: { redirect: to.fullPath },
    });
  }
});
