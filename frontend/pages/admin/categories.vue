<script setup lang="ts">
import type { CategoryList, CategoryPublic } from "~/types/api";
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin"],
});

const { t } = useI18n();
const localePath = useLocalePath();
const { localised } = useLocaleText();
const api = useApi();

useHead({ title: t("admin.categories.title") });

const { data: catRaw, refresh } = await useAsyncData(
  "admin:categories:list",
  () => api<CategoryList>("/categories", { query: { active_only: false } }),
);

const categories = computed<CategoryPublic[]>(
  () => ((catRaw.value as CategoryList | null)?.items ?? []) as CategoryPublic[],
);

const byId = computed(() => {
  const map = new Map<string, CategoryPublic>();
  for (const c of categories.value) map.set(c.id, c);
  return map;
});

function parentLabel(c: CategoryPublic): string {
  if (!c.parent_id) return "—";
  const p = byId.value.get(c.parent_id);
  return p ? localised(p.name, p.slug) : "?";
}

// ---- Modal state ---------------------------------------------------------

type FormMode = "create" | "edit";
const modalOpen = ref(false);
const modalMode = ref<FormMode>("create");
const editingId = ref<string | null>(null);

const form = reactive({
  slug: "",
  name_uz: "",
  name_ru: "",
  name_en: "",
  icon: "",
  parent_id: "",
  sort_order: 0,
  is_active: true,
});

const submitting = ref(false);
const formError = ref<string | null>(null);

function resetForm() {
  form.slug = "";
  form.name_uz = "";
  form.name_ru = "";
  form.name_en = "";
  form.icon = "";
  form.parent_id = "";
  form.sort_order = 0;
  form.is_active = true;
  formError.value = null;
  editingId.value = null;
}

function openCreate() {
  resetForm();
  modalMode.value = "create";
  modalOpen.value = true;
}

function openEdit(c: CategoryPublic) {
  resetForm();
  modalMode.value = "edit";
  editingId.value = c.id;
  form.slug = c.slug;
  form.name_uz = (c.name?.uz as string) ?? "";
  form.name_ru = (c.name?.ru as string) ?? "";
  form.name_en = (c.name?.en as string) ?? "";
  form.icon = c.icon ?? "";
  form.parent_id = c.parent_id ?? "";
  form.sort_order = c.sort_order;
  form.is_active = c.is_active;
  modalOpen.value = true;
}

function closeModal() {
  if (submitting.value) return;
  modalOpen.value = false;
  resetForm();
}

