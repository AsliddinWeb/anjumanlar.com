# Pages va Routes

Nuxt 3 file-based routing ishlatadi. Har bir `.vue` fayl `pages/` ichida — alohida route.

## Routes tuzilmasi

```
pages/
├── index.vue                          → /
├── books/
│   ├── index.vue                      → /books
│   └── [slug].vue                     → /books/:slug
├── categories/
│   ├── index.vue                      → /categories
│   └── [slug].vue                     → /categories/:slug
├── authors/
│   ├── index.vue                      → /authors
│   └── [slug].vue                     → /authors/:slug
├── search.vue                         → /search
├── about.vue                          → /about
├── contact.vue                        → /contact
├── help.vue                           → /help
├── terms.vue                          → /terms
├── privacy.vue                        → /privacy
├── blog/
│   ├── index.vue                      → /blog
│   └── [slug].vue                     → /blog/:slug
│
├── auth/
│   ├── login.vue                      → /auth/login
│   ├── register.vue                   → /auth/register
│   ├── forgot-password.vue            → /auth/forgot-password
│   ├── reset-password.vue             → /auth/reset-password
│   └── verify-email.vue               → /auth/verify-email
│
├── account/
│   ├── index.vue                      → /account
│   ├── profile.vue                    → /account/profile
│   ├── orders/
│   │   ├── index.vue                  → /account/orders
│   │   └── [id].vue                   → /account/orders/:id
│   ├── library.vue                    → /account/library
│   ├── wishlist.vue                   → /account/wishlist
│   ├── settings.vue                   → /account/settings
│   └── security.vue                   → /account/security
│
├── author/
│   ├── index.vue                      → /author (dashboard)
│   ├── books/
│   │   ├── index.vue                  → /author/books
│   │   ├── new.vue                    → /author/books/new
│   │   └── [id]/
│   │       ├── edit.vue               → /author/books/:id/edit
│   │       └── analytics.vue          → /author/books/:id/analytics
│   ├── earnings.vue                   → /author/earnings
│   ├── withdrawals.vue                → /author/withdrawals
│   ├── reviews.vue                    → /author/reviews
│   └── profile.vue                    → /author/profile
│
├── admin/
│   ├── index.vue                      → /admin (dashboard)
│   ├── users/
│   │   ├── index.vue                  → /admin/users
│   │   └── [id].vue                   → /admin/users/:id
│   ├── books/
│   │   ├── index.vue                  → /admin/books
│   │   ├── pending.vue                → /admin/books/pending
│   │   └── [id].vue                   → /admin/books/:id
│   ├── categories.vue                 → /admin/categories
│   ├── orders.vue                     → /admin/orders
│   ├── payments.vue                   → /admin/payments
│   ├── withdrawals.vue                → /admin/withdrawals
│   ├── reviews.vue                    → /admin/reviews
│   ├── reports.vue                    → /admin/reports
│   ├── blog/
│   │   ├── index.vue                  → /admin/blog
│   │   ├── new.vue                    → /admin/blog/new
│   │   └── [id]/edit.vue              → /admin/blog/:id/edit
│   └── settings.vue                   → /admin/settings (superadmin only)
│
├── checkout/
│   ├── index.vue                      → /checkout
│   ├── success.vue                    → /checkout/success
│   └── failed.vue                     → /checkout/failed
│
└── [...slug].vue                      → 404
```

## Layouts taqsimoti

| Path prefiks | Layout | Middleware |
|---|---|---|
| `/` (public) | `default.vue` | yo'q |
| `/auth/*` | `auth.vue` | `guest` |
| `/account/*` | `default.vue` | `auth` |
| `/author/*` | `author.vue` | `auth` + `author` |
| `/admin/*` | `admin.vue` | `auth` + `admin` |

## Layout misollari

### layouts/default.vue

```vue
<template>
  <div class="min-h-screen flex flex-col">
    <AppHeader />
    <main class="flex-1">
      <slot />
    </main>
    <AppFooter />
  </div>
</template>
```

