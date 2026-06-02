<script setup lang="ts">
import { THEMES } from "~/utils/themes";
import { ORNAMENTS } from "~/utils/ornaments";
import { apiErrorMessage } from "~/composables/useAuth";

definePageMeta({
  layout: "admin",
  middleware: ["auth", "admin"],
});

const { t } = useI18n();
const localePath = useLocalePath();
const toast = useToast();
const theme = useTheme();

useHead({ title: t("admin.settings.title") });

const applying = ref<string | null>(null);
const applyingOrnament = ref<string | null>(null);

const themeList = computed(() => Object.values(THEMES));
const ornamentList = computed(() => Object.values(ORNAMENTS));

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
