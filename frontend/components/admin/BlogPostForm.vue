<script setup lang="ts">
export interface BlogPostFormValue {
  slug: string;
  title_uz: string;
  title_ru: string;
  title_en: string;
  excerpt_uz: string;
  excerpt_ru: string;
  excerpt_en: string;
  body_uz: string;
  body_ru: string;
  body_en: string;
  cover_url: string;
}

const props = defineProps<{
  modelValue: BlogPostFormValue;
  loading?: boolean;
  error?: string | null;
  submitLabel: string;
  cancelTo: string;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: BlogPostFormValue];
  "submit": [];
}>();

const { t } = useI18n();

function update<K extends keyof BlogPostFormValue>(key: K, value: BlogPostFormValue[K]) {
  emit("update:modelValue", { ...props.modelValue, [key]: value });
}

const activeLang = ref<"uz" | "ru" | "en">("uz");
const langs = [
  { key: "uz" as const, label: "O'zbek" },
  { key: "ru" as const, label: "Русский" },
  { key: "en" as const, label: "English" },
];

function titleKey(lang: "uz" | "ru" | "en") {
  return `title_${lang}` as const;
}
function excerptKey(lang: "uz" | "ru" | "en") {
  return `excerpt_${lang}` as const;
}
function bodyKey(lang: "uz" | "ru" | "en") {
  return `body_${lang}` as const;
}
</script>

<template>
  <form class="space-y-5" novalidate @submit.prevent="emit('submit')">
    <div class="rounded-md border border-border bg-bg-card p-5 space-y-4">
      <h2 class="text-sm uppercase tracking-wider text-ink-tertiary">
        {{ t("admin.blog.form.section_identity") }}
      </h2>

      <UiInput
        :model-value="modelValue.slug"
        :label="t('admin.blog.form.slug')"
        :hint="t('admin.blog.form.slug_hint')"
        required
        @update:model-value="(v) => update('slug', v)"
      />

      <UiInput
        :model-value="modelValue.cover_url"
        :label="t('admin.blog.form.cover_url')"
        placeholder="https://"
        @update:model-value="(v) => update('cover_url', v)"
      />
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
        <span class="ml-auto text-xs text-ink-tertiary pb-1.5">
          {{ t("admin.blog.form.lang_hint") }}
        </span>
      </div>

      <div v-for="l in langs" v-show="activeLang === l.key" :key="l.key" class="p-5 space-y-4">
        <UiInput
          :model-value="modelValue[titleKey(l.key)]"
          :label="t('admin.blog.form.title_field', { lang: l.label })"
          @update:model-value="(v) => update(titleKey(l.key), v)"
        />

        <label class="block">
          <span class="block text-sm text-ink-secondary mb-1">
            {{ t("admin.blog.form.excerpt_field", { lang: l.label }) }}
          </span>
          <textarea
            :value="modelValue[excerptKey(l.key)]"
            rows="3"
            class="w-full px-3 py-2 rounded border border-border bg-bg text-ink text-sm focus:outline-none focus:border-primary"
            @input="(e) => update(excerptKey(l.key), (e.target as HTMLTextAreaElement).value)"
          />
        </label>

        <label class="block">
          <span class="block text-sm text-ink-secondary mb-1">
            {{ t("admin.blog.form.body_field", { lang: l.label }) }}
          </span>
          <textarea
            :value="modelValue[bodyKey(l.key)]"
            rows="12"
            class="w-full px-3 py-2 rounded border border-border bg-bg text-ink text-sm focus:outline-none focus:border-primary font-mono"
            @input="(e) => update(bodyKey(l.key), (e.target as HTMLTextAreaElement).value)"
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
        {{ t("admin.actions.cancel") }}
      </UiButton>
      <UiButton type="submit" :loading="loading" :disabled="loading">
        <Icon name="check" class="h-4 w-4" />
        {{ submitLabel }}
      </UiButton>
    </div>
  </form>
</template>
