<script setup lang="ts">
import type { AuthorPublic, BookOwnerList } from "~/types/api";
import { formatPrice } from "~/composables/useLocaleText";
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({ middleware: "auth" });

// AuthorPrivate isn't yet exported from types/api.ts — we shape it inline.
interface AuthorPrivate extends AuthorPublic {
  commission_rate: number;
  total_revenue: number;
  available_balance: number;
  pending_balance: number;
}

const { t } = useI18n();
const localePath = useLocalePath();
const { localised } = useLocaleText();
const { formatDate } = useFormatDate();
const { user, refresh: refreshAuth } = useAuth();
const api = useApi();
const toast = useToast();

useSiteSeo({ title: t("author_cabinet.title"), noindex: true });

// ---- Load author profile (may not exist) ----
const profile = ref<AuthorPrivate | null>(null);
const noProfile = ref(false);
const loadError = ref<string | null>(null);

async function loadProfile() {
  try {
    profile.value = await api<AuthorPrivate>("/authors/me");
    noProfile.value = false;
  }
  catch (err: unknown) {
    const code = (err as { data?: { error?: { details?: { code?: string } } } })
      ?.data?.error?.details?.code;
    const status = (err as { statusCode?: number; status?: number }).statusCode
      ?? (err as { status?: number }).status;
    if (code === "author_profile_missing" || status === 404) {
      noProfile.value = true;
      profile.value = null;
    }
    else {
      loadError.value = apiErrorMessage(err, t("common.error"));
    }
  }
}

await loadProfile();

// ---- Author's books (only when profile exists) ----
const { data: booksRaw, refresh: refreshBooks } = await useAsyncData(
  "author:me:books",
  () =>
    noProfile.value
      ? Promise.resolve({ items: [], total: 0, page: 1, page_size: 0 } as BookOwnerList)
      : api<BookOwnerList>("/books/me", { query: { page: 1, page_size: 8 } }),
  { server: false },
);

const myBooks = computed(() => (booksRaw.value as BookOwnerList | null)?.items ?? []);
const totalBooks = computed(() => (booksRaw.value as BookOwnerList | null)?.total ?? 0);

const approvedBooks = computed(() => myBooks.value.filter((b) => b.status === "approved"));
const draftBooks = computed(() => myBooks.value.filter((b) => b.status === "draft"));
const pendingBooks = computed(() => myBooks.value.filter((b) => b.status === "pending"));

// ---- Become-author form ----
const becomeForm = reactive({
  display_name: user.value?.full_name ?? "",
  bio_uz: "",
  bio_ru: "",
  bio_en: "",
  academic_title: "",
  institution: "",
  website: "",
});
const becomeSubmitting = ref(false);
const becomeError = ref<string | null>(null);

async function submitBecome() {
  if (becomeSubmitting.value) return;
  if (!becomeForm.display_name.trim()) {
    becomeError.value = t("author_cabinet.become.error_name_required");
    return;
  }
  becomeSubmitting.value = true;
  becomeError.value = null;
  try {
    const bio: Record<string, string> = {};
    if (becomeForm.bio_uz.trim()) bio.uz = becomeForm.bio_uz.trim();
    if (becomeForm.bio_ru.trim()) bio.ru = becomeForm.bio_ru.trim();
    if (becomeForm.bio_en.trim()) bio.en = becomeForm.bio_en.trim();

    await api("/authors/me", {
      method: "POST",
      body: {
        display_name: becomeForm.display_name.trim(),
        bio: Object.keys(bio).length ? bio : null,
        academic_title: becomeForm.academic_title.trim() || null,
        institution: becomeForm.institution.trim() || null,
        website: becomeForm.website.trim() || null,
      },
    });
    toast.success(t("author_cabinet.become.success"));
    await refreshAuth();
    await loadProfile();
    await refreshBooks();
  }
  catch (err) {
    becomeError.value = apiErrorMessage(err, t("common.error"));
  }
  finally {
    becomeSubmitting.value = false;
  }
}

// ---- Edit profile (collapsible) ----
const editing = ref(false);
const editForm = reactive({
  display_name: "",
  bio_uz: "",
  bio_ru: "",
  bio_en: "",
  academic_title: "",
  institution: "",
  website: "",
});
const editSubmitting = ref(false);
const editError = ref<string | null>(null);

