<script setup lang="ts">
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({ layout: "auth", middleware: "guest" });

const { t } = useI18n();
const localePath = useLocalePath();
const route = useRoute();
const auth = useAuthStore();

useSiteSeo({
  title: t("auth.login.title"),
  description: t("auth.login.subtitle"),
  noindex: true,
});

const email = ref("");
const password = ref("");
const submitting = ref(false);
const error = ref<string | null>(null);

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
  () => email.value && password.value && !emailError.value && !submitting.value,
);

async function onSubmit() {
  validateEmail();
  if (emailError.value) return;
  submitting.value = true;
  error.value = null;
  try {
    await auth.login(email.value, password.value);
    const redirect = (route.query.redirect as string) || localePath("/account");
    await navigateTo(redirect);
  }
  catch (err) {
    error.value = apiErrorMessage(err, t("auth.login.error_generic"));
  }
  finally {
    submitting.value = false;
  }
}
</script>

<template>
  <AuthCard
    badge="👋"
    :title="t('auth.login.title')"
    :subtitle="t('auth.login.subtitle')"
  >
    <form class="space-y-4" novalidate @submit.prevent="onSubmit">
      <AuthAlert v-if="error">
        {{ error }}
      </AuthAlert>

      <FormField
        v-model="email"
        :label="t('auth.login.email')"
        type="email"
        inputmode="email"
        autocomplete="email"
        :error="emailError ?? undefined"
        :placeholder="'name@example.com'"
        required
        autofocus
        @update:model-value="validateEmail"
      />

      <PasswordField
        v-model="password"
        :label="t('auth.login.password')"
        autocomplete="current-password"
        required
      />

      <div class="flex justify-end -mt-1">
        <NuxtLink
          :to="localePath('/auth/forgot-password')"
          class="text-xs text-primary hover:underline"
        >
          {{ t("auth.login.forgot_link") }}
        </NuxtLink>
      </div>

      <AuthSubmit
        :loading="submitting"
        :disabled="!canSubmit"
        :label="t('auth.login.submit')"
        :loading-label="t('auth.login.submitting')"
      />
    </form>

    <template #footer>
      {{ t("auth.login.no_account") }}
      <NuxtLink
        :to="localePath('/auth/register')"
        class="text-primary hover:underline font-medium"
      >
        {{ t("auth.login.register_link") }}
      </NuxtLink>
    </template>
  </AuthCard>
</template>
