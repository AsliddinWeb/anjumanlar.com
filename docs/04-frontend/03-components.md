# Komponentlar (Components)

Nuxt 3 `components/` papkasidagi barcha komponentlarni avtomatik import qiladi. Pastki papka nomi prefiks bo'lib qo'shiladi (masalan, `components/book/Card.vue` → `<BookCard />`).

## Komponentlar tuzilmasi

```
components/
├── common/
│   ├── Button.vue
│   ├── Input.vue
│   ├── Textarea.vue
│   ├── Select.vue
│   ├── Checkbox.vue
│   ├── RadioGroup.vue
│   ├── FileUpload.vue
│   ├── Modal.vue
│   ├── Drawer.vue
│   ├── Dropdown.vue
│   ├── Tabs.vue
│   ├── Badge.vue
│   ├── Avatar.vue
│   ├── Pagination.vue
│   ├── Breadcrumb.vue
│   ├── EmptyState.vue
│   ├── LoadingSpinner.vue
│   ├── SkeletonLoader.vue
│   ├── ConfirmDialog.vue
│   ├── ImageWithFallback.vue
│   ├── Rating.vue
│   └── PriceTag.vue
│
├── layout/
│   ├── AppHeader.vue
│   ├── AppFooter.vue
│   ├── AppLogo.vue
│   ├── MainNav.vue
│   ├── MobileNav.vue
│   ├── LanguageSwitcher.vue
│   ├── ThemeToggle.vue
│   ├── UserMenu.vue
│   ├── CartBadge.vue
│   ├── SearchBar.vue
│   ├── AdminSidebar.vue
│   ├── AdminTopbar.vue
│   └── AuthorSidebar.vue
│
├── book/
│   ├── BookCard.vue
│   ├── BookGrid.vue
│   ├── BookList.vue
│   ├── BookDetail.vue
│   ├── BookCover.vue
│   ├── BookPriceBox.vue
│   ├── BookMeta.vue
│   ├── BookDescription.vue
│   ├── BookPreview.vue          # PDF demo viewer
│   ├── BookFilter.vue
│   ├── BookSort.vue
│   ├── RelatedBooks.vue
│   ├── BookUploadForm.vue
│   └── BookStats.vue
│
├── auth/
│   ├── LoginForm.vue
│   ├── RegisterForm.vue
│   ├── ForgotPasswordForm.vue
│   ├── ResetPasswordForm.vue
│   ├── VerifyEmailNotice.vue
│   └── SocialLogin.vue
│
├── review/
│   ├── ReviewCard.vue
│   ├── ReviewList.vue
│   ├── ReviewForm.vue
│   └── ReviewSummary.vue
│
├── checkout/
│   ├── CartItem.vue
│   ├── CartSummary.vue
│   ├── PaymentMethodSelector.vue
│   └── CheckoutForm.vue
│
├── author/
│   ├── AuthorCard.vue
│   ├── AuthorProfile.vue
│   ├── EarningsChart.vue
│   ├── WithdrawalForm.vue
│   └── BookAnalytics.vue
│
└── admin/
    ├── StatsCard.vue
    ├── RevenueChart.vue
    ├── UserTable.vue
    ├── BookTable.vue
    ├── OrderTable.vue
    ├── PendingApprovals.vue
    └── SettingsForm.vue
```

## Asosiy komponent misollari

### components/common/Button.vue

```vue
<script setup lang="ts">
interface Props {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  disabled?: boolean
  type?: 'button' | 'submit' | 'reset'
  to?: string
  href?: string
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  type: 'button',
})

const classes = computed(() => [
  'btn',
  {
    'btn-primary': props.variant === 'primary',
    'btn-secondary': props.variant === 'secondary',
    'btn-ghost': props.variant === 'ghost',
    'btn-danger': props.variant === 'danger',
    'text-sm px-3 py-1.5': props.size === 'sm',
    'text-base px-4 py-2': props.size === 'md',
    'text-lg px-6 py-3': props.size === 'lg',
    'opacity-50 cursor-not-allowed': props.disabled || props.loading,
  },
])

const Tag = computed(() => {
  if (props.to) return resolveComponent('NuxtLink')
  if (props.href) return 'a'
  return 'button'
})
</script>

<template>
  <component
    :is="Tag"
    :to="to"
    :href="href"
    :type="!to && !href ? type : undefined"
    :disabled="disabled || loading"
    :class="classes"
  >
    <span v-if="loading" class="mr-2">
      <CommonLoadingSpinner size="sm" />
    </span>
    <slot />
  </component>
</template>
```

