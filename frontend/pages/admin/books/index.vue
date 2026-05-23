<script setup lang="ts">
import type { BookList, BookPublic } from "~/types/api";
import { formatPrice } from "~/composables/useLocaleText";
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin"],
});

const { t } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const router = useRouter();
const { localised } = useLocaleText();
const api = useApi();

useHead({ title: t("admin.books.title") });

const PAGE_SIZE = 20;
const currentPage = computed(() => Math.max(1, Number(route.query.page) || 1));

const { data: queueRaw, pending, refresh } = await useAsyncData(
  "admin:books:pending",
  () =>
    api<BookList>("/books/admin/moderation", {
      query: { page: currentPage.value, page_size: PAGE_SIZE },
    }),
  { watch: [currentPage] },
);

const queue = computed(() => queueRaw.value as BookList | null);

function changePage(page: number) {
  router.push({ query: { ...route.query, page } });
  if (import.meta.client) window.scrollTo({ top: 0, behavior: "smooth" });
}

// --- Approve ---------------------------------------------------------------
const approving = ref<Set<string>>(new Set());

async function approveBook(book: BookPublic) {
  if (!confirm(t("admin.books.approve_confirm"))) return;
  if (approving.value.has(book.id)) return;
  approving.value.add(book.id);
  try {
    await api(`/books/admin/${book.id}/approve`, { method: "POST" });
    await refresh();
  }
  catch {
    // surfaced via global toast in Phase 5.9
  }
  finally {
    approving.value.delete(book.id);
  }
}

// --- Reject (modal) --------------------------------------------------------
const rejectTarget = ref<BookPublic | null>(null);
const rejectReason = ref("");
const rejectSubmitting = ref(false);
const rejectError = ref<string | null>(null);

function openReject(book: BookPublic) {
  rejectTarget.value = book;
  rejectReason.value = "";
  rejectError.value = null;
}

function closeReject() {
  rejectTarget.value = null;
  rejectReason.value = "";
  rejectError.value = null;
}

useEscape(() => closeReject(), {
  enabled: computed(() => rejectTarget.value !== null),
});

async function submitReject() {
  if (!rejectTarget.value || rejectSubmitting.value) return;
  const reason = rejectReason.value.trim();
  if (!reason) {
    rejectError.value = t("admin.books.reject_reason_required");
    return;
  }
  rejectSubmitting.value = true;
  rejectError.value = null;
  try {
    await api(`/books/admin/${rejectTarget.value.id}/reject`, {
      method: "POST",
      body: { reason },
    });
    closeReject();
    await refresh();
  }
  catch (err) {
    rejectError.value = apiErrorMessage(err, t("common.error"));
  }
  finally {
    rejectSubmitting.value = false;
  }
}

const breadcrumbs = computed(() => [
  { label: t("admin.title"), to: localePath("/admin") },
  { label: t("admin.books.title") },
]);
</script>

