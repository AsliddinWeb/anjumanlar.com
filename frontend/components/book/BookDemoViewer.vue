<script setup lang="ts">
const props = defineProps<{
  demoUrl: string | null;
  title: string;
}>();

const { t } = useI18n();
const open = ref(false);
const iframeError = ref(false);

function close() {
  open.value = false;
  iframeError.value = false;
}

// Add #toolbar=0 etc. so Chrome's PDF viewer shows just the pages.
const embedUrl = computed(() => {
  if (!props.demoUrl) return null;
  const sep = props.demoUrl.includes("#") ? "&" : "#";
  return `${props.demoUrl}${sep}view=FitH&toolbar=1&navpanes=0`;
});

// Lock body scroll when the modal is open.
watch(open, (isOpen) => {
  if (import.meta.client) {
    document.body.style.overflow = isOpen ? "hidden" : "";
  }
});

onBeforeUnmount(() => {
  if (import.meta.client) document.body.style.overflow = "";
});
</script>

<template>
  <div v-if="demoUrl">
    <UiButton variant="ghost" size="lg" @click="open = true">
      {{ t("book.preview") }}
    </UiButton>

    <Teleport v-if="open" to="body">
      <div
        class="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4"
        role="dialog"
        aria-modal="true"
        @click.self="close"
      >
        <div class="relative w-full max-w-4xl h-[85vh] rounded bg-bg-card border border-border shadow-xl flex flex-col">
          <header class="flex items-center justify-between gap-2 p-3 border-b border-border">
            <div class="min-w-0">
              <h3 class="font-medium text-ink truncate">{{ t("book.demo_title") }}</h3>
              <p class="text-xs text-ink-tertiary truncate">{{ title }}</p>
            </div>
            <div class="flex items-center gap-2">
              <a
                :href="demoUrl"
                target="_blank"
                rel="noopener noreferrer"
                class="text-xs text-primary hover:underline"
              >
                {{ t("book.demo_open_new_tab") }} ↗
              </a>
              <button
                type="button"
                class="h-8 w-8 inline-flex items-center justify-center rounded text-ink-secondary hover:bg-bg-secondary hover:text-ink"
                :aria-label="t('common.cancel')"
                @click="close"
              >
                ✕
              </button>
            </div>
          </header>

          <div class="flex-1 overflow-hidden">
            <iframe
              v-if="!iframeError && embedUrl"
              :src="embedUrl"
              :title="t('book.demo_title')"
              class="w-full h-full"
              @error="iframeError = true"
            />
            <div v-else class="h-full flex flex-col items-center justify-center gap-3 text-sm text-ink-secondary p-6 text-center">
              <p>{{ t("book.demo_unavailable") }}</p>
              <a
                :href="demoUrl"
                target="_blank"
                rel="noopener noreferrer"
                class="text-primary hover:underline"
              >
                {{ t("book.demo_open_new_tab") }} ↗
              </a>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