### components/book/BookCard.vue

```vue
<script setup lang="ts">
import type { Book } from '~/types'

const props = defineProps<{
  book: Book
}>()

const { locale } = useI18n()
const localePath = useLocalePath()

const title = computed(() => props.book.title[locale.value] || props.book.title.uz)
const isFree = computed(() => props.book.price === 0)
</script>

<template>
  <NuxtLink
    :to="localePath(`/books/${book.slug}`)"
    class="group block card hover:shadow-lg transition-shadow duration-300"
  >
    <div class="aspect-[2/3] overflow-hidden rounded-t-lg bg-primary-100 dark:bg-ink-light/20">
      <CommonImageWithFallback
        :src="book.cover_url"
        :alt="title"
        class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
      />
    </div>

    <div class="p-4">
      <div class="mb-2 flex items-center gap-2">
        <CommonBadge v-if="isFree" variant="success">{{ $t('book.free') }}</CommonBadge>
        <CommonBadge v-else variant="primary">{{ $t('book.paid') }}</CommonBadge>
        <CommonRating :value="book.average_rating" :count="book.reviews_count" size="sm" />
      </div>

      <h3 class="font-display text-lg font-semibold line-clamp-2 mb-1">
        {{ title }}
      </h3>

      <p class="text-sm text-ink/70 dark:text-ink-dark/70 mb-3">
        {{ book.author.full_name }}
      </p>

      <BookPriceBox :price="book.price" :discount="book.discount_price" />
    </div>
  </NuxtLink>
</template>
```

### components/layout/AppHeader.vue

```vue
<script setup lang="ts">
const { user, logout } = useAuth()
const localePath = useLocalePath()
const { t } = useI18n()
</script>

<template>
  <header class="sticky top-0 z-50 bg-paper/95 dark:bg-paper-dark/95 backdrop-blur border-b border-primary-100 dark:border-primary-900/40">
    <div class="container mx-auto px-4">
      <div class="flex items-center justify-between h-16">
        <!-- Logo -->
        <NuxtLink :to="localePath('/')" class="flex items-center gap-2">
          <LayoutAppLogo />
          <span class="font-display text-xl font-bold">Monografiya</span>
        </NuxtLink>

        <!-- Nav -->
        <nav class="hidden md:flex items-center gap-6">
          <NuxtLink :to="localePath('/books')" class="hover:text-primary-600">
            {{ t('nav.books') }}
          </NuxtLink>
          <NuxtLink :to="localePath('/categories')" class="hover:text-primary-600">
            {{ t('nav.categories') }}
          </NuxtLink>
          <NuxtLink :to="localePath('/authors')" class="hover:text-primary-600">
            {{ t('nav.authors') }}
          </NuxtLink>
          <NuxtLink :to="localePath('/blog')" class="hover:text-primary-600">
            {{ t('nav.blog') }}
          </NuxtLink>
        </nav>

        <!-- Right -->
        <div class="flex items-center gap-3">
          <LayoutSearchBar />
          <LayoutThemeToggle />
          <LayoutLanguageSwitcher />
          
          <template v-if="user">
            <LayoutUserMenu :user="user" @logout="logout" />
          </template>
          <template v-else>
            <NuxtLink :to="localePath('/auth/login')" class="btn-secondary">
              {{ t('auth.login') }}
            </NuxtLink>
          </template>
        </div>
      </div>
    </div>
  </header>
</template>
```

### components/layout/ThemeToggle.vue

