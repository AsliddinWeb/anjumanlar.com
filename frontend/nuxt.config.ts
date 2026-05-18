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
      titleTemplate: "%s · Anjumanlar.com",
      htmlAttrs: { lang: "uz" },
      meta: [
        { charset: "utf-8" },
        { name: "viewport", content: "width=device-width, initial-scale=1" },
        { name: "format-detection", content: "telephone=no" },
      ],
      link: [{ rel: "icon", type: "image/x-icon", href: "/favicon.ico" }],
    },
  },

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || "http://localhost:8307/api/v1",
      siteUrl: process.env.NUXT_PUBLIC_SITE_URL || "http://localhost:8308",
      siteName: process.env.NUXT_PUBLIC_SITE_NAME || "Anjumanlar.com",
      defaultLocale: process.env.NUXT_PUBLIC_DEFAULT_LOCALE || "uz",
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
    storageKey: "anjumanlar-color-mode",
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
