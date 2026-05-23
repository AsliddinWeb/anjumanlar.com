<script setup lang="ts">
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({ layout: "auth" });

const { t } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const api = useApi();

useSiteSeo({
  title: t("auth.verify.title"),
  noindex: true,
});

type State = "verifying" | "success" | "error";
const state = ref<State>("verifying");
const error = ref<string | null>(null);

onMounted(async () => {
  const token = route.query.token as string | undefined;
  if (!token) {
    state.value = "error";
    error.value = t("auth.verify.error");
    return;
  }
  try {
    await api("/auth/verify-email", {
      method: "POST",
      body: { token },
    });
    state.value = "success";
  }
  catch (err) {
    error.value = apiErrorMessage(err, t("auth.verify.error"));
    state.value = "error";
  }
});

const badge = computed(() => {
  if (state.value === "success") return "✅";
  if (state.value === "error") return "⚠";
  return "⏳";
});
const subtitle = computed(() => {
  if (state.value === "success") return t("auth.verify.success");
  if (state.value === "error") return error.value ?? t("auth.verify.error");
  return t("auth.verify.in_progress");
});
</script>

<template>
  <AuthCard
    :badge="badge"
    :title="t('auth.verify.title')"
    :subtitle="subtitle"
  >
    <div v-if="state === 'verifying'" class="flex items-center justify-center py-2">
      <UiSpinner class="h-6 w-6 text-primary" />
    </div>

    <NuxtLink
      v-else-if="state === 'success'"
      :to="localePath('/auth/login')"
      class="block w-full text-center px-4 py-2.5 rounded bg-primary text-ink-inverse hover:bg-primary-hover transition-colors shadow-sm"
    >
      {{ t("auth.verify.go_to_login") }}
    </NuxtLink>

    <NuxtLink
      v-else
      :to="localePath('/auth/login')"
      class="block w-full text-center px-4 py-2.5 rounded border border-border text-ink-secondary hover:border-primary hover:text-primary"
    >
      {{ t("auth.verify.go_to_login") }}
    </NuxtLink>
  </AuthCard>
</template>
