<script setup lang="ts">
import type { CategoryPublic } from "~/types/api";

export interface CategoryFormValue {
  slug: string;
  name_uz: string;
  name_ru: string;
  name_en: string;
  icon: string;
  parent_id: string;
  sort_order: number;
  is_active: boolean;
}

const props = defineProps<{
  modelValue: CategoryFormValue;
  parents: CategoryPublic[];
  /** When editing, the id of the row being edited (so we can exclude it from the parent list). */
  excludeId?: string;
  loading?: boolean;
  error?: string | null;
  submitLabel: string;
  /** Where the cancel button links to. */
  cancelTo: string;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: CategoryFormValue];
  "submit": [];
}>();

const { t } = useI18n();
const { localised } = useLocaleText();

const form = computed({
  get: () => props.modelValue,
  set: (v) => emit("update:modelValue", v),
});

function update<K extends keyof CategoryFormValue>(key: K, value: CategoryFormValue[K]) {
  emit("update:modelValue", { ...props.modelValue, [key]: value });
}

const parentOptions = computed(() => {
  const opts: { value: string; label: string }[] = [
    { value: "", label: t("admin.categories.form.parent_none") },
  ];
  for (const c of props.parents) {
    if (props.excludeId && c.id === props.excludeId) continue;
    if (c.parent_id) continue;
    opts.push({ value: c.id, label: localised(c.name, c.slug) });
  }
  return opts;
});
</script>

<template>
  <form class="space-y-5" novalidate @submit.prevent="emit('submit')">
    <div class="rounded-md border border-border bg-bg-card p-5 space-y-4">
      <h2 class="font-medium text-ink text-sm uppercase tracking-wider text-ink-tertiary">
        {{ t("admin.categories.form.section_identity") }}
      </h2>

      <UiInput
        :model-value="form.slug"
        :label="t('admin.categories.form.slug')"
        :hint="t('admin.categories.form.slug_hint')"
        required
        @update:model-value="(v) => update('slug', v)"
      />

      <div class="grid sm:grid-cols-3 gap-3">
        <UiInput
          :model-value="form.name_uz"
          :label="t('admin.categories.form.name_uz')"
          @update:model-value="(v) => update('name_uz', v)"
        />
        <UiInput
          :model-value="form.name_ru"
          :label="t('admin.categories.form.name_ru')"
          @update:model-value="(v) => update('name_ru', v)"
        />
        <UiInput
          :model-value="form.name_en"
          :label="t('admin.categories.form.name_en')"
          @update:model-value="(v) => update('name_en', v)"
        />
      </div>
    </div>

    <div class="rounded-md border border-border bg-bg-card p-5 space-y-4">
      <h2 class="text-sm uppercase tracking-wider text-ink-tertiary">
        {{ t("admin.categories.form.section_display") }}
      </h2>

      <div class="grid sm:grid-cols-2 gap-3">
        <IconPicker
          :model-value="form.icon"
          :label="t('admin.categories.form.icon')"
          :hint="t('admin.categories.form.icon_hint')"
          clearable
          @update:model-value="(v) => update('icon', v)"
        />

        <UiSelect
          :model-value="form.parent_id"
          :label="t('admin.categories.form.parent')"
          :options="parentOptions"
          @update:model-value="(v) => update('parent_id', v)"
        />
      </div>

      <div class="grid sm:grid-cols-2 gap-3 items-end">
        <UiInput
          :model-value="String(form.sort_order)"
          type="number"
          :label="t('admin.categories.form.sort_order')"
          @update:model-value="(v) => update('sort_order', Number(v) || 0)"
        />
        <label class="flex items-center gap-2 text-sm text-ink cursor-pointer pb-2">
          <input
            :checked="form.is_active"
            type="checkbox"
            class="h-4 w-4 rounded border-border text-primary focus:ring-primary"
            @change="(e) => update('is_active', (e.target as HTMLInputElement).checked)"
          >
          {{ t("admin.categories.form.is_active") }}
        </label>
      </div>
    </div>

    <p v-if="error" class="flex items-center gap-2 text-sm text-error">
      <Icon name="warning-solid" class="h-4 w-4" />
      {{ error }}
    </p>

    <div class="flex items-center justify-end gap-2">
      <UiButton variant="ghost" :to="cancelTo">
        {{ t("admin.actions.cancel") }}
      </UiButton>
      <UiButton type="submit" :loading="loading" :disabled="loading">
        <Icon name="check" class="h-4 w-4" />
        {{ submitLabel }}
      </UiButton>
    </div>
  </form>
</template>
