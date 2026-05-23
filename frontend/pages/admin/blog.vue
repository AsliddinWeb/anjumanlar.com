<script setup lang="ts">
import type { BlogPostAdminList, BlogPostAdminView, BlogPostStatus } from "~/types/api";
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin"],
});

const { t, locale } = useI18n();
const localePath = useLocalePath();
const { localised } = useLocaleText();
const route = useRoute();
const router = useRouter();
const api = useApi();

useHead({ title: t("admin.blog.title") });

const PAGE_SIZE = 20;
const currentPage = computed(() => Math.max(1, Number(route.query.page) || 1));
const statusFilter = computed(() => (route.query.status as string) || "");

const queryParams = computed(() => {
  const p: Record<string, string | number> = {
    page: currentPage.value,
    page_size: PAGE_SIZE,
  };
  if (statusFilter.value) p.status = statusFilter.value;
  return p;
});

const { data: listRaw, pending, refresh } = await useAsyncData(
  "admin:blog",
  () => api<BlogPostAdminList>("/admin/blog", { query: queryParams.value }),
  { watch: [queryParams] },
);

const list = computed(() => listRaw.value as BlogPostAdminList | null);

function setQuery(updates: Record<string, string | number | undefined>) {
  const next: Record<string, string> = {};
  for (const [k, v] of Object.entries(route.query)) {
    if (typeof v === "string") next[k] = v;
  }
  for (const [k, v] of Object.entries(updates)) {
    if (v === undefined || v === null || v === "") delete next[k];
    else next[k] = String(v);
  }
  if (!("page" in updates)) delete next.page;
  router.push({ query: next });
}

function changePage(page: number) {
  setQuery({ page });
  if (import.meta.client) window.scrollTo({ top: 0, behavior: "smooth" });
}

