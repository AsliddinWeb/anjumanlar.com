# Monografiya Frontend (Nuxt 3)

Vue 3 + Nuxt 3 + Tailwind + i18n (uz/ru/en) + color-mode + Pinia. SSR by default.

## Local development

The frontend runs inside Docker via the root `docker-compose.yml`:

```bash
make up                 # brings up infra + backend + frontend
make logs s=frontend    # tail frontend logs
```

Open <http://localhost:8308>. The page is served by Nuxt's dev server on port
3000 inside the container, mapped to host **8308**.

Hot module reload works over the same port — `vite.server.hmr.clientPort` in
`nuxt.config.ts` is set to 8308 so the browser connects back correctly.

## Layout

```
frontend/
├── app.vue                         root component
├── nuxt.config.ts                  modules + i18n + color-mode + runtime config
├── tailwind.config.js              maps CSS variables → tailwind utilities
├── assets/css/main.css             light/dark CSS variables + base styles
├── components/
│   ├── layout/                     Header, ThemeToggle, LanguageSwitcher
│   └── ui/                         shared primitives (added in Phase 3)
├── layouts/default.vue
├── pages/index.vue                 skeleton landing
├── locales/{uz,ru,en}.json         translations (loaded lazily)
├── composables/useApi.ts           backend client wrapper
├── stores/ui.ts                    Pinia placeholder
├── middleware/                     auth/guest/admin (added in Phase 1+)
├── public/robots.txt
└── server/                         server-only routes (sitemap, etc.)
```

## i18n

URL strategy is `prefix`: every locale lives under its own path
(`/uz/...`, `/ru/...`, `/en/...`). Browser language is detected on the root
URL and stored in the `i18n_redirected` cookie.

Translations are split into `locales/<code>.json`. Keep keys nested
(`home.hero.title`) and grouped by feature.

## Theme

`@nuxtjs/color-mode` exposes 3 preferences: `light`, `dark`, `system`.
`ThemeToggle.vue` cycles through them. The active class (`dark`) toggles all
CSS variables defined in `assets/css/main.css`.

## Adding a new page

1. Drop a `.vue` file under `pages/` — Nuxt auto-generates the route.
2. For locale-aware navigation use `useLocalePath()` instead of raw paths.
3. Add the route's translation keys to all three `locales/*.json` files.
