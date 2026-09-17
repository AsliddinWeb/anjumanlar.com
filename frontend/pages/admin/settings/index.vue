<script setup lang="ts">
import { THEMES } from "~/utils/themes";
import { ORNAMENTS } from "~/utils/ornaments";
import { apiErrorMessage } from "~/composables/useAuth";
import type { SiteSettingsPublic } from "~/types/api";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin", "admin-scope"],
  adminScope: "settings",
});

const { t } = useI18n();
const localePath = useLocalePath();
const toast = useToast();
const theme = useTheme();
const api = useApi();

useHead({ title: t("admin.settings.title") });

// ---- Contact / social links ----
const { data: settingsRaw } = await useAsyncData(
  "admin:settings:full",
  () => api<SiteSettingsPublic>("/admin/settings"),
  { server: false },
);

const contactForm = reactive({
  contact_name: "",
  contact_phone: "",
  contact_email: "",
  telegram_url: "",
  instagram_url: "",
  facebook_url: "",
  youtube_url: "",
});

watch(settingsRaw, (v) => {
  if (!v) return;
  contactForm.contact_name = v.contact_name ?? "";
  contactForm.contact_phone = v.contact_phone ?? "";
  contactForm.contact_email = v.contact_email ?? "";
  contactForm.telegram_url = v.telegram_url ?? "";
  contactForm.instagram_url = v.instagram_url ?? "";
  contactForm.facebook_url = v.facebook_url ?? "";
  contactForm.youtube_url = v.youtube_url ?? "";
}, { immediate: true });

const savingContact = ref(false);

async function saveContact() {
  if (savingContact.value) return;
  savingContact.value = true;
  try {
    await api("/admin/settings", {
      method: "PATCH",
      body: {
        contact_name: contactForm.contact_name.trim() || null,
        contact_phone: contactForm.contact_phone.trim() || null,
        contact_email: contactForm.contact_email.trim() || null,
        telegram_url: contactForm.telegram_url.trim() || null,
        instagram_url: contactForm.instagram_url.trim() || null,
        facebook_url: contactForm.facebook_url.trim() || null,
        youtube_url: contactForm.youtube_url.trim() || null,
      },
    });
    toast.success(t("admin.settings.contact_applied"));
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    savingContact.value = false;
  }
}

const applying = ref<string | null>(null);
const applyingOrnament = ref<string | null>(null);
const togglingAnimations = ref(false);
const togglingAuthorUploads = ref(false);

const themeList = computed(() => Object.values(THEMES));
const ornamentList = computed(() => Object.values(ORNAMENTS));

async function toggleAnimations() {
  if (togglingAnimations.value) return;
  togglingAnimations.value = true;
  try {
    await theme.setAnimations(!theme.animationsEnabled.value);
    toast.success(t("admin.settings.animations_applied"));
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    togglingAnimations.value = false;
  }
}

async function toggleAuthorUploads() {
  if (togglingAuthorUploads.value) return;
  togglingAuthorUploads.value = true;
  try {
    await theme.setAuthorUploads(!theme.authorUploadsEnabled.value);
    toast.success(t("admin.settings.author_uploads_applied"));
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    togglingAuthorUploads.value = false;
  }
}

async function applyTheme(name: string) {
  if (applying.value || theme.current.value === name) return;
  applying.value = name;
  try {
    await theme.setTheme(name);
    toast.success(t("admin.settings.theme_applied", { name: THEMES[name].label }));
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    applying.value = null;
  }
}

async function applyOrnament(name: string) {
  if (applyingOrnament.value || theme.currentOrnament.value === name) return;
  applyingOrnament.value = name;
  try {
    await theme.setOrnament(name);
    toast.success(t("admin.settings.ornament_applied", { name: ORNAMENTS[name].label }));
  }
  catch (err) {
    toast.error(apiErrorMessage(err, t("common.error")));
  }
  finally {
    applyingOrnament.value = null;
  }
}
</script>

