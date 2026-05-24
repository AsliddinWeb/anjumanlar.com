<script setup lang="ts">
const { toasts, dismiss } = useToast();

const toneClass: Record<string, string> = {
  success: "border-success/30 bg-success/10 text-success",
  error: "border-error/30 bg-error/10 text-error",
  warning: "border-warning/30 bg-warning/10 text-warning",
  info: "border-info/30 bg-info/10 text-info",
};
</script>

<template>
  <Teleport to="body">
    <TransitionGroup
      tag="div"
      name="toast"
      class="fixed bottom-4 right-4 z-[100] flex flex-col items-end gap-2 pointer-events-none"
    >
      <div
        v-for="t in toasts"
        :key="t.id"
        class="pointer-events-auto w-80 max-w-[calc(100vw-2rem)] rounded-md border bg-bg-elevated shadow-lg overflow-hidden"
        role="status"
        :aria-live="t.tone === 'error' ? 'assertive' : 'polite'"
      >
        <div class="flex items-start gap-3 p-3" :class="toneClass[t.tone]">
          <Icon v-if="t.icon" :name="t.icon" class="h-5 w-5 mt-0.5 shrink-0" />
          <div class="flex-1 min-w-0">
            <p v-if="t.title" class="font-medium text-sm leading-tight">
              {{ t.title }}
            </p>
            <p class="text-sm text-ink-secondary leading-snug">
              {{ t.message }}
            </p>
          </div>
          <button
            type="button"
            class="shrink-0 -m-1 p-1 rounded text-ink-tertiary hover:text-ink hover:bg-bg-secondary"
            aria-label="Close"
            @click="dismiss(t.id)"
          >
            <Icon name="close" class="h-4 w-4" />
          </button>
        </div>
      </div>
    </TransitionGroup>
  </Teleport>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 200ms ease;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(20px);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(20px);
}
</style>