const formatDate = (iso: string | null) => {
  if (!iso) return "—";
  return new Intl.DateTimeFormat(locale.value, {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(iso));
};

function statusTone(s: BlogPostStatus) {
  return ({ draft: "neutral", published: "success", archived: "neutral" } as const)[s];
}

// ---- Modal -----
type FormMode = "create" | "edit";
const modalOpen = ref(false);
const modalMode = ref<FormMode>("create");
const editingId = ref<string | null>(null);

const form = reactive({
  slug: "",
  title_uz: "",
  title_ru: "",
  title_en: "",
  excerpt_uz: "",
  excerpt_ru: "",
  excerpt_en: "",
  body_uz: "",
  body_ru: "",
  body_en: "",
  cover_url: "",
});

const submitting = ref(false);
const formError = ref<string | null>(null);

function resetForm() {
  Object.assign(form, {
    slug: "",
    title_uz: "",
    title_ru: "",
    title_en: "",
    excerpt_uz: "",
    excerpt_ru: "",
    excerpt_en: "",
    body_uz: "",
    body_ru: "",
    body_en: "",
    cover_url: "",
  });
  formError.value = null;
  editingId.value = null;
}

function openCreate() {
  resetForm();
  modalMode.value = "create";
  modalOpen.value = true;
}

function openEdit(p: BlogPostAdminView) {
  resetForm();
  modalMode.value = "edit";
  editingId.value = p.id;
  form.slug = p.slug;
  form.title_uz = (p.title?.uz as string) ?? "";
  form.title_ru = (p.title?.ru as string) ?? "";
  form.title_en = (p.title?.en as string) ?? "";
  form.excerpt_uz = (p.excerpt?.uz as string) ?? "";
  form.excerpt_ru = (p.excerpt?.ru as string) ?? "";
  form.excerpt_en = (p.excerpt?.en as string) ?? "";
  form.body_uz = (p.body?.uz as string) ?? "";
  form.body_ru = (p.body?.ru as string) ?? "";
  form.body_en = (p.body?.en as string) ?? "";
  form.cover_url = p.cover_url ?? "";
  modalOpen.value = true;
}

function closeModal() {
  if (submitting.value) return;
  modalOpen.value = false;
  resetForm();
}

function _collect(prefix: "title" | "excerpt" | "body"): Record<string, string> {
  const out: Record<string, string> = {};
  for (const k of ["uz", "ru", "en"] as const) {
    const v = (form as Record<string, string>)[`${prefix}_${k}`].trim();
    if (v) out[k] = v;
  }
  return out;
}

async function submitForm() {
  if (submitting.value) return;
  if (!form.slug.trim()) {
    formError.value = t("admin.blog.form.slug_required");
    return;
  }
  const title = _collect("title");
  if (Object.keys(title).length === 0) {
    formError.value = t("admin.blog.form.title_required");
    return;
  }
  const payload: Record<string, unknown> = {
    slug: form.slug.trim(),
    title,
    excerpt: _collect("excerpt"),
    body: _collect("body"),
    cover_url: form.cover_url.trim() || null,
  };

  submitting.value = true;
  formError.value = null;
  try {
    if (modalMode.value === "create") {
      await api("/admin/blog", { method: "POST", body: payload });
    }
    else if (editingId.value) {
      await api(`/admin/blog/${editingId.value}`, { method: "PATCH", body: payload });
    }
    modalOpen.value = false;
    resetForm();
    await refresh();
  }
  catch (err) {
    formError.value = apiErrorMessage(err, t("common.error"));
  }
  finally {
    submitting.value = false;
  }
}

// ---- Direct actions ----
const busy = ref<Set<string>>(new Set());

async function publishPost(p: BlogPostAdminView) {
  if (busy.value.has(p.id)) return;
  busy.value.add(p.id);
  try {
    await api(`/admin/blog/${p.id}/publish`, { method: "POST" });
    await refresh();
  }
  finally {
    busy.value.delete(p.id);
  }
}

async function unpublishPost(p: BlogPostAdminView) {
  if (busy.value.has(p.id)) return;
  busy.value.add(p.id);
  try {
    await api(`/admin/blog/${p.id}/unpublish`, { method: "POST" });
    await refresh();
  }
  finally {
    busy.value.delete(p.id);
  }
}

async function deletePost(p: BlogPostAdminView) {
  if (!confirm(t("admin.blog.actions.delete_confirm"))) return;
  if (busy.value.has(p.id)) return;
  busy.value.add(p.id);
  try {
    await api(`/admin/blog/${p.id}`, { method: "DELETE" });
    await refresh();
  }
  finally {
    busy.value.delete(p.id);
  }
}

const breadcrumbs = computed(() => [
  { label: t("admin.title"), to: localePath("/admin") },
  { label: t("admin.blog.title") },
]);

const statusOptions = [
  { value: "draft", labelKey: "admin.blog.statuses.draft" },
  { value: "published", labelKey: "admin.blog.statuses.published" },
  { value: "archived", labelKey: "admin.blog.statuses.archived" },
];
</script>

<template>
  <section class="space-y-6">
    <UiBreadcrumbs :items="breadcrumbs" />

    <header class="flex items-end justify-between gap-3 flex-wrap">
      <div>
        <h1 class="font-serif text-2xl text-ink">{{ t("admin.blog.title") }}</h1>
        <p class="text-sm text-ink-secondary">{{ t("admin.blog.subtitle") }}</p>
      </div>
      <UiButton @click="openCreate">+ {{ t("admin.blog.add_button") }}</UiButton>
    </header>

    <div class="flex flex-wrap items-end gap-3">
      <UiSelect
        :model-value="statusFilter"
        :label="t('admin.blog.filter_status')"
        :placeholder="t('admin.blog.filter_status_any')"
        :options="statusOptions.map((s) => ({ value: s.value, label: t(s.labelKey) }))"
        @update:model-value="(v) => setQuery({ status: v })"
      />
      <span class="text-sm text-ink-tertiary ml-auto">{{ list?.total ?? 0 }}</span>
    </div>

    <div v-if="pending && !list" class="space-y-2">
      <UiSkeleton v-for="i in 4" :key="i" :height="'3rem'" :block="true" />
    </div>

    <UiEmptyState
      v-else-if="(list?.items.length ?? 0) === 0"
      icon="📰"
      :title="t('admin.blog.empty_title')"
      :description="t('admin.blog.empty_body')"
    />

    <div v-else class="overflow-x-auto rounded border border-border">
      <table class="w-full text-sm">
        <thead class="bg-bg-secondary text-left text-xs text-ink-tertiary">
          <tr>
            <th class="px-3 py-2">{{ t("admin.blog.table.title_col") }}</th>
            <th class="px-3 py-2">{{ t("admin.blog.table.slug") }}</th>
            <th class="px-3 py-2">{{ t("admin.blog.table.status") }}</th>
            <th class="px-3 py-2">{{ t("admin.blog.table.published_at") }}</th>
            <th class="px-3 py-2 text-right">{{ t("admin.blog.table.actions") }}</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="p in list!.items"
            :key="p.id"
            class="border-t border-border hover:bg-bg-secondary/40"
          >
            <td class="px-3 py-2 text-ink">{{ localised(p.title, p.slug) }}</td>
            <td class="px-3 py-2 font-mono text-xs text-ink-secondary">{{ p.slug }}</td>
            <td class="px-3 py-2">
              <UiBadge :tone="statusTone(p.status)" size="sm">
                {{ t(`admin.blog.statuses.${p.status}`) }}
              </UiBadge>
            </td>
            <td class="px-3 py-2 text-xs text-ink-tertiary">
              {{ formatDate(p.published_at) }}
            </td>
            <td class="px-3 py-2 text-right">
              <div class="inline-flex gap-1.5">
                <UiButton
                  v-if="p.status !== 'published'"
                  size="sm"
                  :disabled="busy.has(p.id)"
                  @click="publishPost(p)"
                >
                  {{ t("admin.blog.actions.publish") }}
                </UiButton>
                <UiButton
                  v-else
                  size="sm"
                  variant="ghost"
                  :disabled="busy.has(p.id)"
                  @click="unpublishPost(p)"
                >
                  {{ t("admin.blog.actions.unpublish") }}
                </UiButton>
                <UiButton size="sm" variant="ghost" @click="openEdit(p)">
                  {{ t("admin.blog.actions.edit") }}
                </UiButton>
                <UiButton
                  size="sm"
                  variant="danger"
                  :disabled="busy.has(p.id)"
                  @click="deletePost(p)"
                >
                  {{ t("admin.blog.actions.delete") }}
                </UiButton>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="pt-4">
      <UiPagination
        :page="currentPage"
        :page-size="PAGE_SIZE"
        :total="list?.total ?? 0"
        @change="changePage"
      />
    </div>

    <!-- Create / Edit modal -->
    <Teleport v-if="modalOpen" to="body">
      <div
        class="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4 overflow-y-auto"
        role="dialog"
        aria-modal="true"
        @click.self="closeModal"
      >
        <div class="w-full max-w-2xl rounded bg-bg-card border border-border shadow-xl p-5 space-y-3 max-h-[90vh] overflow-y-auto">
          <header class="space-y-1">
            <h3 class="font-serif text-lg text-ink">
              {{
                modalMode === "create"
                  ? t("admin.blog.form.create_title")
                  : t("admin.blog.form.edit_title")
              }}
            </h3>
          </header>

          <UiInput
            v-model="form.slug"
            :label="t('admin.blog.form.slug')"
            :hint="t('admin.blog.form.slug_hint')"
            required
          />

          <div class="grid sm:grid-cols-3 gap-3">
            <UiInput v-model="form.title_uz" :label="t('admin.blog.form.title_uz')" />
            <UiInput v-model="form.title_ru" :label="t('admin.blog.form.title_ru')" />
            <UiInput v-model="form.title_en" :label="t('admin.blog.form.title_en')" />
          </div>

          <UiInput v-model="form.cover_url" :label="t('admin.blog.form.cover_url')" placeholder="https://" />

          <div class="grid sm:grid-cols-3 gap-3">
            <label class="block">
              <span class="block text-sm text-ink-secondary mb-1">
                {{ t("admin.blog.form.excerpt_uz") }}
              </span>
              <textarea
                v-model="form.excerpt_uz"
                rows="3"
                class="w-full px-3 py-2 rounded border border-border bg-bg text-ink text-sm focus:outline-none focus:border-primary"
              />
            </label>
            <label class="block">
              <span class="block text-sm text-ink-secondary mb-1">
                {{ t("admin.blog.form.excerpt_ru") }}
              </span>
              <textarea
                v-model="form.excerpt_ru"
                rows="3"
                class="w-full px-3 py-2 rounded border border-border bg-bg text-ink text-sm focus:outline-none focus:border-primary"
              />
            </label>
            <label class="block">
              <span class="block text-sm text-ink-secondary mb-1">
                {{ t("admin.blog.form.excerpt_en") }}
              </span>
              <textarea
                v-model="form.excerpt_en"
                rows="3"
                class="w-full px-3 py-2 rounded border border-border bg-bg text-ink text-sm focus:outline-none focus:border-primary"
              />
            </label>
          </div>

          <div class="grid sm:grid-cols-3 gap-3">
            <label class="block">
              <span class="block text-sm text-ink-secondary mb-1">
                {{ t("admin.blog.form.body_uz") }}
              </span>
              <textarea
                v-model="form.body_uz"
                rows="6"
                class="w-full px-3 py-2 rounded border border-border bg-bg text-ink text-sm focus:outline-none focus:border-primary"
              />
            </label>
            <label class="block">
              <span class="block text-sm text-ink-secondary mb-1">
                {{ t("admin.blog.form.body_ru") }}
              </span>
              <textarea
                v-model="form.body_ru"
                rows="6"
                class="w-full px-3 py-2 rounded border border-border bg-bg text-ink text-sm focus:outline-none focus:border-primary"
              />
            </label>
            <label class="block">
              <span class="block text-sm text-ink-secondary mb-1">
                {{ t("admin.blog.form.body_en") }}
              </span>
              <textarea
                v-model="form.body_en"
                rows="6"
                class="w-full px-3 py-2 rounded border border-border bg-bg text-ink text-sm focus:outline-none focus:border-primary"
              />
            </label>
          </div>

          <p v-if="formError" class="text-sm text-error">{{ formError }}</p>

          <div class="flex justify-end gap-2 pt-2">
            <UiButton variant="ghost" :disabled="submitting" @click="closeModal">
              {{ t("admin.blog.form.cancel") }}
            </UiButton>
            <UiButton :loading="submitting" :disabled="submitting" @click="submitForm">
              {{
                modalMode === "create"
                  ? t("admin.blog.form.submit_create")
                  : t("admin.blog.form.submit_edit")
              }}
            </UiButton>
          </div>
        </div>
      </div>
    </Teleport>
  </section>
</template>
