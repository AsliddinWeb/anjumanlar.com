<script setup lang="ts">
import type { BookLanguage, CategoryPublic } from "~/types/api";

export interface BookFormValue {
  title_uz: string;
  title_ru: string;
  title_en: string;
  subtitle_uz: string;
  subtitle_ru: string;
  subtitle_en: string;
  description_uz: string;
  description_ru: string;
  description_en: string;
  language: BookLanguage;
  isbn: string;
  publication_year: string;
  publisher: string;
  price: string;
  discount_price: string;
  category_ids: string[];
  keywords: string;
}

const props = defineProps<{
  modelValue: BookFormValue;
  categories: CategoryPublic[];
  loading?: boolean;
  error?: string | null;
  submitLabel: string;
  cancelTo: string;
  showDelete?: boolean;
  deleting?: boolean;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: BookFormValue];
  "submit": [];
  "delete": [];
}>();

const { t } = useI18n();
const { localised } = useLocaleText();

function update<K extends keyof BookFormValue>(key: K, value: BookFormValue[K]) {
  emit("update:modelValue", { ...props.modelValue, [key]: value });
}

const activeLang = ref<"uz" | "ru" | "en">("uz");
const langs = [
  { key: "uz" as const, label: "O'zbek" },
  { key: "ru" as const, label: "Русский" },
  { key: "en" as const, label: "English" },
];

function titleKey(l: "uz" | "ru" | "en") {
  return `title_${l}` as const;
}
function subtitleKey(l: "uz" | "ru" | "en") {
  return `subtitle_${l}` as const;
}
function descriptionKey(l: "uz" | "ru" | "en") {
  return `description_${l}` as const;
}

const languageOptions = computed(() => [
  { value: "uz", label: t("account_books.form.languages.uz") },
  { value: "ru", label: t("account_books.form.languages.ru") },
  { value: "en", label: t("account_books.form.languages.en") },
  { value: "mixed", label: t("account_books.form.languages.mixed") },
]);

const categoryOptions = computed(() =>
  [...props.categories].sort((a, b) =>
    localised(a.name, a.slug).localeCompare(localised(b.name, b.slug)),
  ),
);

function toggleCategory(id: string) {
  const set = new Set(props.modelValue.category_ids);
  set.has(id) ? set.delete(id) : set.add(id);
  update("category_ids", [...set]);
}
function isCategorySelected(id: string) {
  return props.modelValue.category_ids.includes(id);
}
</script>

