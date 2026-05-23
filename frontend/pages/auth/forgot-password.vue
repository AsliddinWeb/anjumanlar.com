<script setup lang="ts">
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({ layout: "auth", middleware: "guest" });

const { t } = useI18n();
const localePath = useLocalePath();
const api = useApi();

useSiteSeo({
  title: t("auth.forgot.title"),
  description: t("auth.forgot.subtitle"),
  noindex: true,
});

const email = ref("");
const submitting = ref(false);
const error = ref<string | null>(null);
const success = ref(false);

const emailError = ref<string | null>(null);

function validateEmail() {
  if (!email.value) {
    emailError.value = null;
    return;
  }
  emailError.value =
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value) ? null : t("auth.validation.email_invalid");
}

const canSubmit = computed(
  () => email.value && !emailError.value && !submitting.value,
);

async function onSubmit() {
  validateEmail();
  if (emailError.value) return;
  submitting.value = true;
  error.value = null;
  try {
    await api("/auth/forgot-password", {
      method: "POST",
      body: { email: email.value },
    });
    success.value = true;
  }
  catch (err) {
    error.value = apiErrorMessage(err, t("common.error"));
  }
  finally {
    submitting.value = false;
  }
}
</script>

<template>
  <AuthCard
    v-if="success"
    icon="envelope"
    :title="t('auth.forgot.title')"
    :subtitle="t('auth.forgot.success')"
  >
    <NuxtLink
      :to="localePath('/auth/login')"
      class="flex items-center justify-center gap-2 w-full text-center px-4 py-2.5 rounded border border-border text-ink-secondary hover:border-primary hover:text-primary"
    >
      <Icon name="arrow-left" class="h-4 w-4" />
      {{ t("auth.forgot.back_to_login") }}
    </NuxtLink>
  </AuthCard>

  <AuthCard
    v-else
    icon="key"
    :title="t('auth.forgot.title')"
    :subtitle="t('auth.forgot.subtitle')"
  >
    <form class="space-y-4" novalidate @submit.prevent="onSubmit">
      <AuthAlert v-if="error">
        {{ error }}
      </AuthAlert>

      <FormField
        v-model="email"
        :label="t('auth.forgot.email')"
        type="email"
        inputmode="email"
        autocomplete="email"
        :error="emailError ?? undefined"
        placeholder="name@example.com"
        required
        autofocus
        @update:model-value="validateEmail"
      />

      <AuthSubmit
        :loading="submitting"
        :disabled="!canSubmit"
        :label="t('auth.forgot.submit')"
        :loading-label="t('auth.forgot.submitting')"
      />
    </form>

    <template #footer>
      <NuxtLink
        :to="localePath('/auth/login')"
        class="inline-flex items-center gap-1 text-primary hover:underline font-medium"
      >
        <Icon name="arrow-left" class="h-4 w-4" />
        {{ t("auth.forgot.back_to_login") }}
      </NuxtLink>
    </template>
  </AuthCard>
</template>
