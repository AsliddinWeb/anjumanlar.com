<script setup lang="ts">
import type { UserLibraryItem } from "~/types/api";

definePageMeta({ middleware: "auth" });

const { t } = useI18n();
const route = useRoute();
const localePath = useLocalePath();
const api = useApi();
const { localised } = useLocaleText();

const bookId = computed(() => route.params.id as string);

const { data: itemRaw } = await useAsyncData(
  `library:read:${bookId.value}`,
  async () => {
    const list = await api<{ items: UserLibraryItem[]; total: number }>(`/libraries/me`, {
      query: { page_size: 100 },
    });
    return list.items.find((i) => i.book.id === bookId.value) ?? null;
  },
  { server: false },
);
const item = computed<UserLibraryItem | null>(() => itemRaw.value as UserLibraryItem | null);

const title = computed(() =>
  item.value ? localised(item.value.book.title, item.value.book.slug) : t("library.reader.title"),
);

useSiteSeo({ title: title.value, noindex: true });

const ClientReader = defineAsyncComponent(() => import("~/components/book/BookReader.vue"));
</script>

<template>
  <AccountShell>
    <section class="space-y-4">
      <header class="flex items-start justify-between gap-3 flex-wrap">
        <div class="min-w-0">
          <nav class="text-xs text-ink-tertiary mb-1 flex items-center gap-1.5">
            <NuxtLink :to="localePath('/account/library')" class="hover:text-primary">
              {{ t("library.title") }}
            </NuxtLink>
            <Icon name="chevron-down" class="h-3 w-3 -rotate-90" />
            <span class="truncate">{{ title }}</span>
          </nav>
          <h1 class="font-serif text-xl md:text-2xl text-ink leading-tight truncate">
            {{ title }}
          </h1>
          <p v-if="item" class="text-xs text-ink-secondary mt-0.5 truncate">
            {{ item.book.author.display_name }}
          </p>
        </div>
        <UiButton variant="ghost" size="sm" :to="localePath('/account/library')">
          <Icon name="arrow-left" class="h-3.5 w-3.5" />
          {{ t("library.reader.back") }}
        </UiButton>
      </header>

      <ClientOnly>
        <ClientReader v-if="item" :book-id="item.book.id" :title="title" />
        <template #fallback>
          <div class="rounded-md border border-border bg-bg-secondary/40 p-12 text-center text-sm text-ink-tertiary">
            {{ t("library.reader.loading") }}
          </div>
        </template>
      </ClientOnly>

      <p class="text-[11px] text-ink-tertiary leading-relaxed">
        {{ t("library.reader.legal_notice") }}
      </p>
    </section>
  </AccountShell>
</template>