<template>
  <section class="space-y-8">
    <AdminPageHeader
      :title="t('admin.settings.title')"
      :description="t('admin.settings.subtitle')"
      icon="settings"
      :breadcrumbs="[
        { label: t('admin.title'), to: localePath('/admin') },
        { label: t('admin.settings.title') },
      ]"
    >
      <template #actions>
        <AdminStatusPill
          tone="info"
          icon="sparkles"
          :label="t('admin.settings.active_theme', { name: THEMES[theme.current.value]?.label ?? '' })"
        />
      </template>
    </AdminPageHeader>

    <!-- CONTACT / SOCIAL -->
    <section class="space-y-3">
      <h2 class="text-sm uppercase tracking-wider text-ink-tertiary">
        {{ t("admin.settings.contact_section") }}
      </h2>
      <p class="text-sm text-ink-secondary">
        {{ t("admin.settings.contact_hint") }}
      </p>
      <div class="rounded-md border border-border bg-bg-card p-5 space-y-4">
        <div class="grid sm:grid-cols-2 gap-4">
          <UiInput
            v-model="contactForm.contact_name"
            :label="t('admin.settings.contact_name')"
            :placeholder="t('admin.settings.contact_name')"
          />
          <UiInput
            v-model="contactForm.contact_phone"
            :label="t('admin.settings.contact_phone')"
            placeholder="+998 90 123 45 67"
          />
          <UiInput
            v-model="contactForm.contact_email"
            type="email"
            :label="t('admin.settings.contact_email')"
            placeholder="info@monografiya.com"
          />
          <UiInput
            v-model="contactForm.telegram_url"
            :label="t('admin.settings.telegram_url')"
            placeholder="https://t.me/..."
          />
          <UiInput
            v-model="contactForm.instagram_url"
            :label="t('admin.settings.instagram_url')"
            placeholder="https://instagram.com/..."
          />
          <UiInput
            v-model="contactForm.facebook_url"
            :label="t('admin.settings.facebook_url')"
            placeholder="https://facebook.com/..."
          />
          <UiInput
            v-model="contactForm.youtube_url"
            :label="t('admin.settings.youtube_url')"
            placeholder="https://youtube.com/@..."
          />
        </div>
        <div class="flex justify-end">
          <UiButton :loading="savingContact" @click="saveContact">
            <Icon name="check" class="h-4 w-4" />
            {{ t("admin.actions.save") }}
          </UiButton>
        </div>
      </div>
    </section>

    <!-- ANIMATIONS -->
    <section class="space-y-3">
      <h2 class="text-sm uppercase tracking-wider text-ink-tertiary">
        {{ t("admin.settings.animations_section") }}
      </h2>
      <div class="rounded-md border border-border bg-bg-card p-5 flex items-start gap-4">
        <div class="h-10 w-10 rounded-md bg-primary/10 text-primary flex items-center justify-center shrink-0">
          <Icon name="sparkles" class="h-5 w-5" />
        </div>
        <div class="min-w-0 flex-1">
          <h3 class="font-medium text-ink">{{ t("admin.settings.animations_title") }}</h3>
          <p class="text-xs text-ink-secondary mt-0.5">{{ t("admin.settings.animations_hint") }}</p>
        </div>
        <button
          type="button"
          role="switch"
          :aria-checked="theme.animationsEnabled.value"
          class="relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary/30"
          :class="theme.animationsEnabled.value ? 'bg-primary' : 'bg-border'"
          :disabled="togglingAnimations"
          @click="toggleAnimations"
        >
          <span
            class="inline-block h-5 w-5 rounded-full bg-white shadow transform transition-transform"
            :class="theme.animationsEnabled.value ? 'translate-x-[22px]' : 'translate-x-0.5'"
          />
        </button>
      </div>
    </section>

    <!-- AUTHOR UPLOADS -->
    <section class="space-y-3">
      <h2 class="text-sm uppercase tracking-wider text-ink-tertiary">
        {{ t("admin.settings.author_uploads_section") }}
      </h2>
      <div class="rounded-md border border-border bg-bg-card p-5 flex items-start gap-4">
        <div class="h-10 w-10 rounded-md bg-primary/10 text-primary flex items-center justify-center shrink-0">
          <Icon name="book" class="h-5 w-5" />
        </div>
        <div class="min-w-0 flex-1">
          <h3 class="font-medium text-ink">{{ t("admin.settings.author_uploads_title") }}</h3>
          <p class="text-xs text-ink-secondary mt-0.5">{{ t("admin.settings.author_uploads_hint") }}</p>
          <p v-if="!theme.authorUploadsEnabled.value" class="text-xs text-warning mt-1.5 inline-flex items-center gap-1">
            <Icon name="warning" class="h-3.5 w-3.5" />
            {{ t("admin.settings.author_uploads_paused_label") }}
          </p>
        </div>
        <button
          type="button"
          role="switch"
          :aria-checked="theme.authorUploadsEnabled.value"
          class="relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary/30"
          :class="theme.authorUploadsEnabled.value ? 'bg-primary' : 'bg-border'"
          :disabled="togglingAuthorUploads"
          @click="toggleAuthorUploads"
        >
          <span
            class="inline-block h-5 w-5 rounded-full bg-white shadow transform transition-transform"
            :class="theme.authorUploadsEnabled.value ? 'translate-x-[22px]' : 'translate-x-0.5'"
          />
        </button>
      </div>
    </section>

    <!-- THEME -->
    <section class="space-y-3">
      <h2 class="text-sm uppercase tracking-wider text-ink-tertiary">
        {{ t("admin.settings.theme_section") }}
      </h2>
      <p class="text-sm text-ink-secondary">
        {{ t("admin.settings.theme_hint") }}
      </p>

      <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
        <article
          v-for="t_ in themeList"
          :key="t_.name"
          class="rounded-md border bg-bg-card overflow-hidden transition-all"
          :class="theme.current.value === t_.name
            ? 'border-primary ring-2 ring-primary/20'
            : 'border-border hover:border-primary/40'"
        >
          <div class="h-28 flex items-stretch" :style="{ background: t_.palette.bg }">
            <div class="flex-1 flex flex-col justify-end p-3 gap-1">
              <div class="h-3 w-3/4 rounded-full" :style="{ background: t_.palette.textPrimary, opacity: 0.85 }" />
              <div class="h-2 w-1/2 rounded-full" :style="{ background: t_.palette.textSecondary, opacity: 0.6 }" />
            </div>
            <div class="w-1/2 grid grid-cols-2 gap-1 p-2">
              <div class="rounded-md shadow-sm" :style="{ background: t_.palette.primary }" />
              <div class="rounded-md shadow-sm" :style="{ background: t_.palette.accentGold }" />
              <div class="rounded-md shadow-sm" :style="{ background: t_.palette.accentBurgundy }" />
              <div class="rounded-md shadow-sm" :style="{ background: t_.palette.bgCard, border: '1px solid ' + t_.palette.border }" />
            </div>
          </div>
          <div class="p-4 space-y-3 border-t border-border">
            <div class="flex items-start justify-between gap-2">
              <div class="min-w-0">
                <h3 class="font-serif text-lg text-ink leading-tight">{{ t_.label }}</h3>
                <p class="text-xs text-ink-tertiary mt-0.5">{{ t_.description }}</p>
              </div>
              <span
                v-if="theme.current.value === t_.name"
                class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-primary/10 text-primary shrink-0"
              >
                <Icon name="check" class="h-3 w-3" />
                {{ t("admin.settings.active") }}
              </span>
            </div>
            <UiButton
              v-if="theme.current.value !== t_.name"
              variant="ghost"
              size="sm"
              class="w-full"
              :loading="applying === t_.name"
              :disabled="!!applying"
              @click="applyTheme(t_.name)"
            >
              <Icon name="sparkles" class="h-4 w-4" />
              {{ t("admin.settings.apply_theme") }}
            </UiButton>
            <UiButton v-else variant="ghost" size="sm" class="w-full opacity-60 cursor-default" disabled>
              {{ t("admin.settings.already_active") }}
            </UiButton>
          </div>
        </article>
      </div>
    </section>

    <!-- ORNAMENT -->
    <section class="space-y-3">
      <h2 class="text-sm uppercase tracking-wider text-ink-tertiary">
        {{ t("admin.settings.ornament_section") }}
      </h2>
      <p class="text-sm text-ink-secondary">
        {{ t("admin.settings.ornament_hint") }}
      </p>

      <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
        <article
          v-for="o in ornamentList"
          :key="o.name"
          class="rounded-md border bg-bg-card overflow-hidden transition-all"
          :class="theme.currentOrnament.value === o.name
            ? 'border-primary ring-2 ring-primary/20'
            : 'border-border hover:border-primary/40'"
        >
          <!-- Preview: divider centered on a paper-tone strip -->
          <div class="h-28 bg-bg-secondary/60 flex items-center justify-center text-primary">
            <span
              class="block h-px w-12"
              style="background: linear-gradient(to right, transparent, currentColor 70%, currentColor);"
            />
            <svg
              width="60"
              height="60"
              viewBox="0 0 42 42"
              fill="none"
              stroke="currentColor"
              stroke-width="1.2"
              class="opacity-80"
            >
              <g v-html="o.divider" />
            </svg>
            <span
              class="block h-px w-12"
              style="background: linear-gradient(to right, currentColor, currentColor 30%, transparent);"
            />
          </div>

          <div class="p-4 space-y-3 border-t border-border">
            <div class="flex items-start justify-between gap-2">
              <div class="min-w-0">
                <h3 class="font-serif text-lg text-ink leading-tight">{{ o.label }}</h3>
                <p class="text-xs text-ink-tertiary mt-0.5">{{ o.description }}</p>
              </div>
              <span
                v-if="theme.currentOrnament.value === o.name"
                class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-primary/10 text-primary shrink-0"
              >
                <Icon name="check" class="h-3 w-3" />
                {{ t("admin.settings.active") }}
              </span>
            </div>
            <UiButton
              v-if="theme.currentOrnament.value !== o.name"
              variant="ghost"
              size="sm"
              class="w-full"
              :loading="applyingOrnament === o.name"
              :disabled="!!applyingOrnament"
              @click="applyOrnament(o.name)"
            >
              <Icon name="sparkles" class="h-4 w-4" />
              {{ t("admin.settings.apply_ornament") }}
            </UiButton>
            <UiButton v-else variant="ghost" size="sm" class="w-full opacity-60 cursor-default" disabled>
              {{ t("admin.settings.already_active") }}
            </UiButton>
          </div>
        </article>
      </div>
    </section>
  </section>
</template>