```vue
<script setup lang="ts">
const colorMode = useColorMode()

function toggle() {
  colorMode.preference = colorMode.value === 'dark' ? 'light' : 'dark'
}
</script>

<template>
  <button
    @click="toggle"
    class="p-2 rounded-md hover:bg-primary-100 dark:hover:bg-primary-900/40"
    :aria-label="colorMode.value === 'dark' ? 'Kunduzgi rejim' : 'Tungi rejim'"
  >
    <Icon v-if="colorMode.value === 'dark'" name="heroicons:sun" class="w-5 h-5" />
    <Icon v-else name="heroicons:moon" class="w-5 h-5" />
  </button>
</template>
```

### components/layout/LanguageSwitcher.vue

```vue
<script setup lang="ts">
const { locale, locales, setLocale } = useI18n()
const switchLocalePath = useSwitchLocalePath()

const currentLocale = computed(() =>
  locales.value.find(l => l.code === locale.value)
)
</script>

<template>
  <Menu as="div" class="relative">
    <MenuButton class="p-2 rounded-md hover:bg-primary-100 dark:hover:bg-primary-900/40 flex items-center gap-1">
      <Icon name="heroicons:language" class="w-5 h-5" />
      <span class="text-sm font-medium uppercase">{{ currentLocale.code }}</span>
    </MenuButton>

    <MenuItems class="absolute right-0 mt-2 w-40 origin-top-right rounded-md bg-white dark:bg-ink-light shadow-lg ring-1 ring-black/5 focus:outline-none">
      <MenuItem v-for="l in locales" :key="l.code" v-slot="{ active }">
        <NuxtLink
          :to="switchLocalePath(l.code)"
          :class="[
            active ? 'bg-primary-50 dark:bg-primary-900/40' : '',
            l.code === locale ? 'font-semibold' : '',
            'block px-4 py-2 text-sm'
          ]"
        >
          {{ l.name }}
        </NuxtLink>
      </MenuItem>
    </MenuItems>
  </Menu>
</template>
```

## Composables

### composables/useAuth.ts

```typescript
import type { User } from '~/types'

export const useAuth = () => {
  const user = useState<User | null>('auth.user', () => null)
  const token = useCookie<string | null>('access_token', {
    maxAge: 60 * 30, // 30 min
    sameSite: 'lax',
  })
  const refreshToken = useCookie<string | null>('refresh_token', {
    maxAge: 60 * 60 * 24 * 7, // 7 kun
    sameSite: 'lax',
    httpOnly: false,
  })

  const isAuthenticated = computed(() => !!user.value)

  async function login(email: string, password: string) {
    const { $api } = useNuxtApp()
    const res = await $api<{ access_token: string; refresh_token: string }>('/auth/login', {
      method: 'POST',
      body: { email, password },
    })
    token.value = res.access_token
    refreshToken.value = res.refresh_token
    await fetchUser()
  }

  async function fetchUser() {
    const { $api } = useNuxtApp()
    try {
      user.value = await $api<User>('/auth/me')
    } catch {
      user.value = null
    }
  }

  async function logout() {
    const { $api } = useNuxtApp()
    try { await $api('/auth/logout', { method: 'POST' }) } catch {}
    token.value = null
    refreshToken.value = null
    user.value = null
    await navigateTo('/')
  }

  return { user, token, isAuthenticated, login, logout, fetchUser }
}
```

### composables/useApi.ts

```typescript
export const useApi = () => {
  const config = useRuntimeConfig()
  const token = useCookie<string | null>('access_token')

  return $fetch.create({
    baseURL: config.public.apiBase,
    onRequest({ options }) {
      if (token.value) {
        options.headers = {
          ...options.headers,
          Authorization: `Bearer ${token.value}`,
        }
      }
    },
    onResponseError({ response }) {
      if (response.status === 401) {
        navigateTo('/auth/login')
      }
    },
  })
}
```

### plugins/api.ts

```typescript
export default defineNuxtPlugin(() => {
  return {
    provide: {
      api: useApi(),
    },
  }
})
```

**Keyingi qadam:** `04-frontend/04-i18n.md`
