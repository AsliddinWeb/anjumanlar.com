/**
 * Inverse of ``auth`` — pages that only make sense when *logged out*
 * (login, register, forgot-password). Bounces authenticated users to
 * /account so they can't accidentally re-login.
 */
export default defineNuxtRouteMiddleware(() => {
  if (import.meta.server) return;
  const auth = useAuthStore();
  if (auth.isAuthenticated) {
    const localePath = useLocalePath();
    return navigateTo(localePath("/account"));
  }
});
