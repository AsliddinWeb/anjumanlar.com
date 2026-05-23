/**
 * Wire @sentry/vue on the client. No-op when the DSN is empty so dev
 * runs don't ship local errors upstream and CI doesn't need a real
 * project key.
 *
 * Lives at order 04 (after auth/wishlist/cart hydration) so any error
 * thrown by those plugins still surfaces — Sentry's global error
 * handler is attached on init.
 */
export default defineNuxtPlugin((nuxtApp) => {
  const runtime = useRuntimeConfig();
  const dsn = runtime.public.sentryDsn as string;
  if (!dsn) return;

  // Lazy import — keeps the bundle off the critical path when Sentry
  // is disabled (every dev preview).
  import("@sentry/vue").then((Sentry) => {
    Sentry.init({
      app: nuxtApp.vueApp,
      dsn,
      environment: (runtime.public.sentryEnvironment as string) || "production",
      // Pageload + navigation tracing. Drop to 0.1 if quota hurts.
      tracesSampleRate: 0.1,
      // Replay on errors only; keeps quota predictable.
      replaysSessionSampleRate: 0,
      replaysOnErrorSampleRate: 1.0,
    });
  });
});
