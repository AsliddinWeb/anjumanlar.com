# Frontend Setup — Nuxt 3 (Vue 3)

## Texnologiyalar

- **Nuxt 3** — Vue 3 framework (SSR/SSG, SEO uchun zarur)
- **Vue 3** — Composition API
- **TypeScript** — type safety
- **Tailwind CSS** — utility-first CSS
- **Pinia** — state management
- **vue-i18n** — 3 til uchun (uz/ru/en)
- **@nuxtjs/color-mode** — dark/light mode
- **@vueuse/core** — composable helpers
- **axios** — HTTP klient (yoki Nuxt'ning `$fetch`)

## Loyihani boshlash

```bash
cd frontend
npx nuxi@latest init .
npm install
```

## package.json (asosiy dependencies)

```json
{
  "name": "monografiya-frontend",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "nuxt dev",
    "build": "nuxt build",
    "preview": "nuxt preview",
    "generate": "nuxt generate",
    "lint": "eslint .",
    "typecheck": "nuxt typecheck"
  },
  "dependencies": {
    "nuxt": "^3.13.0",
    "vue": "^3.5.0",
    "vue-router": "^4.4.0",
    "@nuxtjs/tailwindcss": "^6.12.0",
    "@nuxtjs/i18n": "^8.5.0",
    "@nuxtjs/color-mode": "^3.5.0",
    "@nuxtjs/seo": "^2.0.0",
    "@nuxtjs/sitemap": "^6.0.0",
    "@nuxtjs/robots": "^5.0.0",
    "@pinia/nuxt": "^0.5.0",
    "pinia": "^2.2.0",
    "@vueuse/core": "^11.0.0",
    "@vueuse/nuxt": "^11.0.0",
    "@headlessui/vue": "^1.7.23",
    "@heroicons/vue": "^2.1.5",
    "vue-toastification": "^2.0.0-rc.5",
    "vee-validate": "^4.13.0",
    "yup": "^1.4.0",
    "marked": "^14.1.0",
    "dompurify": "^3.1.0",
    "vue-pdf-embed": "^2.1.0"
  },
  "devDependencies": {
    "@nuxt/eslint-config": "^0.5.0",
    "@types/node": "^22.0.0",
    "autoprefixer": "^10.4.20",
    "eslint": "^9.10.0",
    "postcss": "^8.4.45",
    "tailwindcss": "^3.4.10",
    "typescript": "^5.5.0"
  }
}
```

## nuxt.config.ts

```typescript
export default defineNuxtConfig({
  compatibilityDate: '2024-09-01',
  devtools: { enabled: true },
  
  modules: [
    '@nuxtjs/tailwindcss',
    '@nuxtjs/i18n',
    '@nuxtjs/color-mode',
    '@nuxtjs/seo',
    '@pinia/nuxt',
    '@vueuse/nuxt',
  ],

  // SSR yoqilgan — SEO uchun zarur
  ssr: true,

  // Runtime config
  runtimeConfig: {
    public: {
      apiBase: process.env.API_BASE_URL || 'http://localhost:8000/api/v1',
      siteUrl: process.env.SITE_URL || 'https://monografiya.com',
      siteName: 'Monografiya',
    },
  },

  // i18n config
  i18n: {
    locales: [
      { code: 'uz', name: "O'zbekcha", file: 'uz.json', iso: 'uz-UZ' },
      { code: 'ru', name: 'Русский', file: 'ru.json', iso: 'ru-RU' },
      { code: 'en', name: 'English', file: 'en.json', iso: 'en-US' },
    ],
    defaultLocale: 'uz',
    strategy: 'prefix_except_default',
    lazy: true,
    langDir: 'locales/',
    detectBrowserLanguage: {
      useCookie: true,
      cookieKey: 'i18n_redirected',
      redirectOn: 'root',
    },
  },

  // Color mode
  colorMode: {
    preference: 'system',
    fallback: 'light',
    classSuffix: '',
    storageKey: 'monografiya-color-mode',
  },

  // Tailwind
  tailwindcss: {
    cssPath: '~/assets/css/main.css',
    configPath: 'tailwind.config.ts',
  },

  // SEO
  site: {
    url: process.env.SITE_URL || 'https://monografiya.com',
    name: 'Monografiya',
  },

  // App config
  app: {
    head: {
      htmlAttrs: { lang: 'uz' },
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'format-detection', content: 'telephone=no' },
      ],
      link: [
        { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' },
        // Preconnect for Google Fonts
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
      ],
    },
    pageTransition: { name: 'page', mode: 'out-in' },
  },

  // Build
  nitro: {
    compressPublicAssets: true,
  },
})
```

## tailwind.config.ts

```typescript
import type { Config } from 'tailwindcss'

export default <Config>{
  darkMode: 'class',
  content: [
    './components/**/*.{vue,js,ts}',
    './layouts/**/*.vue',
    './pages/**/*.vue',
    './plugins/**/*.{js,ts}',
    './app.vue',
    './error.vue',
  ],
  theme: {
    extend: {
      colors: {
        // Brand — qadimiy kitob estetikasi
        primary: {
          50: '#fdf8f3',
          100: '#faf0e3',
          200: '#f3dcc0',
          300: '#e9c197',
          400: '#dba16a',
          500: '#c98449',
          600: '#b66c3d',
          700: '#975434',
          800: '#7a4530',
          900: '#643a2a',
          950: '#351c14',
        },
        // Paper/ink — kitob teksturasi
        paper: {
          light: '#faf7f2',
          DEFAULT: '#f5f1e8',
          dark: '#1a1612',
        },
        ink: {
          light: '#2c2418',
          DEFAULT: '#1a1410',
          dark: '#e8e2d4',
        },
        // Accent
        accent: {
          gold: '#c9a449',
          burgundy: '#7a2e2e',
          forest: '#3a5a40',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        serif: ['Lora', 'Georgia', 'serif'],
        display: ['Playfair Display', 'serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      typography: {
        DEFAULT: {
          css: {
            maxWidth: 'none',
            color: 'rgb(26 20 16)',
            fontFamily: 'Lora, Georgia, serif',
          },
        },
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.4s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('@tailwindcss/aspect-ratio'),
  ],
}
```

## assets/css/main.css

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Lora:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Playfair+Display:wght@600;700;800&display=swap');

@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  html {
    font-family: 'Inter', system-ui, sans-serif;
    scroll-behavior: smooth;
  }

  body {
    @apply bg-paper text-ink antialiased;
    @apply dark:bg-paper-dark dark:text-ink-dark;
  }

  h1, h2, h3, h4, h5, h6 {
    font-family: 'Playfair Display', serif;
    @apply font-bold;
  }
}

