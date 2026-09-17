<script setup lang="ts">
import type { SiteSettingsPublic } from "~/types/api";

const { t } = useI18n();
const localePath = useLocalePath();
const api = useApi();

const year = new Date().getFullYear();

const { data: settingsRaw } = await useAsyncData(
  "footer:settings",
  () => api<SiteSettingsPublic>("/settings"),
);
const settings = computed(() => settingsRaw.value);

const socialLinks = computed(() => [
  { label: "Telegram", url: settings.value?.telegram_url },
  { label: "Instagram", url: settings.value?.instagram_url },
  { label: "Facebook", url: settings.value?.facebook_url },
  { label: "YouTube", url: settings.value?.youtube_url },
].filter((l) => l.url));

const exploreLinks = computed(() => [
  { to: "/books", label: t("nav.books") },
  { to: "/authors", label: t("nav.authors") },
  { to: "/search", label: t("search.title") },
  { to: "/blog", label: t("nav.blog") },
]);

const companyLinks = computed(() => [
  { to: "/about", label: t("nav.about") },
  { to: "/authors/me", label: t("home.hero.cta_become_author") },
]);

const legalLinks = computed(() => [
  { to: "/legal/terms", label: t("footer.terms") },
  { to: "/legal/privacy", label: t("footer.privacy") },
]);
</script>

<template>
  <footer class="border-t border-border mt-12 bg-bg-secondary">
    <div class="max-w-6xl mx-auto px-4 py-10 grid gap-8 md:grid-cols-4 sm:grid-cols-2">
      <!-- Brand -->
      <div class="space-y-2">
        <NuxtLink
          :to="localePath('/')"
          class="font-serif font-bold text-lg text-primary"
        >
          {{ t("site.title") }}
        </NuxtLink>
        <p class="text-sm text-ink-secondary">{{ t("footer.tagline") }}</p>
      </div>

      <!-- Explore -->
      <div>
        <h4 class="text-sm font-medium text-ink mb-3">{{ t("footer.explore") }}</h4>
        <ul class="space-y-2 text-sm">
          <li v-for="l in exploreLinks" :key="l.to">
            <NuxtLink
              :to="localePath(l.to)"
              class="text-ink-secondary hover:text-primary"
            >
              {{ l.label }}
            </NuxtLink>
          </li>
        </ul>
      </div>

      <!-- Company -->
      <div>
        <h4 class="text-sm font-medium text-ink mb-3">{{ t("footer.company") }}</h4>
        <ul class="space-y-2 text-sm">
          <li v-for="l in companyLinks" :key="l.to">
            <NuxtLink
              :to="localePath(l.to)"
              class="text-ink-secondary hover:text-primary"
            >
              {{ l.label }}
            </NuxtLink>
          </li>
          <li v-if="settings?.contact_email">
            <a
              :href="`mailto:${settings.contact_email}`"
              class="text-ink-secondary hover:text-primary"
            >
              {{ settings.contact_email }}
            </a>
          </li>
          <li v-if="settings?.contact_phone">
            <a
              :href="`tel:${settings.contact_phone.replace(/\\s+/g, '')}`"
              class="text-ink-secondary hover:text-primary"
            >
              {{ settings.contact_phone }}
            </a>
          </li>
          <li v-if="settings?.contact_name" class="text-ink-tertiary">
            {{ settings.contact_name }}
          </li>
        </ul>
      </div>

      <!-- Legal + social -->
      <div class="space-y-4">
        <div>
          <h4 class="text-sm font-medium text-ink mb-3">{{ t("footer.legal") }}</h4>
          <ul class="space-y-2 text-sm">
            <li v-for="l in legalLinks" :key="l.to">
              <NuxtLink
                :to="localePath(l.to)"
                class="text-ink-secondary hover:text-primary"
              >
                {{ l.label }}
              </NuxtLink>
            </li>
          </ul>
        </div>
        <div v-if="socialLinks.length">
          <h4 class="text-sm font-medium text-ink mb-3">{{ t("footer.follow") }}</h4>
          <div class="flex items-center gap-3 text-sm">
            <a
              v-for="l in socialLinks"
              :key="l.label"
              :href="l.url!"
              target="_blank"
              rel="noopener noreferrer"
              class="text-ink-secondary hover:text-primary"
              :aria-label="l.label"
            >
              {{ l.label }}
            </a>
          </div>
        </div>
      </div>
    </div>

    <div class="border-t border-border">
      <div class="max-w-6xl mx-auto px-4 py-4 text-xs text-ink-tertiary flex flex-wrap justify-between gap-2">
        <span>© {{ year }} {{ t("site.title") }}. {{ t("footer.rights") }}</span>
        <span>{{ t("home.hero.subtitle") }}</span>
      </div>
    </div>
  </footer>
</template>
