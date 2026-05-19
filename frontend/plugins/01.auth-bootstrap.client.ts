/**
 * Once on first client hydration, try to restore the session from the
 * refresh cookie. SSR can't see httpOnly cookies, so we keep this strictly
 * client-side — the very first render is unauthenticated, then this plugin
 * fires and the UI updates if the cookie was valid.
 */
export default defineNuxtPlugin(async () => {
  const auth = useAuthStore();
  await auth.bootstrap();
});
