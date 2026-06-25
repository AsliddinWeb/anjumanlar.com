<script setup lang="ts">
/**
 * Nuxt's global error boundary.
 *
 * Catches anything that bubbles past a page's local error handler (route
 * misses, SSR throws, API failures during navigation). Picks the copy
 * by HTTP status so a 404 doesn't read like a server-down panic.
 */
import type { NuxtError } from "#app";

const props = defineProps<{ error: NuxtError }>();

const { t } = useI18n();
const localePath = useLocalePath();

const statusCode = computed(() => Number(props.error?.statusCode ?? 500));
const isNotFound = computed(() => statusCode.value === 404);

const headingKey = computed(() => isNotFound.value ? "errors.not_found_title" : "errors.server_title");
const bodyKey = computed(() => isNotFound.value ? "errors.not_found_body" : "errors.server_body");

function goHome() {
  return clearError({ redirect: localePath("/") });
}
</script>

<template>
  <NuxtLayout name="default">
    <section class="bg-bg">
      <div class="max-w-2xl mx-auto px-4 py-20 md:py-28 text-center space-y-6">
        <p class="font-serif text-7xl md:text-8xl text-primary/30 tabular-nums tracking-tight">
          {{ statusCode }}
        </p>
        <div class="space-y-2">
          <h1 class="font-serif text-2xl md:text-3xl text-ink leading-tight">
            {{ t(headingKey) }}
          </h1>
          <p class="text-sm text-ink-secondary max-w-md mx-auto">
            {{ t(bodyKey) }}
          </p>
        </div>
        <div class="flex flex-wrap items-center justify-center gap-2">
          <UiButton @click.prevent="goHome">
            <Icon name="home" class="h-4 w-4" />
            {{ t("errors.go_home") }}
          </UiButton>
          <UiButton variant="ghost" :to="localePath('/books')">
            <Icon name="book" class="h-4 w-4" />
            {{ t("errors.browse_books") }}
          </UiButton>
        </div>
      </div>
    </section>
  </NuxtLayout>
</template>
