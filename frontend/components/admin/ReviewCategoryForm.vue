<script setup lang="ts">
export interface ReviewCategoryFormValue {
  slug: string;
  name_uz: string;
  name_ru: string;
  name_en: string;
  description_uz: string;
  description_ru: string;
  description_en: string;
  sort_order: string;
  is_active: boolean;
}

const props = defineProps<{
  modelValue: ReviewCategoryFormValue;
  loading?: boolean;
  error?: string | null;
  submitLabel: string;
  cancelTo: string;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: ReviewCategoryFormValue];
  "submit": [];
}>();

const { t } = useI18n();

function update<K extends keyof ReviewCategoryFormValue>(key: K, value: ReviewCategoryFormValue[K]) {
  emit("update:modelValue", { ...props.modelValue, [key]: value });
}

type LangKey = "uz" | "ru" | "en";
const activeLang = ref<LangKey>("uz");
const langs = [
  { key: "uz" as const, label: "O'zbek" },
  { key: "ru" as const, label: "Русский" },
  { key: "en" as const, label: "English" },
];
const activeLabel = computed(() => langs.find((l) => l.key === activeLang.value)?.label ?? "");

function fieldKey(kind: "name" | "description"): keyof ReviewCategoryFormValue {
  return `${kind}_${activeLang.value}` as keyof ReviewCategoryFormValue;
}
</script>

<template>
  <form class="space-y-5" novalidate @submit.prevent="emit('submit')">
    <div class="rounded-md border border-border bg-bg-card p-5 space-y-4">
      <h2 class="text-sm uppercase tracking-wider text-ink-tertiary">
        {{ t("admin.review_categories.section_identity") }}
      </h2>
      <UiInput
        :model-value="modelValue.slug"
        :label="t('admin.review_categories.form.slug')"
        :hint="t('admin.review_categories.form.slug_hint')"
        placeholder="article"
        @update:model-value="(v) => update('slug', v)"
      />
      <UiInput
        :model-value="modelValue.sort_order"
        type="number"
        :label="t('admin.review_categories.form.sort_order')"
        @update:model-value="(v) => update('sort_order', v)"
      />
      <label class="flex items-start gap-3 cursor-pointer">
        <button
          type="button"
          class="relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary/30 mt-0.5"
          :class="modelValue.is_active ? 'bg-primary' : 'bg-border'"
          @click="update('is_active', !modelValue.is_active)"
        >
          <span
            class="inline-block h-5 w-5 rounded-full bg-white shadow transform transition-transform"
            :class="modelValue.is_active ? 'translate-x-[22px]' : 'translate-x-0.5'"
          />
        </button>
        <span class="min-w-0">
          <span class="block text-sm font-medium text-ink">{{ t("admin.review_categories.form.is_active") }}</span>
          <span class="block text-xs text-ink-tertiary mt-0.5">{{ t("admin.review_categories.form.is_active_hint") }}</span>
        </span>
      </label>
    </div>

    <div class="rounded-md border border-border bg-bg-card overflow-hidden">
      <div class="flex items-center gap-1 px-3 pt-3 border-b border-border">
        <button
          v-for="l in langs"
          :key="l.key"
          type="button"
          class="px-3 py-1.5 -mb-px text-sm border-b-2 transition-colors"
          :class="activeLang === l.key
            ? 'border-primary text-primary font-medium'
            : 'border-transparent text-ink-secondary hover:text-ink'"
          @click="activeLang = l.key"
        >
          {{ l.label }}
        </button>
      </div>
      <div :key="activeLang" class="p-5 space-y-4">
        <UiInput
          :model-value="modelValue[fieldKey('name')] as string"
          :label="t('admin.review_categories.form.name_field', { lang: activeLabel })"
          @update:model-value="(v) => update(fieldKey('name'), v as never)"
        />
        <label class="block">
          <span class="block text-sm text-ink-secondary mb-1">
            {{ t("admin.review_categories.form.description_field", { lang: activeLabel }) }}
          </span>
          <textarea
            :value="modelValue[fieldKey('description')] as string"
            rows="4"
            class="w-full px-3 py-2 rounded border border-border bg-bg text-ink text-sm focus:outline-none focus:border-primary"
            @input="(e) => update(fieldKey('description'), (e.target as HTMLTextAreaElement).value as never)"
          />
        </label>
      </div>
    </div>

    <p v-if="error" class="flex items-center gap-2 text-sm text-error">
      <Icon name="warning-solid" class="h-4 w-4" />
      {{ error }}
    </p>

    <div class="flex items-center justify-end gap-2">
      <UiButton variant="ghost" :to="cancelTo">
        {{ t("common.cancel") }}
      </UiButton>
      <UiButton type="submit" :loading="loading" :disabled="loading">
        <Icon name="check" class="h-4 w-4" />
        {{ submitLabel }}
      </UiButton>
    </div>
  </form>
</template>