@layer components {
  .btn {
    @apply inline-flex items-center justify-center px-4 py-2 rounded-md font-medium;
    @apply transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2;
  }

  .btn-primary {
    @apply btn bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500;
    @apply dark:bg-primary-500 dark:hover:bg-primary-600;
  }

  .btn-secondary {
    @apply btn bg-paper border border-primary-300 text-ink hover:bg-primary-50;
    @apply dark:bg-paper-dark dark:border-primary-700 dark:text-ink-dark dark:hover:bg-primary-900;
  }

  .card {
    @apply bg-white dark:bg-ink-light/40 rounded-lg shadow-sm border border-primary-100 dark:border-primary-900/40;
  }

  .input {
    @apply w-full px-3 py-2 rounded-md border border-primary-200 bg-white;
    @apply dark:bg-ink-light/40 dark:border-primary-800 dark:text-ink-dark;
    @apply focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent;
  }
}
```

## .env.example

```env
API_BASE_URL=http://localhost:8000/api/v1
SITE_URL=http://localhost:3000
```

## Dockerfile (frontend)

```dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Production stage
FROM node:20-alpine AS production
WORKDIR /app

COPY --from=builder /app/.output ./.output
COPY --from=builder /app/package.json ./

ENV NODE_ENV=production
ENV NITRO_PORT=3000
ENV NITRO_HOST=0.0.0.0

EXPOSE 3000
CMD ["node", ".output/server/index.mjs"]
```

## Loyiha tuzilmasi

```
frontend/
├── assets/
│   ├── css/main.css
│   └── images/
├── components/
│   ├── common/
│   ├── book/
│   ├── auth/
│   ├── layout/
│   └── admin/
├── composables/
│   ├── useAuth.ts
│   ├── useApi.ts
│   └── useCart.ts
├── layouts/
│   ├── default.vue
│   ├── auth.vue
│   ├── admin.vue
│   └── author.vue
├── locales/
│   ├── uz.json
│   ├── ru.json
│   └── en.json
├── middleware/
│   ├── auth.ts
│   ├── admin.ts
│   └── author.ts
├── pages/
│   ├── index.vue
│   ├── books/
│   ├── auth/
│   ├── account/
│   ├── author/
│   └── admin/
├── plugins/
│   ├── api.ts
│   └── toast.ts
├── stores/
│   ├── auth.ts
│   ├── cart.ts
│   └── books.ts
├── types/
│   └── index.ts
├── public/
├── app.vue
├── error.vue
├── nuxt.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

**Keyingi qadam:** `04-frontend/02-pages-and-routes.md`
