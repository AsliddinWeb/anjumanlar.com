/**
 * Restore the user's session from localStorage on first client tick.
 *
 * Fire-and-forget — we deliberately don't ``await`` ``bootstrap()``
 * because doing so would block the entire app's first paint behind two
 * HTTP round-trips (``/auth/me`` and possibly ``/auth/refresh``). The
 * UI starts rendering immediately in the anonymous state; auth-aware
 * components reactively flip to the authed state once the request
 * resolves. Auth middleware only runs on the client and consults the
 * already-populated localStorage tokens synchronously to know whether
 * to redirect, so it doesn't need the network round-trip either.
 */
export default defineNuxtPlugin(() => {
  const auth = useAuthStore();
  void auth.bootstrap();
});