function openEdit() {
  if (!profile.value) return;
  editForm.display_name = profile.value.display_name;
  editForm.bio_uz = (profile.value.bio?.uz as string) ?? "";
  editForm.bio_ru = (profile.value.bio?.ru as string) ?? "";
  editForm.bio_en = (profile.value.bio?.en as string) ?? "";
  editForm.academic_title = profile.value.academic_title ?? "";
  editForm.institution = profile.value.institution ?? "";
  editForm.website = profile.value.website ?? "";
  editError.value = null;
  editing.value = true;
}

async function submitEdit() {
  if (editSubmitting.value) return;
  editSubmitting.value = true;
  editError.value = null;
  try {
    const bio: Record<string, string> = {};
    if (editForm.bio_uz.trim()) bio.uz = editForm.bio_uz.trim();
    if (editForm.bio_ru.trim()) bio.ru = editForm.bio_ru.trim();
    if (editForm.bio_en.trim()) bio.en = editForm.bio_en.trim();

    profile.value = await api<AuthorPrivate>("/authors/me", {
      method: "PATCH",
      body: {
        display_name: editForm.display_name.trim() || null,
        bio: Object.keys(bio).length ? bio : null,
        academic_title: editForm.academic_title.trim() || null,
        institution: editForm.institution.trim() || null,
        website: editForm.website.trim() || null,
      },
    });
    toast.success(t("author_cabinet.edit_success"));
    editing.value = false;
  }
  catch (err) {
    editError.value = apiErrorMessage(err, t("common.error"));
  }
  finally {
    editSubmitting.value = false;
  }
}

const STATUS_TONE: Record<string, string> = {
  approved: "bg-success/10 text-success",
  pending: "bg-warning/10 text-warning",
  draft: "bg-bg-secondary text-ink-secondary",
  rejected: "bg-error/10 text-error",
};

const initials = computed(() => {
  const name = profile.value?.display_name ?? user.value?.full_name ?? "";
  return name.trim().split(/\s+/).slice(0, 2).map((p) => p.charAt(0).toUpperCase()).join("") || "?";
});

const joinedAt = computed(() => {
  if (!profile.value) return "";
  return formatDate(profile.value.created_at, { withTime: false });
});
</script>

