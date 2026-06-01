<script setup lang="ts">
import type { AuthorList, ReviewRequestPublic } from "~/types/api";
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({ middleware: "auth" });

const { t } = useI18n();
const localePath = useLocalePath();
const router = useRouter();
const api = useApi();
const toast = useToast();

useHead({ title: t("review_requests.new_title") });

const { data: authorsRaw } = await useAsyncData(
  "review-request:new:authors",
  () => api<AuthorList>("/authors", { query: { page_size: 100 } }),
  { server: false },
);
const authors = computed(() => authorsRaw.value?.items ?? []);

const authorId = ref("");
const notes = ref("");
const proposedPrice = ref("");
const submitting = ref(false);
const error = ref<string | null>(null);

const authorOptions = computed(() => [
  { value: "", label: t("review_requests.author_select_placeholder") },
  ...authors.value.map((a) => ({
    value: a.id,
    label: a.academic_title ? `${a.display_name} — ${a.academic_title}` : a.display_name,
  })),
]);

async function submit() {
  error.value = null;
  if (!authorId.value) {
    error.value = t("review_requests.author_required");
    return;
  }
  submitting.value = true;
  try {
    const created = await api<ReviewRequestPublic>("/review-requests", {
      method: "POST",
      body: {
        author_id: authorId.value,
        notes: notes.value.trim() || null,
        proposed_price: proposedPrice.value ? Number(proposedPrice.value) : null,
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
        v-if="authors.length === 0"
        icon="users"
        :title="t('review_requests.no_authors_title')"
        :description="t('review_requests.no_authors_body')"
      />

      <form v-else class="space-y-5" novalidate @submit.prevent="submit">
        <div class="rounded-md border border-border bg-bg-card p-5 space-y-3">
          <h2 class="text-sm uppercase tracking-wider text-ink-tertiary">
            {{ t("review_requests.section_author") }}
          </h2>
          <UiSelect
            v-model="authorId"
            :label="t('review_requests.author_field')"
            :options="authorOptions"
          />
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
          <UiInput
            v-model="proposedPrice"
            type="number"
            :label="t('review_requests.proposed_price')"
            :hint="t('review_requests.proposed_price_hint')"
          />
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
