// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: "2024-11-01",
  devtools: { enabled: true },

  modules: [
    "@nuxtjs/tailwindcss",
    "@nuxtjs/i18n",
    "@nuxtjs/color-mode",
    "@pinia/nuxt",
    "@vueuse/nuxt",
    "@nuxt/image",
    "@nuxt/eslint",
  ],

  css: ["~/assets/css/main.css"],

  components: [
    // Auto-import components from ~/components without folder prefixing,
    // so <components/layout/AppHeader.vue> is used as <AppHeader>.
    { path: "~/components", pathPrefix: false },
  ],

  app: {
    head: {
      titleTemplate: "%s · Monografiya.com",
      htmlAttrs: { lang: "uz" },
      meta: [
        { charset: "utf-8" },
        { name: "viewport", content: "width=device-width, initial-scale=1" },
        { name: "format-detection", content: "telephone=no" },
      ],
      link: [
        { rel: "icon", type: "image/svg+xml", href: "/favicon.svg" },
        { rel: "alternate icon", type: "image/x-icon", href: "/favicon.ico" },
        { rel: "apple-touch-icon", href: "/favicon.svg" },
        // Display + body fonts: Playfair Display for headings, DM Sans for copy.
        { rel: "preconnect", href: "https://fonts.googleapis.com" },
        { rel: "preconnect", href: "https://fonts.gstatic.com", crossorigin: "" },
        {
          rel: "stylesheet",
          href: "https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&display=swap",
        },
      ],
    },
  },

  // Nuxt auto-substitutes NUXT_*  /  NUXT_PUBLIC_* env vars into the
  // runtimeConfig tree at boot; the defaults below act as dev fallbacks only.
  //
  // ``apiBaseInternal`` is server-only — Nuxt SSR runs inside the frontend
  // Docker container which can't reach ``localhost:8307`` (the host port),
  // so server-rendered requests must use the in-network ``backend:8000``
  // hostname. The browser uses ``public.apiBase`` for the same calls.
  runtimeConfig: {
    apiBaseInternal: "http://backend:8000/api/v1",
    public: {
      apiBase: "http://localhost:8307/api/v1",
      siteUrl: "http://localhost:8308",
      siteName: "Monografiya.com",
      defaultLocale: "uz",
      // Sentry — left blank in dev so the plugin no-ops. Production
      // wires it via NUXT_PUBLIC_SENTRY_DSN + NUXT_PUBLIC_SENTRY_ENV.
      sentryDsn: "",
      sentryEnvironment: "development",
    },
  },

  i18n: {
    defaultLocale: "uz",
    strategy: "prefix",
    langDir: "locales/",
    locales: [
      { code: "uz", iso: "uz-UZ", file: "uz.json", name: "O'zbekcha" },
      { code: "ru", iso: "ru-RU", file: "ru.json", name: "Русский" },
      { code: "en", iso: "en-US", file: "en.json", name: "English" },
    ],
    lazy: true,
    detectBrowserLanguage: {
      useCookie: true,
      cookieKey: "i18n_redirected",
      redirectOn: "root",
      fallbackLocale: "uz",
    },
  },

  colorMode: {
    preference: "system",
    fallback: "light",
    classSuffix: "",
    storageKey: "monografiya-color-mode",
  },

  tailwindcss: {
    cssPath: "~/assets/css/main.css",
    viewer: false,
  },

  typescript: {
    strict: true,
    typeCheck: false,
  },

  nitro: {
    compressPublicAssets: true,
  },

  vite: {
    server: {
      hmr: {
        // Match the host port so the browser reaches the HMR socket via Nginx-less direct mapping.
        clientPort: 8308,
      },
    },
  },
});
