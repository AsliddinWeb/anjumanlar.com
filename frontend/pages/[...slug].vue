<script setup lang="ts">
const { t } = useI18n();
const localePath = useLocalePath();
const router = useRouter();

definePageMeta({
  // Match anything that didn't hit a real route.
});

setResponseStatus(404);

useSiteSeo({
  title: t("error.404_title"),
  description: t("error.404_body"),
  noindex: true,
});

const searchInput = ref("");
async function submitSearch() {
  const q = searchInput.value.trim();
  if (!q) return;
  await router.push({ path: localePath("/search"), query: { q } });
}

const popularLinks = computed(() => [
  { to: "/books", icon: "book" as const, label: t("error.popular.catalog") },
  { to: "/authors", icon: "academic" as const, label: t("error.popular.authors") },
  { to: "/blog", icon: "news" as const, label: t("error.popular.blog") },
  { to: "/about", icon: "sparkles" as const, label: t("error.popular.about") },
]);
</script>

<template>
  <section class="bg-bg">
    <div
      aria-hidden="true"
      class="absolute inset-x-0 top-0 -z-10 h-[60vh] opacity-60"
      style="background-image:
        radial-gradient(ellipse 60% 60% at 50% 0%, color-mix(in oklab, var(--color-primary) 12%, transparent), transparent 65%);"
    />
    <div class="max-w-2xl mx-auto px-4 py-20 md:py-28 text-center space-y-6">
      <div
        class="font-serif text-[6rem] md:text-[9rem] leading-none text-primary/30 tracking-tighter select-none"
      >
        404
      </div>

      <div class="space-y-3">
        <h1 class="font-serif text-3xl md:text-4xl text-ink leading-tight tracking-tight">
          {{ t("error.404_title") }}
        </h1>
        <p class="text-ink-secondary leading-relaxed max-w-md mx-auto">
          {{ t("error.404_body") }}
        </p>
      </div>

      <!-- Search -->
      <form class="relative max-w-md mx-auto pt-2" @submit.prevent="submitSearch">
        <Icon
          name="search"
          class="absolute left-4 top-1/2 -translate-y-1/2 mt-1 h-4 w-4 text-ink-tertiary pointer-events-none"
        />
        <input
          v-model="searchInput"
          type="search"
          :placeholder="t('error.search_placeholder')"
          class="w-full pl-11 pr-4 py-3 rounded-full border border-border bg-bg-card text-ink text-sm placeholder:text-ink-tertiary focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 shadow-sm"
          autocomplete="off"
        >
      </form>

      <!-- Quick links -->
      <div class="pt-2 space-y-3">
        <p class="text-xs uppercase tracking-wider text-ink-tertiary">
          {{ t("error.popular.heading") }}
        </p>
        <div class="flex flex-wrap justify-center gap-2">
          <NuxtLink
            v-for="link in popularLinks"
            :key="link.to"
            :to="localePath(link.to)"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-border bg-bg-card text-sm text-ink-secondary hover:border-primary hover:text-primary transition-colors"
          >
            <Icon :name="link.icon" class="h-3.5 w-3.5" />
            {{ link.label }}
          </NuxtLink>
        </div>
      </div>

      <div class="pt-4">
        <UiButton :to="localePath('/')" size="lg">
          <Icon name="home" class="h-4 w-4" />
          {{ t("error.go_home") }}
        </UiButton>
      </div>
    </div>
  </section>
</template>
