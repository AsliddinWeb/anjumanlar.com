<script setup lang="ts">
import type { PublicationTypeList, PublicationTypePublic } from "~/types/api";
import type { PublicationTypeFormValue } from "~/components/admin/PublicationTypeForm.vue";
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin", "admin-scope"],
  adminScope: "categories",
});

const { t } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const api = useApi();
const toast = useToast();
const { localised } = useLocaleText();

const typeId = computed(() => route.params.id as string);

const { data: ptRaw } = await useAsyncData(
  "admin:publication-types:edit",
  () => api<PublicationTypeList>("/publication-types", { query: { active_only: false } }),
  { server: false },
);

const allTypes = computed<PublicationTypePublic[]>(
  () => ((ptRaw.value as PublicationTypeList | null)?.items ?? []) as PublicationTypePublic[],
);

const current = computed<PublicationTypePublic | null>(
  () => allTypes.value.find((pt) => pt.id === typeId.value) ?? null,
);

if (!current.value) {
  throw createError({ statusCode: 404, statusMessage: "Publication type not found" });
}

useHead({
  title: t("admin.publication_types.form.edit_title") + " — " + localised(current.value!.name, current.value!.slug),
});

const form = ref<PublicationTypeFormValue>({
  slug: current.value!.slug,
  name_uz: (current.value!.name?.uz as string) ?? "",
  name_ru: (current.value!.name?.ru as string) ?? "",
  name_en: (current.value!.name?.en as string) ?? "",
  sort_order: current.value!.sort_order,
  is_active: current.value!.is_active,
});

const submitting = ref(false);
const error = ref<string | null>(null);

async function onSubmit() {
  if (submitting.value) return;
  error.value = null;

  if (!form.value.slug.trim()) {
    error.value = t("admin.publication_types.form.slug_required");
    return;
  }
  const name: Record<string, string> = {};
  if (form.value.name_uz.trim()) name.uz = form.value.name_uz.trim();
  if (form.value.name_ru.trim()) name.ru = form.value.name_ru.trim();
  if (form.value.name_en.trim()) name.en = form.value.name_en.trim();
  if (Object.keys(name).length === 0) {
    error.value = t("admin.publication_types.form.name_required");
    return;
  }

  submitting.value = true;
  try {
    await api(`/publication-types/${typeId.value}`, {
      method: "PATCH",
      body: {
        slug: form.value.slug.trim(),
        name,
        sort_order: Number(form.value.sort_order) || 0,
        is_active: form.value.is_active,
      },
    });
    toast.success(t("admin.publication_types.update_success"));
    await navigateTo(localePath("/admin/publication-types"));
  }
  catch (err) {
    error.value = apiErrorMessage(err, t("admin.form.save_failed"));
  }
  finally {
    submitting.value = false;
  }
}
</script>

<template>
  <section>
    <AdminPageHeader
      :title="t('admin.publication_types.form.edit_title')"
      :description="current ? localised(current.name, current.slug) : ''"
      icon="pencil"
      :breadcrumbs="[
        { label: t('admin.title'), to: localePath('/admin') },
        { label: t('admin.publication_types.title'), to: localePath('/admin/publication-types') },
        { label: current ? localised(current.name, current.slug) : '' },
      ]"
    >
      <template #actions>
        <UiButton variant="ghost" :to="localePath('/admin/publication-types')">
          <Icon name="arrow-left" class="h-4 w-4" />
          {{ t("admin.actions.back") }}
        </UiButton>
      </template>
    </AdminPageHeader>

    <div class="max-w-3xl">
      <PublicationTypeForm
        v-model="form"
        :loading="submitting"
        :error="error"
        :submit-label="t('admin.publication_types.form.submit_edit')"
        :cancel-to="localePath('/admin/publication-types')"
        @submit="onSubmit"
      />
    </div>
  </section>
</template>