<template>
  <AccountShell>
    <!-- BECOME AUTHOR -->
    <template v-if="noProfile">
      <header class="space-y-2 mb-8">
        <div class="flex items-center gap-3">
          <span class="h-10 w-10 rounded-md bg-primary/10 text-primary inline-flex items-center justify-center shrink-0">
            <Icon name="pencil" class="h-5 w-5" />
          </span>
          <div>
            <h1 class="font-serif text-2xl md:text-3xl text-ink leading-tight">
              {{ t("author_cabinet.become.title") }}
            </h1>
            <p class="text-sm text-ink-secondary">{{ t("author_cabinet.become.subtitle") }}</p>
          </div>
        </div>
      </header>

      <!-- Perks reminder -->
      <ul class="grid sm:grid-cols-3 gap-3 mb-8">
        <li class="rounded-md border border-border bg-bg-card p-4 space-y-1.5">
          <Icon name="currency" class="h-5 w-5 text-success" />
          <div class="font-medium text-ink text-sm">{{ t("author_cabinet.perks.earn_title") }}</div>
          <div class="text-xs text-ink-tertiary">{{ t("author_cabinet.perks.earn_body") }}</div>
        </li>
        <li class="rounded-md border border-border bg-bg-card p-4 space-y-1.5">
          <Icon name="users" class="h-5 w-5 text-primary" />
          <div class="font-medium text-ink text-sm">{{ t("author_cabinet.perks.reach_title") }}</div>
          <div class="text-xs text-ink-tertiary">{{ t("author_cabinet.perks.reach_body") }}</div>
        </li>
        <li class="rounded-md border border-border bg-bg-card p-4 space-y-1.5">
          <Icon name="chart" class="h-5 w-5 text-info" />
          <div class="font-medium text-ink text-sm">{{ t("author_cabinet.perks.insights_title") }}</div>
          <div class="text-xs text-ink-tertiary">{{ t("author_cabinet.perks.insights_body") }}</div>
        </li>
      </ul>

      <form
        class="rounded-md border border-border bg-bg-card p-5 md:p-6 space-y-5"
        novalidate
        @submit.prevent="submitBecome"
      >
        <div class="space-y-1">
          <h2 class="font-serif text-xl text-ink">{{ t("author_cabinet.become.form_title") }}</h2>
          <p class="text-sm text-ink-secondary">{{ t("author_cabinet.become.form_hint") }}</p>
        </div>

        <UiInput
          v-model="becomeForm.display_name"
          :label="t('author_cabinet.fields.display_name')"
          :hint="t('author_cabinet.fields.display_name_hint')"
          required
        />

        <div class="grid sm:grid-cols-2 gap-3">
          <UiInput
            v-model="becomeForm.academic_title"
            :label="t('author_cabinet.fields.academic_title')"
            :placeholder="t('author_cabinet.fields.academic_title_placeholder')"
          />
          <UiInput
            v-model="becomeForm.institution"
            :label="t('author_cabinet.fields.institution')"
            :placeholder="t('author_cabinet.fields.institution_placeholder')"
          />
        </div>

        <UiInput
          v-model="becomeForm.website"
          :label="t('author_cabinet.fields.website')"
          placeholder="https://"
        />

        <div>
          <span class="block text-sm text-ink-secondary mb-2">
            {{ t("author_cabinet.fields.bio") }}
          </span>
          <div class="grid sm:grid-cols-3 gap-3">
            <label class="block">
              <span class="block text-xs text-ink-tertiary mb-1">O'zbekcha</span>
              <textarea
                v-model="becomeForm.bio_uz"
                rows="4"
                class="w-full px-3 py-2 rounded border border-border bg-bg text-sm text-ink focus:outline-none focus:border-primary"
              />
            </label>
            <label class="block">
              <span class="block text-xs text-ink-tertiary mb-1">Русский</span>
              <textarea
                v-model="becomeForm.bio_ru"
                rows="4"
                class="w-full px-3 py-2 rounded border border-border bg-bg text-sm text-ink focus:outline-none focus:border-primary"
              />
            </label>
            <label class="block">
              <span class="block text-xs text-ink-tertiary mb-1">English</span>
              <textarea
                v-model="becomeForm.bio_en"
                rows="4"
                class="w-full px-3 py-2 rounded border border-border bg-bg text-sm text-ink focus:outline-none focus:border-primary"
              />
            </label>
          </div>
        </div>

        <p v-if="becomeError" class="flex items-center gap-2 text-sm text-error">
          <Icon name="warning-solid" class="h-4 w-4" />
          {{ becomeError }}
        </p>

        <div class="flex items-center justify-end">
          <UiButton type="submit" :loading="becomeSubmitting" :disabled="becomeSubmitting">
            <Icon name="check" class="h-4 w-4" />
            {{ t("author_cabinet.become.submit") }}
          </UiButton>
        </div>
      </form>
    </template>

    <!-- AUTHOR DASHBOARD -->
    <template v-else-if="profile">
      <!-- Header -->
      <header class="space-y-3 mb-8">
        <div class="flex items-start gap-4">
          <span class="h-14 w-14 rounded-full bg-primary text-ink-inverse flex items-center justify-center text-lg font-semibold shrink-0 shadow-md">
            {{ initials }}
          </span>
          <div class="flex-1 min-w-0">
            <h1 class="font-serif text-2xl md:text-3xl text-ink leading-tight">
              {{ profile.display_name }}
            </h1>
            <p v-if="profile.academic_title" class="text-sm text-ink-secondary mt-0.5">
              {{ profile.academic_title }}
            </p>
            <p v-if="profile.institution" class="inline-flex items-center gap-1 text-xs text-ink-tertiary mt-1">
              <Icon name="institution" class="h-3 w-3" />
              {{ profile.institution }}
            </p>
          </div>
          <div class="flex gap-2 shrink-0">
            <UiButton
              variant="ghost"
              size="sm"
              :to="localePath(`/authors/${profile.slug}`)"
            >
              <Icon name="external" class="h-4 w-4" />
              {{ t("author_cabinet.view_public") }}
            </UiButton>
            <UiButton size="sm" @click="openEdit">
              <Icon name="pencil" class="h-4 w-4" />
              {{ t("author_cabinet.edit_profile") }}
            </UiButton>
          </div>
        </div>
      </header>

      <!-- Stat tiles -->
      <section class="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-8">
        <NuxtLink
          :to="localePath('/account/balance')"
          class="group rounded-md border border-border bg-bg-card p-4 hover:border-primary hover:shadow-sm transition-all"
        >
          <div class="flex items-center justify-between mb-3">
            <span class="h-9 w-9 rounded-md flex items-center justify-center bg-success/10 text-success">
              <Icon name="currency" class="h-4 w-4" />
            </span>
            <Icon name="arrow-right" class="h-4 w-4 text-ink-tertiary opacity-0 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all" />
          </div>
          <div class="font-serif text-xl text-success tabular-nums">
            {{ formatPrice(profile.available_balance) }}
          </div>
          <div class="text-xs uppercase tracking-wider text-ink-tertiary mt-1">
            {{ t("author_cabinet.stat_available") }}
          </div>
        </NuxtLink>

        <div class="rounded-md border border-border bg-bg-card p-4">
          <div class="flex items-center mb-3">
            <span class="h-9 w-9 rounded-md flex items-center justify-center bg-warning/10 text-warning">
              <Icon name="arrow-path" class="h-4 w-4" />
            </span>
          </div>
          <div class="font-serif text-xl text-warning tabular-nums">
            {{ formatPrice(profile.pending_balance) }}
          </div>
          <div class="text-xs uppercase tracking-wider text-ink-tertiary mt-1">
            {{ t("author_cabinet.stat_pending") }}
          </div>
        </div>

        <div class="rounded-md border border-border bg-bg-card p-4">
          <div class="flex items-center mb-3">
            <span class="h-9 w-9 rounded-md flex items-center justify-center bg-info/10 text-info">
              <Icon name="chart" class="h-4 w-4" />
            </span>
          </div>
          <div class="font-serif text-xl text-ink tabular-nums">
            {{ formatPrice(profile.total_revenue) }}
          </div>
          <div class="text-xs uppercase tracking-wider text-ink-tertiary mt-1">
            {{ t("author_cabinet.stat_total_revenue") }}
          </div>
        </div>

        <div class="rounded-md border border-border bg-bg-card p-4">
          <div class="flex items-center mb-3">
            <span class="h-9 w-9 rounded-md flex items-center justify-center bg-primary/10 text-primary">
              <Icon name="book" class="h-4 w-4" />
            </span>
          </div>
          <div class="font-serif text-xl text-ink tabular-nums">
            {{ totalBooks }}
          </div>
          <div class="text-xs uppercase tracking-wider text-ink-tertiary mt-1">
            {{ t("author_cabinet.stat_books") }}
          </div>
        </div>
      </section>

      <!-- Edit form (inline expandable) -->
      <section
        v-if="editing"
        class="rounded-md border border-primary/40 bg-bg-card p-5 md:p-6 mb-8 space-y-5"
      >
        <div class="space-y-1">
          <h2 class="font-serif text-xl text-ink">{{ t("author_cabinet.edit_title") }}</h2>
          <p class="text-sm text-ink-secondary">{{ t("author_cabinet.edit_subtitle") }}</p>
        </div>

        <form class="space-y-5" novalidate @submit.prevent="submitEdit">
          <UiInput
            v-model="editForm.display_name"
            :label="t('author_cabinet.fields.display_name')"
            required
          />

          <div class="grid sm:grid-cols-2 gap-3">
            <UiInput
              v-model="editForm.academic_title"
              :label="t('author_cabinet.fields.academic_title')"
            />
            <UiInput
              v-model="editForm.institution"
              :label="t('author_cabinet.fields.institution')"
            />
          </div>

          <UiInput
            v-model="editForm.website"
            :label="t('author_cabinet.fields.website')"
            placeholder="https://"
          />

          <div>
            <span class="block text-sm text-ink-secondary mb-2">
              {{ t("author_cabinet.fields.bio") }}
            </span>
            <div class="grid sm:grid-cols-3 gap-3">
              <label class="block">
                <span class="block text-xs text-ink-tertiary mb-1">O'zbekcha</span>
                <textarea
                  v-model="editForm.bio_uz"
                  rows="4"
                  class="w-full px-3 py-2 rounded border border-border bg-bg text-sm focus:outline-none focus:border-primary"
                />
              </label>
              <label class="block">
                <span class="block text-xs text-ink-tertiary mb-1">Русский</span>
                <textarea
                  v-model="editForm.bio_ru"
                  rows="4"
                  class="w-full px-3 py-2 rounded border border-border bg-bg text-sm focus:outline-none focus:border-primary"
                />
              </label>
              <label class="block">
                <span class="block text-xs text-ink-tertiary mb-1">English</span>
                <textarea
                  v-model="editForm.bio_en"
                  rows="4"
                  class="w-full px-3 py-2 rounded border border-border bg-bg text-sm focus:outline-none focus:border-primary"
                />
              </label>
            </div>
          </div>

          <p v-if="editError" class="flex items-center gap-2 text-sm text-error">
            <Icon name="warning-solid" class="h-4 w-4" />
            {{ editError }}
          </p>

          <div class="flex items-center justify-end gap-2">
            <UiButton variant="ghost" type="button" :disabled="editSubmitting" @click="editing = false">
              {{ t("common.cancel") }}
            </UiButton>
            <UiButton type="submit" :loading="editSubmitting" :disabled="editSubmitting">
              <Icon name="check" class="h-4 w-4" />
              {{ t("author_cabinet.save") }}
            </UiButton>
          </div>
        </form>
      </section>

      <!-- My books -->
      <section class="space-y-4 mb-8">
        <div class="flex items-end justify-between gap-3 flex-wrap">
          <div>
            <h2 class="font-serif text-2xl text-ink leading-tight">
              {{ t("author_cabinet.my_books") }}
            </h2>
            <p class="text-sm text-ink-secondary mt-1">
              <span class="tabular-nums">{{ approvedBooks.length }}</span> {{ t("author_cabinet.published") }}
              <template v-if="pendingBooks.length">
                · <span class="tabular-nums">{{ pendingBooks.length }}</span> {{ t("author_cabinet.in_review") }}
              </template>
              <template v-if="draftBooks.length">
                · <span class="tabular-nums">{{ draftBooks.length }}</span> {{ t("author_cabinet.drafts") }}
              </template>
            </p>
          </div>
          <div class="flex items-center gap-2">
            <UiButton variant="ghost" :to="localePath('/account/books')">
              <Icon name="book" class="h-4 w-4" />
              {{ t("account_books.nav_label") }}
            </UiButton>
            <UiButton :to="localePath('/account/books/new')">
              <Icon name="plus" class="h-4 w-4" />
              {{ t("account_books.new_button") }}
            </UiButton>
          </div>
        </div>

        <ul v-if="myBooks.length > 0" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          <li
            v-for="book in myBooks"
            :key="book.id"
            class="rounded-md border border-border bg-bg-card overflow-hidden flex flex-col hover:border-primary transition-colors"
          >
            <NuxtLink :to="localePath(`/books/${book.slug}`)">
              <BookCover :src="book.cover_url" :alt="localised(book.title, book.slug)" />
            </NuxtLink>
            <div class="p-3 space-y-2 flex-1 flex flex-col">
              <NuxtLink
                :to="localePath(`/books/${book.slug}`)"
                class="font-serif text-sm text-ink leading-snug line-clamp-2 hover:text-primary transition-colors"
              >
                {{ localised(book.title, book.slug) }}
              </NuxtLink>
              <span
                class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-medium self-start"
                :class="STATUS_TONE[book.status] ?? STATUS_TONE.draft"
              >
                {{ t(`author_cabinet.status.${book.status}`) }}
              </span>
              <div class="text-[11px] text-ink-tertiary mt-auto">
                {{ formatPrice(book.price) }}
              </div>
            </div>
          </li>
        </ul>

        <UiEmptyState
          v-else
          icon="book"
          :title="t('author_cabinet.no_books_title')"
          :description="t('author_cabinet.no_books_body')"
        />
      </section>

      <!-- Footer meta -->
      <p class="text-xs text-ink-tertiary text-center pt-4 border-t border-border">
        {{ t("author_cabinet.joined", { date: joinedAt }) }} ·
        {{ t("author_cabinet.commission", { rate: profile.commission_rate }) }}
      </p>
    </template>

    <!-- LOAD ERROR -->
    <template v-else-if="loadError">
      <div class="rounded-md border border-error/30 bg-error/5 p-6 flex items-start gap-4">
        <Icon name="warning-solid" class="h-6 w-6 text-error shrink-0" />
        <div>
          <h2 class="font-serif text-lg text-ink mb-1">{{ t("author_cabinet.error_title") }}</h2>
          <p class="text-sm text-ink-secondary">{{ loadError }}</p>
        </div>
      </div>
    </template>
  </AccountShell>
</template>
