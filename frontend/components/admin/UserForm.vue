<script setup lang="ts">
import type { UserRole, UserStatus } from "~/types/api";

export interface UserFormValue {
  email: string;
  full_name: string;
  role: UserRole;
  status: UserStatus;
  password: string;
  display_name: string;
  academic_title: string;
  institution: string;
  bio: string;
}

const props = defineProps<{
  modelValue: UserFormValue;
  /** When true the password field is shown only when explicitly opened
   *  (edit flow: keep current password unless admin chooses to change it). */
  passwordOptional?: boolean;
  loading?: boolean;
  error?: string | null;
  submitLabel: string;
  cancelTo: string;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: UserFormValue];
  "submit": [];
}>();

const { t } = useI18n();
const { user: me } = useAuth();

function update<K extends keyof UserFormValue>(key: K, value: UserFormValue[K]) {
  emit("update:modelValue", { ...props.modelValue, [key]: value });
}

const roleOptions = computed(() => {
  const opts: { value: UserRole; label: string }[] = [
    { value: "reader" as UserRole, label: t("admin.users.roles.reader") },
    { value: "author" as UserRole, label: t("admin.users.roles.author") },
    { value: "admin" as UserRole, label: t("admin.users.roles.admin") },
  ];
  if (me.value?.role === "superadmin") {
    opts.push({ value: "superadmin" as UserRole, label: t("admin.users.roles.superadmin") });
  }
  return opts;
});

const statusOptions = computed<{ value: UserStatus; label: string }[]>(() => [
  { value: "active", label: t("admin.users.statuses.active") },
  { value: "pending", label: t("admin.users.statuses.pending") },
  { value: "blocked", label: t("admin.users.statuses.blocked") },
]);

const isAuthorRole = computed(() =>
  ["author", "admin", "superadmin"].includes(props.modelValue.role),
);

const changePassword = ref(false);
</script>

<template>
  <form class="space-y-5" novalidate @submit.prevent="emit('submit')">
    <div class="rounded-md border border-border bg-bg-card p-5 space-y-4">
      <h2 class="text-sm uppercase tracking-wider text-ink-tertiary">
        {{ t("admin.users.form.section_identity") }}
      </h2>

      <UiInput
        :model-value="modelValue.full_name"
        :label="t('admin.users.form.full_name')"
        required
        autocomplete="name"
        @update:model-value="(v) => update('full_name', v)"
      />

      <UiInput
        :model-value="modelValue.email"
        type="email"
        :label="t('admin.users.form.email')"
        required
        autocomplete="email"
        @update:model-value="(v) => update('email', v)"
      />
    </div>

    <div class="rounded-md border border-border bg-bg-card p-5 space-y-4">
      <h2 class="text-sm uppercase tracking-wider text-ink-tertiary">
        {{ t("admin.users.form.section_access") }}
      </h2>

      <div class="grid sm:grid-cols-2 gap-3">
        <UiSelect
          :model-value="modelValue.role"
          :label="t('admin.users.form.role')"
          :options="roleOptions"
          @update:model-value="(v) => update('role', v as UserRole)"
        />
        <UiSelect
          :model-value="modelValue.status"
          :label="t('admin.users.form.status')"
          :options="statusOptions"
          @update:model-value="(v) => update('status', v as UserStatus)"
        />
      </div>
    </div>

    <div v-if="isAuthorRole" class="rounded-md border border-border bg-bg-card p-5 space-y-4">
      <h2 class="text-sm uppercase tracking-wider text-ink-tertiary">
        {{ t("admin.users.form.section_author_profile") }}
      </h2>
      <p class="text-xs text-ink-tertiary">
        {{ t("admin.users.form.author_profile_hint") }}
      </p>

      <UiInput
        :model-value="modelValue.display_name"
        :label="t('admin.users.form.display_name')"
        :placeholder="modelValue.full_name"
        @update:model-value="(v) => update('display_name', v)"
      />

      <div class="grid sm:grid-cols-2 gap-3">
        <UiInput
          :model-value="modelValue.academic_title"
          :label="t('admin.users.form.academic_title')"
          :placeholder="t('admin.users.form.academic_title_placeholder')"
          @update:model-value="(v) => update('academic_title', v)"
        />
        <UiInput
          :model-value="modelValue.institution"
          :label="t('admin.users.form.institution')"
          :placeholder="t('admin.users.form.institution_placeholder')"
          @update:model-value="(v) => update('institution', v)"
        />
      </div>

      <label class="block">
        <span class="block text-sm font-medium text-ink-secondary mb-1.5">
          {{ t("admin.users.form.bio") }}
        </span>
        <textarea
          :value="modelValue.bio"
          rows="4"
          maxlength="2000"
          class="w-full px-3.5 py-2.5 rounded-md border border-border bg-bg-card text-ink placeholder:text-ink-tertiary focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors"
          @input="(e) => update('bio', (e.target as HTMLTextAreaElement).value)"
        />
      </label>
    </div>

    <div class="rounded-md border border-border bg-bg-card p-5 space-y-4">
      <h2 class="text-sm uppercase tracking-wider text-ink-tertiary">
        {{ t("admin.users.form.section_password") }}
      </h2>

      <template v-if="!passwordOptional || changePassword">
        <UiInput
          :model-value="modelValue.password"
          type="password"
          :label="t('admin.users.form.password')"
          :hint="t('admin.users.form.password_hint')"
          :required="!passwordOptional"
          autocomplete="new-password"
          minlength="8"
          @update:model-value="(v) => update('password', v)"
        />
        <button
          v-if="passwordOptional"
          type="button"
          class="text-xs text-ink-secondary hover:text-ink underline"
          @click="changePassword = false; update('password', '')"
        >
          {{ t("admin.users.form.cancel_password_change") }}
        </button>
      </template>
      <button
        v-else
        type="button"
        class="inline-flex items-center gap-1.5 text-sm text-primary hover:underline"
        @click="changePassword = true"
      >
        <Icon name="key" class="h-4 w-4" />
        {{ t("admin.users.form.change_password") }}
      </button>
    </div>

    <p v-if="error" class="flex items-center gap-2 text-sm text-error">
      <Icon name="warning-solid" class="h-4 w-4" />
      {{ error }}
    </p>

    <div class="flex items-center justify-end gap-2 flex-wrap">
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