<template>
  <form class="space-y-5" novalidate @submit.prevent="emit('submit')">
    <!-- Multilingual content (title, subtitle, description) -->
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
        <span class="ml-auto text-xs text-ink-tertiary pb-1.5">
          {{ t("account_books.form.lang_hint") }}
        </span>
      </div>

      <div v-for="l in langs" v-show="activeLang === l.key" :key="l.key" class="p-5 space-y-4">
        <UiInput
          :model-value="modelValue[titleKey(l.key)]"
          :label="t('account_books.form.title_field', { lang: l.label })"
          :hint="l.key === 'uz' ? t('account_books.form.title_required_hint') : ''"
          @update:model-value="(v) => update(titleKey(l.key), v)"
        />
        <UiInput
          :model-value="modelValue[subtitleKey(l.key)]"
          :label="t('account_books.form.subtitle_field', { lang: l.label })"
          @update:model-value="(v) => update(subtitleKey(l.key), v)"
        />
        <label class="block">
          <span class="block text-sm text-ink-secondary mb-1">
            {{ t("account_books.form.description_field", { lang: l.label }) }}
          </span>
          <textarea
            :value="modelValue[descriptionKey(l.key)]"
            rows="8"
            class="w-full px-3 py-2 rounded border border-border bg-bg text-ink text-sm focus:outline-none focus:border-primary"
            @input="(e) => update(descriptionKey(l.key), (e.target as HTMLTextAreaElement).value)"
          />
        </label>
      </div>
    </div>

    <!-- Classification -->
    <div class="rounded-md border border-border bg-bg-card p-5 space-y-4">
      <h2 class="text-sm uppercase tracking-wider text-ink-tertiary">
        {{ t("account_books.section_classification") }}
      </h2>

      <div class="grid sm:grid-cols-3 gap-3">
        <UiSelect
          :model-value="modelValue.language"
          :label="t('account_books.form.language')"
          :options="languageOptions"
          @update:model-value="(v) => update('language', v as BookLanguage)"
        />
        <UiInput
          :model-value="modelValue.isbn"
          :label="t('account_books.form.isbn')"
          :placeholder="t('account_books.form.isbn_placeholder')"
          @update:model-value="(v) => update('isbn', v)"
        />
        <UiInput
          :model-value="modelValue.publisher"
          :label="t('account_books.form.publisher')"
          @update:model-value="(v) => update('publisher', v)"
        />
      </div>

      <div class="grid sm:grid-cols-3 gap-3">
        <UiInput
          :model-value="modelValue.publication_year"
          type="number"
          :label="t('account_books.form.publication_year')"
          @update:model-value="(v) => update('publication_year', v)"
        />
      </div>

      <div>
        <span class="block text-sm text-ink-secondary mb-2">
          {{ t("account_books.form.categories") }}
          <span class="text-xs text-ink-tertiary ml-1">{{ t("account_books.form.categories_hint") }}</span>
        </span>
        <div v-if="categoryOptions.length === 0" class="text-sm text-ink-tertiary">
          {{ t("account_books.form.categories_empty") }}
        </div>
        <div v-else class="flex flex-wrap gap-2">
          <button
            v-for="c in categoryOptions"
            :key="c.id"
            type="button"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-medium transition-colors"
            :class="isCategorySelected(c.id)
              ? 'border-primary bg-primary/10 text-primary'
              : 'border-border text-ink-secondary hover:border-primary/40 hover:text-ink'"
            @click="toggleCategory(c.id)"
          >
            <Icon v-if="c.icon" :name="c.icon as any" fallback="folder" class="h-3.5 w-3.5" />
            {{ localised(c.name, c.slug) }}
          </button>
        </div>
      </div>
    </div>

    <!-- Pricing -->
    <div class="rounded-md border border-border bg-bg-card p-5 space-y-4">
      <h2 class="text-sm uppercase tracking-wider text-ink-tertiary">
        {{ t("account_books.section_pricing") }}
      </h2>

      <div class="grid sm:grid-cols-2 gap-3">
        <UiInput
          :model-value="modelValue.price"
          type="number"
          :label="t('account_books.form.price')"
          :hint="t('account_books.form.price_hint')"
          @update:model-value="(v) => update('price', v)"
        />
        <UiInput
          :model-value="modelValue.discount_price"
          type="number"
          :label="t('account_books.form.discount_price')"
          :hint="t('account_books.form.discount_price_hint')"
          @update:model-value="(v) => update('discount_price', v)"
        />
      </div>
    </div>

    <!-- Keywords -->
    <div class="rounded-md border border-border bg-bg-card p-5 space-y-4">
      <h2 class="text-sm uppercase tracking-wider text-ink-tertiary">
        {{ t("account_books.section_keywords") }}
      </h2>
      <UiInput
        :model-value="modelValue.keywords"
        :label="t('account_books.form.keywords')"
        :hint="t('account_books.form.keywords_hint')"
        :placeholder="t('account_books.form.keywords_placeholder')"
        @update:model-value="(v) => update('keywords', v)"
      />
    </div>

    <p v-if="error" class="flex items-center gap-2 text-sm text-error">
      <Icon name="warning-solid" class="h-4 w-4" />
      {{ error }}
    </p>

    <div class="flex items-center justify-end gap-2 flex-wrap">
      <UiButton v-if="showDelete" variant="ghost" :loading="deleting" @click="emit('delete')">
        <Icon name="trash" class="h-4 w-4" />
        {{ t("account_books.delete_button") }}
      </UiButton>
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