<template>
  <section class="space-y-6">
    <UiBreadcrumbs :items="breadcrumbs" />

    <header class="space-y-1">
      <h1 class="font-serif text-2xl text-ink">{{ t("admin.books.title") }}</h1>
      <p class="text-sm text-ink-secondary">{{ t("admin.books.subtitle") }}</p>
    </header>

    <div v-if="pending && !queue" class="space-y-3">
      <UiSkeleton v-for="i in 3" :key="i" :height="'10rem'" :block="true" />
    </div>

    <UiEmptyState
      v-else-if="(queue?.items.length ?? 0) === 0"
      icon="📥"
      :title="t('admin.books.empty_title')"
      :description="t('admin.books.empty_body')"
    />

    <ul v-else class="space-y-4">
      <li
        v-for="book in queue!.items"
        :key="book.id"
        class="rounded border border-border bg-bg-card p-4 grid sm:grid-cols-[120px_1fr] gap-4"
      >
        <div class="w-[120px]">
          <BookCover :src="book.cover_url" :alt="localised(book.title, book.slug)" />
        </div>

        <div class="space-y-3 min-w-0">
          <div class="flex items-start justify-between gap-3 flex-wrap">
            <div class="min-w-0">
              <h2 class="font-serif text-lg text-ink leading-snug">
                {{ localised(book.title, book.slug) }}
              </h2>
              <p class="text-sm text-ink-secondary truncate">
                {{ book.author.display_name }}
              </p>
            </div>
            <BookPriceTag
              :price="book.price"
              :discount-price="book.discount_price"
              :is-free="book.is_free"
              size="sm"
            />
          </div>

          <div class="flex flex-wrap gap-1.5">
            <NuxtLink
              v-for="cat in book.categories"
              :key="cat.id"
              :to="localePath(`/category/${cat.slug}`)"
              class="inline-flex"
            >
              <UiBadge tone="neutral" size="sm">
                {{ localised(cat.name, cat.slug) }}
              </UiBadge>
            </NuxtLink>
          </div>

          <dl class="grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-1 text-xs">
            <div>
              <dt class="text-ink-tertiary">{{ t("admin.books.language_label") }}</dt>
              <dd class="text-ink">{{ book.language }}</dd>
            </div>
            <div v-if="book.publication_year">
              <dt class="text-ink-tertiary">{{ t("admin.books.publication_year_label") }}</dt>
              <dd class="text-ink">{{ book.publication_year }}</dd>
            </div>
            <div v-if="book.publisher">
              <dt class="text-ink-tertiary">{{ t("admin.books.publisher_label") }}</dt>
              <dd class="text-ink truncate">{{ book.publisher }}</dd>
            </div>
            <div>
              <dt class="text-ink-tertiary">{{ t("admin.books.price_label") }}</dt>
              <dd class="text-ink">{{ formatPrice(book.price) }}</dd>
            </div>
          </dl>

          <p v-if="localised(book.description)" class="text-sm text-ink-secondary line-clamp-3">
            {{ localised(book.description) }}
          </p>

          <div class="flex flex-wrap items-center gap-2 pt-1">
            <a
              v-if="book.demo_url"
              :href="book.demo_url"
              target="_blank"
              rel="noopener noreferrer"
              class="text-xs text-primary hover:underline"
            >
              {{ t("admin.books.view_preview") }} ↗
            </a>
            <span v-else class="text-xs text-ink-tertiary">
              {{ t("admin.books.no_demo") }}
            </span>

            <span class="flex-1" />

            <UiButton
              size="sm"
              variant="ghost"
              :disabled="rejectSubmitting"
              @click="openReject(book)"
            >
              {{ t("admin.books.reject") }}
            </UiButton>
            <UiButton
              size="sm"
              :loading="approving.has(book.id)"
              :disabled="approving.has(book.id)"
              @click="approveBook(book)"
            >
              ✓ {{ t("admin.books.approve") }}
            </UiButton>
          </div>
        </div>
      </li>
    </ul>

    <div class="pt-4">
      <UiPagination
        :page="currentPage"
        :page-size="PAGE_SIZE"
        :total="queue?.total ?? 0"
        @change="changePage"
      />
    </div>

    <!-- Reject modal -->
    <Teleport v-if="rejectTarget" to="body">
      <div
        class="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4"
        role="dialog"
        aria-modal="true"
        @click.self="closeReject"
      >
        <div class="w-full max-w-md rounded bg-bg-card border border-border shadow-xl p-5 space-y-4">
          <header class="space-y-1">
            <h3 class="font-serif text-lg text-ink">
              {{ t("admin.books.reject_modal_title") }}
            </h3>
            <p class="text-sm text-ink-secondary truncate">
              {{ localised(rejectTarget.title, rejectTarget.slug) }}
            </p>
          </header>

          <label class="block">
            <span class="block text-sm text-ink-secondary mb-1">
              {{ t("admin.books.reject_reason") }}
              <span class="text-error">*</span>
            </span>
            <textarea
              v-model="rejectReason"
              rows="4"
              maxlength="2000"
              :placeholder="t('admin.books.reject_reason_placeholder')"
              class="w-full px-3 py-2 rounded border border-border bg-bg text-ink placeholder:text-ink-tertiary focus:outline-none focus:border-primary text-sm"
            />
          </label>

          <p v-if="rejectError" class="text-sm text-error">{{ rejectError }}</p>

          <div class="flex justify-end gap-2 pt-1">
            <UiButton
              variant="ghost"
              :disabled="rejectSubmitting"
              @click="closeReject"
            >
              {{ t("admin.books.reject_cancel") }}
            </UiButton>
            <UiButton
              variant="danger"
              :loading="rejectSubmitting"
              :disabled="rejectSubmitting"
              @click="submitReject"
            >
              {{ t("admin.books.reject_submit") }}
            </UiButton>
          </div>
        </div>
      </div>
    </Teleport>
  </section>
</template>
