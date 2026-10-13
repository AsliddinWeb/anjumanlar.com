<script setup lang="ts">
import type { UserLibraryItem } from "~/types/api";
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({ middleware: "auth" });

const { t } = useI18n();
const route = useRoute();
const localePath = useLocalePath();
const api = useApi();
const toast = useToast();
const { localised } = useLocaleText();

const bookId = computed(() => route.params.id as string);

const { data: itemRaw, pending } = await useAsyncData(
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
const notFound = computed(() => !pending.value && item.value === null);

const title = computed(() =>
  item.value ? localised(item.value.book.title, item.value.book.slug) : t("library.reader.title"),
);

useSiteSeo({ title: title.value, noindex: true });

const ClientReader = defineAsyncComponent(() => import("~/components/book/BookReader.vue"));

const downloading = ref(false);

async function downloadBook() {
  if (!item.value || downloading.value) return;
  downloading.value = true;
  try {
    const resp = await api<{ url: string }>(`/libraries/me/${item.value.book.id}/download`);
    if (import.meta.client) window.open(resp.url, "_blank", "noopener,noreferrer");
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("library.reader.download_failed")));
  }
  finally {
    downloading.value = false;
  }
}
</script>

<template>
  <AccountShell>
    <section class="space-y-4">
      <header class="flex items-start justify-between gap-3 flex-wrap">
        <div class="min-w-0 flex items-center gap-3">
          <BookCover
            v-if="item"
            :src="item.book.cover_url"
            :alt="title"
            class="w-10 shrink-0 hidden sm:block"
          />
          <div class="min-w-0">
            <nav class="text-xs text-ink-tertiary mb-1 flex items-center gap-1.5">
              <NuxtLink :to="localePath('/account/library')" class="hover:text-primary">
                {{ t("library.title") }}
              </NuxtLink>
              <Icon name="chevron-down" class="h-3 w-3 -rotate-90 shrink-0" />
              <span class="truncate">{{ title }}</span>
            </nav>
            <h1 class="font-serif text-xl md:text-2xl text-ink leading-tight truncate">
              {{ title }}
            </h1>
            <p v-if="item" class="text-xs text-ink-secondary mt-0.5 truncate">
              {{ item.book.author.display_name }}
            </p>
            <UiSkeleton v-else-if="pending" width="10rem" height="0.9rem" class="mt-1" />
          </div>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <UiButton
            v-if="item?.book.downloads_enabled"
            variant="ghost"
            size="sm"
            :loading="downloading"
            :disabled="downloading"
            @click="downloadBook"
          >
            <Icon name="upload" class="h-3.5 w-3.5 rotate-180" />
            <span class="hidden sm:inline">{{ t("library.reader.download") }}</span>
          </UiButton>
          <UiButton variant="ghost" size="sm" :to="localePath('/account/library')">
            <Icon name="arrow-left" class="h-3.5 w-3.5" />
            <span class="hidden sm:inline">{{ t("library.reader.back") }}</span>
          </UiButton>
        </div>
      </header>

      <p v-if="item && !item.book.downloads_enabled" class="text-xs text-ink-tertiary inline-flex items-center gap-1.5">
        <Icon name="lock" class="h-3.5 w-3.5" />
        {{ t("library.reader.download_disabled") }}
      </p>

      <!-- Loading skeleton (before we even know whether this book is in the library) -->
      <div v-if="pending" class="rounded-md border border-border bg-bg-secondary/40 p-4 space-y-3">
        <UiSkeleton height="2.5rem" block />
        <UiSkeleton height="70vh" block />
      </div>

      <!-- Not in this user's library (wrong id, or never purchased) -->
      <UiEmptyState
        v-else-if="notFound"
        icon="library"
        :title="t('library.reader.not_found_title')"
        :description="t('library.reader.not_found_body')"
      >
        <UiButton :to="localePath('/account/library')">
          <Icon name="library" class="h-4 w-4" />
          {{ t("library.reader.back") }}
        </UiButton>
      </UiEmptyState>

      <ClientOnly v-else>
        <ClientReader
          v-if="item"
          :book-id="item.book.id"
          :title="title"
          :downloads-enabled="item.book.downloads_enabled"
          @download="downloadBook"
        />
        <template #fallback>
          <div class="rounded-md border border-border bg-bg-secondary/40 p-4 space-y-3">
            <UiSkeleton height="2.5rem" block />
            <UiSkeleton height="70vh" block />
          </div>
        </template>
      </ClientOnly>

      <p v-if="item" class="text-[11px] text-ink-tertiary leading-relaxed flex items-start gap-1.5">
        <Icon name="lock" class="h-3 w-3 shrink-0 mt-0.5" />
        {{ t("library.reader.legal_notice") }}
      </p>
    </section>
  </AccountShell>
</template>
