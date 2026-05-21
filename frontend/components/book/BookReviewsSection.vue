<script setup lang="ts">
import type { ReviewList, ReviewPublic } from "~/types/api";
import { apiErrorMessage } from "~/composables/useAuth";

const props = defineProps<{
  bookId: string;
}>();

const { t, locale } = useI18n();
const localePath = useLocalePath();
const api = useApi();
const { isAuthenticated } = useAuth();

const { data: reviewsRaw, pending, refresh } = await useAsyncData(
  `book:${props.bookId}:reviews`,
  () =>
    api<ReviewList>(`/books/${props.bookId}/reviews`, {
      query: { page: 1, page_size: 20 },
    }),
);

const reviews = computed<ReviewPublic[]>(
  () => ((reviewsRaw.value as ReviewList | null)?.items ?? []) as ReviewPublic[],
);

const formOpen = ref(false);
const formRating = ref(0);
const formTitle = ref("");
const formBody = ref("");
const submitting = ref(false);
const submitError = ref<string | null>(null);
const submitSuccess = ref(false);

function resetForm() {
  formRating.value = 0;
  formTitle.value = "";
  formBody.value = "";
  submitError.value = null;
}

async function submitReview() {
  if (submitting.value) return;
  if (formRating.value < 1 || formRating.value > 5) {
    submitError.value = t("book.review_form.error_generic");
    return;
  }
  if (!formBody.value.trim()) {
    submitError.value = t("book.review_form.error_generic");
    return;
  }
  submitting.value = true;
  submitError.value = null;
  try {
    await api(`/books/${props.bookId}/reviews`, {
      method: "POST",
      body: {
        rating: formRating.value,
        title: formTitle.value.trim() || null,
        body: formBody.value.trim(),
      },
    });
    submitSuccess.value = true;
    resetForm();
    formOpen.value = false;
    await refresh();
  }
  catch (err) {
    submitError.value = apiErrorMessage(err, t("book.review_form.error_generic"));
  }
  finally {
    submitting.value = false;
  }
}

const dateFmt = (iso: string) =>
  new Intl.DateTimeFormat(locale.value, { year: "numeric", month: "short", day: "numeric" })
    .format(new Date(iso));
</script>

<template>
  <div class="space-y-6">
    <!-- Submit area -->
    <div class="rounded border border-border bg-bg-card p-4">
      <div v-if="!isAuthenticated" class="text-sm text-ink-secondary">
        <NuxtLink :to="localePath('/auth/login')" class="text-primary hover:underline">
          {{ t("book.review_form.login_to_review") }}
        </NuxtLink>
      </div>

      <div v-else-if="submitSuccess" class="text-sm text-success">
        ✓ {{ t("book.review_form.success") }}
      </div>

      <div v-else>
        <button
          v-if="!formOpen"
          type="button"
          class="text-sm text-primary hover:underline"
          @click="formOpen = true"
        >
          + {{ t("book.write_review") }}
        </button>

        <form v-else class="space-y-3" @submit.prevent="submitReview">
          <div>
            <span class="block text-sm text-ink-secondary mb-1">
              {{ t("book.review_form.rating") }} <span class="text-error">*</span>
            </span>
            <StarRating
              :value="formRating"
              interactive
              size="lg"
              @update:value="formRating = $event"
            />
          </div>

          <UiInput
            v-model="formTitle"
            :label="t('book.review_form.title')"
            :maxlength="255"
          />

          <label class="block">
            <span class="block text-sm text-ink-secondary mb-1">
              {{ t("book.review_form.body") }} <span class="text-error">*</span>
            </span>
            <textarea
              v-model="formBody"
              rows="4"
              maxlength="5000"
              required
              class="w-full px-3 py-2 rounded border border-border bg-bg-card text-ink placeholder:text-ink-tertiary focus:outline-none focus:border-primary"
            />
          </label>

          <p v-if="submitError" class="text-sm text-error">{{ submitError }}</p>

          <div class="flex gap-2">
            <UiButton type="submit" :loading="submitting" :disabled="submitting">
              {{ submitting ? t("book.review_form.submitting") : t("book.review_form.submit") }}
            </UiButton>
            <UiButton variant="ghost" type="button" :disabled="submitting" @click="formOpen = false; resetForm()">
              {{ t("common.cancel") }}
            </UiButton>
          </div>
        </form>
      </div>
    </div>

    <!-- List -->
    <div v-if="pending && reviews.length === 0" class="text-sm text-ink-tertiary">
      {{ t("book.reviews_loading") }}
    </div>

    <UiEmptyState
      v-else-if="reviews.length === 0"
      icon="💬"
      :title="t('book.no_reviews')"
      :description="t('book.reviews_placeholder')"
    />

    <ul v-else class="space-y-4">
      <li
        v-for="r in reviews"
        :key="r.id"
        class="rounded border border-border bg-bg-card p-4 space-y-2"
      >
        <div class="flex items-center justify-between gap-2">
          <div class="flex items-center gap-3">
            <div class="h-9 w-9 rounded-full bg-bg-secondary flex items-center justify-center text-sm text-ink-secondary">
              {{ (r.user.full_name || "?").trim().charAt(0).toUpperCase() }}
            </div>
            <div>
              <div class="text-sm font-medium text-ink">{{ r.user.full_name }}</div>
              <div class="text-xs text-ink-tertiary">{{ dateFmt(r.created_at) }}</div>
            </div>
          </div>
          <StarRating :value="r.rating" size="sm" />
        </div>
        <h4 v-if="r.title" class="font-medium text-ink">{{ r.title }}</h4>
        <p class="text-sm text-ink-secondary whitespace-pre-line">{{ r.body }}</p>
        <div v-if="r.helpful_count > 0" class="text-xs text-ink-tertiary">
          {{ t("book.review_helpful", { n: r.helpful_count }) }}
        </div>
      </li>
    </ul>
  </div>
</template>