### layouts/admin.vue

```vue
<template>
  <div class="min-h-screen flex bg-paper dark:bg-paper-dark">
    <AdminSidebar />
    <div class="flex-1 flex flex-col">
      <AdminTopbar />
      <main class="flex-1 p-6 overflow-auto">
        <slot />
      </main>
    </div>
  </div>
</template>
```

### layouts/author.vue

```vue
<template>
  <div class="min-h-screen flex bg-paper dark:bg-paper-dark">
    <AuthorSidebar />
    <div class="flex-1 flex flex-col">
      <AppHeader minimal />
      <main class="flex-1 p-6">
        <slot />
      </main>
    </div>
  </div>
</template>
```

## Middleware misollari

### middleware/auth.ts

```typescript
export default defineNuxtRouteMiddleware((to) => {
  const { isAuthenticated } = useAuth()
  
  if (!isAuthenticated.value) {
    return navigateTo({
      path: '/auth/login',
      query: { redirect: to.fullPath }
    })
  }
})
```

### middleware/admin.ts

```typescript
export default defineNuxtRouteMiddleware(() => {
  const { user } = useAuth()
  
  if (!user.value || !['admin', 'superadmin'].includes(user.value.role)) {
    throw createError({
      statusCode: 403,
      statusMessage: 'Forbidden'
    })
  }
})
```

### middleware/author.ts

```typescript
export default defineNuxtRouteMiddleware(() => {
  const { user } = useAuth()
  
  if (!user.value || !['author', 'admin', 'superadmin'].includes(user.value.role)) {
    return navigateTo('/account')
  }
})
```

## Sahifa misoli — kitob detali

### pages/books/[slug].vue

```vue
<script setup lang="ts">
import type { Book } from '~/types'

const route = useRoute()
const { $api } = useNuxtApp()

const { data: book, error } = await useAsyncData<Book>(
  `book-${route.params.slug}`,
  () => $api(`/books/${route.params.slug}`)
)

if (error.value) {
  throw createError({
    statusCode: 404,
    statusMessage: 'Kitob topilmadi'
  })
}

// SEO meta
useSeoMeta({
  title: () => book.value?.title?.uz || 'Kitob',
  description: () => book.value?.description?.uz?.slice(0, 160),
  ogTitle: () => book.value?.title?.uz,
  ogDescription: () => book.value?.description?.uz?.slice(0, 160),
  ogImage: () => book.value?.cover_url,
  ogType: 'book',
  twitterCard: 'summary_large_image',
})

// JSON-LD strukturlangan ma'lumot
useSchemaOrg([
  defineBook({
    name: book.value?.title?.uz,
    author: book.value?.author?.full_name,
    isbn: book.value?.isbn,
    bookFormat: 'EBook',
    inLanguage: 'uz',
    image: book.value?.cover_url,
    offers: {
      '@type': 'Offer',
      price: book.value?.price,
      priceCurrency: 'UZS',
      availability: 'https://schema.org/InStock',
    },
  }),
])
</script>

<template>
  <div class="container mx-auto px-4 py-8">
    <BookDetail v-if="book" :book="book" />
  </div>
</template>
```

## SSR/SSG strategiya

| Sahifa turi | Render usuli | Sabab |
|---|---|---|
| Bosh sahifa | SSR | Dinamik kontent, SEO muhim |
| Kitob detali | SSR | SEO + dinamik narx |
| Muallif sahifasi | SSR | SEO |
| Blog post | SSG (yoki ISR) | Kam o'zgaradi |
| About / Terms | SSG | Statik |
| Admin/Author panel | CSR | Auth, SEO kerakmas |
| Account sahifalar | CSR | Auth required |

`definePageMeta` orqali sozlash:

```vue
<script setup>
definePageMeta({
  layout: 'admin',
  middleware: ['auth', 'admin'],
  ssr: false, // CSR only
})
</script>
```

**Keyingi qadam:** `04-frontend/03-components.md`
