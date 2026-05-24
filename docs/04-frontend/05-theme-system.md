# Theme System — Tungi/Kunduzgi rejim

`@nuxtjs/color-mode` moduli orqali avtomatik tarzda system preference'ni aniqlaydi, foydalanuvchi tanlovini saqlaydi va SSR'da flash'siz ishlaydi.

## Konfiguratsiya

`nuxt.config.ts` da allaqachon sozlangan:

```typescript
colorMode: {
  preference: 'system',        // foydalanuvchi tanlovi yo'q bo'lsa
  fallback: 'light',           // system aniqlanmasa
  classSuffix: '',             // 'dark-mode' emas, faqat 'dark'
  storageKey: 'monografiya-color-mode',
}
```

Tailwind `darkMode: 'class'` sozlangan. Ya'ni `<html class="dark">` qo'shilganda `dark:` prefiks ishlaydi.

## Toggle komponenti

`components/layout/ThemeToggle.vue` — yuqorida ko'rsatilgan. Uch holat: `light`, `dark`, `system`.

## Yaxshilangan versiya (3 holatli)

```vue
<script setup lang="ts">
import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/vue'

const colorMode = useColorMode()

const themes = [
  { value: 'light', icon: 'heroicons:sun', label: 'Kunduzgi' },
  { value: 'dark', icon: 'heroicons:moon', label: 'Tungi' },
  { value: 'system', icon: 'heroicons:computer-desktop', label: 'Tizim' },
]

const currentIcon = computed(() => {
  const t = themes.find(t => t.value === colorMode.preference)
  return t?.icon || 'heroicons:sun'
})
</script>

<template>
  <Menu as="div" class="relative">
    <MenuButton
      class="p-2 rounded-md hover:bg-primary-100 dark:hover:bg-primary-900/40"
      aria-label="Rejimni o'zgartirish"
    >
      <Icon :name="currentIcon" class="w-5 h-5" />
    </MenuButton>

    <MenuItems class="absolute right-0 mt-2 w-40 origin-top-right rounded-md bg-white dark:bg-ink-light shadow-lg ring-1 ring-black/5 focus:outline-none">
      <MenuItem v-for="t in themes" :key="t.value" v-slot="{ active }">
        <button
          @click="colorMode.preference = t.value"
          :class="[
            active ? 'bg-primary-50 dark:bg-primary-900/40' : '',
            colorMode.preference === t.value ? 'font-semibold text-primary-600' : '',
            'flex items-center gap-2 w-full px-4 py-2 text-sm text-left'
          ]"
        >
          <Icon :name="t.icon" class="w-4 h-4" />
          {{ t.label }}
        </button>
      </MenuItem>
    </MenuItems>
  </Menu>
</template>
```

## Tailwind'da dark mode foydalanish

```vue
<template>
  <!-- Fon va matn -->
  <div class="bg-paper text-ink dark:bg-paper-dark dark:text-ink-dark">
    
    <!-- Card -->
    <div class="bg-white dark:bg-ink-light/40 border border-primary-100 dark:border-primary-900/40">
      
      <!-- Tugma -->
      <button class="bg-primary-600 dark:bg-primary-500 text-white hover:bg-primary-700 dark:hover:bg-primary-600">
        Bosing
      </button>
      
      <!-- Input -->
      <input class="bg-white dark:bg-ink-light/40 border-primary-200 dark:border-primary-800" />
    </div>
  </div>
</template>
```

## CSS o'zgaruvchilari yondashuvi (qo'shimcha)

Murakkab komponentlar uchun CSS variables foydali:

```css
/* assets/css/main.css */

:root {
  --color-bg: 245 241 232;          /* paper */
  --color-bg-elevated: 255 255 255; /* card bg */
  --color-fg: 26 20 16;             /* ink */
  --color-fg-muted: 100 90 75;
  --color-border: 243 220 192;      /* primary-200 */
  --color-primary: 201 132 73;      /* primary-500 */
  --shadow-soft: 0 1px 3px rgb(0 0 0 / 0.05);
}

.dark {
  --color-bg: 26 22 18;             /* paper-dark */
  --color-bg-elevated: 35 30 25;
  --color-fg: 232 226 212;          /* ink-dark */
  --color-fg-muted: 168 158 142;
  --color-border: 122 69 48;        /* primary-800 */
  --color-primary: 219 161 106;     /* primary-400 */
  --shadow-soft: 0 1px 3px rgb(0 0 0 / 0.3);
}
```

Foydalanish:

```css
.my-card {
  background: rgb(var(--color-bg-elevated));
  color: rgb(var(--color-fg));
  border: 1px solid rgb(var(--color-border));
  box-shadow: var(--shadow-soft);
}
```

## Flash of unstyled content (FOUC) oldini olish

`@nuxtjs/color-mode` buni avtomatik hal qiladi — `<html>` teg'iga script inject qiladi va class to'g'ri o'rnatiladi script run bo'lishidan oldin.

Qo'shimcha xavfsizlik uchun `app.vue` da:

```vue
<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>

<script setup>
// SSR'da color-mode dan foydalansak
const colorMode = useColorMode()

useHead({
  htmlAttrs: {
    class: computed(() => colorMode.value),
  },
})
</script>
```

## PDF Preview rejimga moslashish

PDF demo viewer ham dark/light rejimga moslashishi kerak:

```vue
<script setup lang="ts">
import VuePdfEmbed from 'vue-pdf-embed'

const colorMode = useColorMode()

const isDark = computed(() => colorMode.value === 'dark')
</script>

<template>
  <div
    class="pdf-viewer"
    :class="{ 'dark-pdf': isDark }"
  >
    <VuePdfEmbed :source="demoUrl" />
  </div>
</template>

<style scoped>
.dark-pdf :deep(.vue-pdf-embed__page) {
  filter: invert(0.92) hue-rotate(180deg);
}
</style>
```

## Rasm va logotipga moslashish

Logo va illyustratsiyalar uchun dark mode versiyasi:

```vue
<template>
  <ClientOnly>
    <img
      :src="colorMode.value === 'dark' ? '/logo-dark.svg' : '/logo-light.svg'"
      alt="Monografiya"
    />
    <template #fallback>
      <img src="/logo-light.svg" alt="Monografiya" />
    </template>
  </ClientOnly>
</template>
```

Yoki CSS orqali:

```html
<img src="/logo-light.svg" class="block dark:hidden" alt="Monografiya" />
<img src="/logo-dark.svg" class="hidden dark:block" alt="Monografiya" />
```

## Foydalanuvchi profilida saqlash

Agar foydalanuvchi ro'yxatdan o'tgan bo'lsa, theme tanlovini DB'da ham saqlash mumkin:

```typescript
// composables/useThemeSync.ts
export const useThemeSync = () => {
  const colorMode = useColorMode()
  const { user, isAuthenticated } = useAuth()
  const { $api } = useNuxtApp()

  // Login bo'lganda DB dan yuklaymiz
  watch(isAuthenticated, async (val) => {
    if (val && user.value?.preferences?.theme) {
      colorMode.preference = user.value.preferences.theme
    }
  })

  // O'zgarganda DB ga saqlaymiz
  watch(() => colorMode.preference, async (newVal) => {
    if (isAuthenticated.value) {
      await $api('/users/me/preferences', {
        method: 'PATCH',
        body: { theme: newVal },
      })
    }
  })
}
```

**Keyingi qadam:** `05-database/01-schema.md`