async function submit() {
  if (submitting.value) return;
  if (!form.slug.trim()) {
    formError.value = t("admin.categories.form.slug_required");
    return;
  }
  const name: Record<string, string> = {};
  if (form.name_uz.trim()) name.uz = form.name_uz.trim();
  if (form.name_ru.trim()) name.ru = form.name_ru.trim();
  if (form.name_en.trim()) name.en = form.name_en.trim();
  if (Object.keys(name).length === 0) {
    formError.value = t("admin.categories.form.name_required");
    return;
  }

  const payload: Record<string, unknown> = {
    slug: form.slug.trim(),
    name,
    icon: form.icon.trim() || null,
    parent_id: form.parent_id || null,
    sort_order: Number(form.sort_order) || 0,
    is_active: form.is_active,
  };

  submitting.value = true;
  formError.value = null;
  try {
    if (modalMode.value === "create") {
      await api("/categories", { method: "POST", body: payload });
    }
    else if (editingId.value) {
      await api(`/categories/${editingId.value}`, { method: "PATCH", body: payload });
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

// ---- Delete --------------------------------------------------------------
const deleting = ref<Set<string>>(new Set());

async function deleteCategory(c: CategoryPublic) {
  if (!confirm(t("admin.categories.delete_confirm"))) return;
  if (deleting.value.has(c.id)) return;
  deleting.value.add(c.id);
  try {
    await api(`/categories/${c.id}`, { method: "DELETE" });
    await refresh();
  }
  catch {
    // toast in 5.9
  }
  finally {
    deleting.value.delete(c.id);
  }
}

// Parent options exclude the category being edited (and its descendants —
// nice-to-have, kept flat for now to ship the page).
const parentOptions = computed(() => {
  const opts: { value: string; label: string }[] = [
    { value: "", label: t("admin.categories.form.parent_none") },
  ];
  for (const c of categories.value) {
    if (modalMode.value === "edit" && c.id === editingId.value) continue;
    if (c.parent_id) continue; // only top-level can act as parent for simplicity
    opts.push({ value: c.id, label: localised(c.name, c.slug) });
  }
  return opts;
});

const breadcrumbs = computed(() => [
  { label: t("admin.title"), to: localePath("/admin") },
  { label: t("admin.categories.title") },
]);
</script>

<template>
  <section class="space-y-6">
    <UiBreadcrumbs :items="breadcrumbs" />

    <header class="flex items-end justify-between gap-3 flex-wrap">
      <div>
        <h1 class="font-serif text-2xl text-ink">{{ t("admin.categories.title") }}</h1>
        <p class="text-sm text-ink-secondary">{{ t("admin.categories.subtitle") }}</p>
      </div>
      <UiButton @click="openCreate">+ {{ t("admin.categories.add_button") }}</UiButton>
    </header>

    <UiEmptyState
      v-if="categories.length === 0"
      icon="🗂"
      :title="t('admin.categories.empty_title')"
      :description="t('admin.categories.empty_body')"
    />

    <div v-else class="overflow-x-auto rounded border border-border">
      <table class="w-full text-sm">
        <thead class="bg-bg-secondary text-left text-xs text-ink-tertiary">
          <tr>
            <th class="px-3 py-2">{{ t("admin.categories.table.icon") }}</th>
            <th class="px-3 py-2">{{ t("admin.categories.table.name") }}</th>
            <th class="px-3 py-2">{{ t("admin.categories.table.slug") }}</th>
            <th class="px-3 py-2">{{ t("admin.categories.table.parent") }}</th>
            <th class="px-3 py-2">{{ t("admin.categories.table.sort") }}</th>
            <th class="px-3 py-2">{{ t("admin.categories.table.books") }}</th>
            <th class="px-3 py-2">{{ t("admin.categories.table.active") }}</th>
            <th class="px-3 py-2 text-right">{{ t("admin.categories.table.actions") }}</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="c in categories"
            :key="c.id"
            class="border-t border-border hover:bg-bg-secondary/40"
          >
            <td class="px-3 py-2 text-base">{{ c.icon ?? "—" }}</td>
            <td class="px-3 py-2 text-ink">{{ localised(c.name, c.slug) }}</td>
            <td class="px-3 py-2 font-mono text-xs text-ink-secondary">{{ c.slug }}</td>
            <td class="px-3 py-2 text-ink-secondary">{{ parentLabel(c) }}</td>
            <td class="px-3 py-2 text-ink-tertiary">{{ c.sort_order }}</td>
            <td class="px-3 py-2 text-ink-tertiary">{{ c.book_count }}</td>
            <td class="px-3 py-2">
              <UiBadge :tone="c.is_active ? 'success' : 'neutral'" size="sm">
                {{ c.is_active ? "✓" : "—" }}
              </UiBadge>
            </td>
            <td class="px-3 py-2 text-right">
              <div class="inline-flex gap-1.5">
                <UiButton size="sm" variant="ghost" @click="openEdit(c)">
                  {{ t("admin.categories.edit") }}
                </UiButton>
                <UiButton
                  size="sm"
                  variant="danger"
                  :disabled="deleting.has(c.id)"
                  @click="deleteCategory(c)"
                >
                  {{ t("admin.categories.delete") }}
                </UiButton>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create / Edit modal -->
    <Teleport v-if="modalOpen" to="body">
      <div
        class="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4"
        role="dialog"
        aria-modal="true"
        @click.self="closeModal"
      >
        <div class="w-full max-w-lg rounded bg-bg-card border border-border shadow-xl p-5 space-y-3 max-h-[90vh] overflow-y-auto">
          <header class="space-y-1">
            <h3 class="font-serif text-lg text-ink">
              {{
                modalMode === "create"
                  ? t("admin.categories.form.create_title")
                  : t("admin.categories.form.edit_title")
              }}
            </h3>
          </header>

          <UiInput
            v-model="form.slug"
            :label="t('admin.categories.form.slug')"
            :hint="t('admin.categories.form.slug_hint')"
            required
          />

          <div class="grid sm:grid-cols-3 gap-3">
            <UiInput v-model="form.name_uz" :label="t('admin.categories.form.name_uz')" />
            <UiInput v-model="form.name_ru" :label="t('admin.categories.form.name_ru')" />
            <UiInput v-model="form.name_en" :label="t('admin.categories.form.name_en')" />
          </div>

          <div class="grid sm:grid-cols-2 gap-3">
            <UiInput v-model="form.icon" :label="t('admin.categories.form.icon')" :placeholder="'📚'" />
            <UiSelect
              :model-value="form.parent_id"
              :label="t('admin.categories.form.parent')"
              :options="parentOptions"
              @update:model-value="(v) => (form.parent_id = v)"
            />
          </div>

          <div class="grid sm:grid-cols-2 gap-3 items-end">
            <UiInput
              v-model="form.sort_order"
              type="number"
              :label="t('admin.categories.form.sort_order')"
            />
            <label class="flex items-center gap-2 text-sm text-ink cursor-pointer pb-2">
              <input v-model="form.is_active" type="checkbox">
              {{ t("admin.categories.form.is_active") }}
            </label>
          </div>

          <p v-if="formError" class="text-sm text-error">{{ formError }}</p>

          <div class="flex justify-end gap-2 pt-2">
            <UiButton variant="ghost" :disabled="submitting" @click="closeModal">
              {{ t("admin.categories.form.cancel") }}
            </UiButton>
            <UiButton :loading="submitting" :disabled="submitting" @click="submit">
              {{
                submitting
                  ? t("admin.categories.form.submitting")
                  : modalMode === "create"
                    ? t("admin.categories.form.submit_create")
                    : t("admin.categories.form.submit_edit")
              }}
            </UiButton>
          </div>
        </div>
      </div>
    </Teleport>
  </section>
</template>
