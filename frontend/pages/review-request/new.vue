<script setup lang="ts">
import type { ReviewCategoryList, ReviewRequestPublic } from "~/types/api";
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({ middleware: "auth" });

const { t } = useI18n();
const localePath = useLocalePath();
const router = useRouter();
const api = useApi();
const toast = useToast();
const { localised } = useLocaleText();

useHead({ title: t("review_requests.new_title") });

const { data: categoriesRaw } = await useAsyncData(
  "review-request:new:categories",
  () => api<ReviewCategoryList>("/review-categories"),
  { server: false },
);
const categories = computed(() => categoriesRaw.value?.items ?? []);

const categoryId = ref("");
const isInternational = ref(false);
const notes = ref("");
const submitting = ref(false);
const error = ref<string | null>(null);

const categoryOptions = computed(() => [
  { value: "", label: t("review_requests.category_select_placeholder") },
  ...categories.value.map((c) => ({
    value: c.id,
    label: localised(c.name, c.slug),
  })),
]);

async function submit() {
  error.value = null;
  if (!categoryId.value) {
    error.value = t("review_requests.category_required");
    return;
  }
  submitting.value = true;
  try {
    const created = await api<ReviewRequestPublic>("/review-requests", {
      method: "POST",
      body: {
        category_id: categoryId.value,
        is_international: isInternational.value,
        notes: notes.value.trim() || null,
      },
    });
    toast.success(t("review_requests.create_success"));
    await router.push(localePath(`/account/review-requests/${created.id}`));
  }
  catch (err) {
    error.value = apiErrorMessage(err, t("common.error"));
    toast.error(error.value);
  }
  finally {
    submitting.value = false;
  }
}
</script>

<template>
  <AccountShell>
    <section class="space-y-5">
      <header>
        <h1 class="font-serif text-2xl md:text-3xl text-ink leading-tight">
          {{ t("review_requests.new_title") }}
        </h1>
        <p class="text-sm text-ink-secondary mt-1">{{ t("review_requests.new_subtitle") }}</p>
      </header>

      <UiEmptyState
        v-if="categories.length === 0"
        icon="folder"
        :title="t('review_requests.no_categories_title')"
        :description="t('review_requests.no_categories_body')"
      />

      <form v-else class="space-y-5" novalidate @submit.prevent="submit">
        <div class="rounded-md border border-border bg-bg-card p-5 space-y-4">
          <h2 class="text-sm uppercase tracking-wider text-ink-tertiary">
            {{ t("review_requests.section_category") }}
          </h2>
          <UiSelect
            v-model="categoryId"
            :label="t('review_requests.category_field')"
            :options="categoryOptions"
            :hint="t('review_requests.category_hint')"
          />
          <label class="flex items-start gap-3 cursor-pointer">
            <button
              type="button"
              class="relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary/30 mt-0.5"
              :class="isInternational ? 'bg-primary' : 'bg-border'"
              @click="isInternational = !isInternational"
            >
              <span
                class="inline-block h-5 w-5 rounded-full bg-white shadow transform transition-transform"
                :class="isInternational ? 'translate-x-[22px]' : 'translate-x-0.5'"
              />
            </button>
            <span class="min-w-0">
              <span class="block text-sm font-medium text-ink">{{ t("review_requests.international_field") }}</span>
              <span class="block text-xs text-ink-tertiary mt-0.5">{{ t("review_requests.international_hint") }}</span>
            </span>
          </label>
        </div>

        <div class="rounded-md border border-border bg-bg-card p-5 space-y-3">
          <h2 class="text-sm uppercase tracking-wider text-ink-tertiary">
            {{ t("review_requests.section_details") }}
          </h2>
          <label class="block">
            <span class="block text-sm font-medium text-ink-secondary mb-1.5">
              {{ t("review_requests.notes_field") }}
            </span>
            <textarea
              v-model="notes"
              rows="6"
              maxlength="4000"
              :placeholder="t('review_requests.notes_placeholder')"
              class="w-full px-3.5 py-2.5 rounded-md border border-border bg-bg-card text-ink placeholder:text-ink-tertiary focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors"
            />
          </label>
          <p class="text-xs text-ink-tertiary">
            {{ t("review_requests.manuscript_upload_after_create_hint") }}
          </p>
        </div>

        <p v-if="error" class="flex items-center gap-2 text-sm text-error">
          <Icon name="warning-solid" class="h-4 w-4" />
          {{ error }}
        </p>

        <div class="flex items-center justify-end gap-2">
          <UiButton variant="ghost" :to="localePath('/account/review-requests')">
            {{ t("common.cancel") }}
          </UiButton>
          <UiButton type="submit" :loading="submitting" :disabled="submitting">
            <Icon name="check" class="h-4 w-4" />
            {{ t("review_requests.create_button") }}
          </UiButton>
        </div>
      </form>
    </section>
  </AccountShell>
</template>
