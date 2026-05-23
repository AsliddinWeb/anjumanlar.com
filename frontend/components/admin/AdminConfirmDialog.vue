<script setup lang="ts">
import type { IconName } from "~/components/ui/Icon.vue";

const props = withDefaults(
  defineProps<{
    open: boolean;
    title: string;
    description?: string;
    /** What the user is about to do. Buttons reflect this tone. */
    tone?: "primary" | "danger" | "warning";
    icon?: IconName;
    confirmLabel?: string;
    cancelLabel?: string;
    loading?: boolean;
    /** When true, the confirm button is disabled. */
    disabled?: boolean;
  }>(),
  { tone: "primary" },
);

const emit = defineEmits<{
  "update:open": [value: boolean];
  "confirm": [];
  "cancel": [];
}>();

const isOpen = computed(() => props.open);

useEscape(() => {
  if (props.open && !props.loading) {
    emit("update:open", false);
    emit("cancel");
  }
}, { enabled: isOpen });

watch(
  () => props.open,
  (open) => {
    if (!import.meta.client) return;
    document.body.style.overflow = open ? "hidden" : "";
  },
);

onBeforeUnmount(() => {
  if (import.meta.client) document.body.style.overflow = "";
});

const toneIconClass = computed(() => {
  if (props.tone === "danger") return "bg-error/10 text-error";
  if (props.tone === "warning") return "bg-warning/10 text-warning";
  return "bg-primary/10 text-primary";
});

const confirmVariant = computed<"primary" | "danger">(() =>
  props.tone === "danger" ? "danger" : "primary",
);

function onBackdrop() {
  if (props.loading) return;
  emit("update:open", false);
  emit("cancel");
}

function onCancel() {
  if (props.loading) return;
  emit("update:open", false);
  emit("cancel");
}

function onConfirm() {
  if (props.disabled || props.loading) return;
  emit("confirm");
}
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-100 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="open"
        class="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="`confirm-title`"
        @click.self="onBackdrop"
      >
        <Transition
          appear
          enter-active-class="transition duration-200 ease-out"
          enter-from-class="opacity-0 scale-95"
          enter-to-class="opacity-100 scale-100"
        >
          <div class="w-full max-w-md rounded-lg bg-bg-elevated border border-border shadow-2xl overflow-hidden">
            <header class="flex items-start gap-3 p-5 pb-4">
              <div
                v-if="icon"
                class="h-10 w-10 rounded-full flex items-center justify-center shrink-0"
                :class="toneIconClass"
              >
                <Icon :name="icon" class="h-5 w-5" />
              </div>
              <div class="flex-1 min-w-0">
                <h3 id="confirm-title" class="font-serif text-lg text-ink leading-snug">
                  {{ title }}
                </h3>
                <p v-if="description" class="text-sm text-ink-secondary mt-1 leading-relaxed">
                  {{ description }}
                </p>
              </div>
            </header>

            <div v-if="$slots.default" class="px-5 pb-2">
              <slot />
            </div>

            <footer class="flex items-center justify-end gap-2 px-5 py-4 bg-bg-secondary/40 border-t border-border">
              <UiButton variant="ghost" size="sm" :disabled="loading" @click="onCancel">
                {{ cancelLabel ?? "Cancel" }}
              </UiButton>
              <UiButton
                :variant="confirmVariant"
                size="sm"
                :loading="loading"
                :disabled="disabled || loading"
                @click="onConfirm"
              >
                {{ confirmLabel ?? "Confirm" }}
              </UiButton>
            </footer>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
