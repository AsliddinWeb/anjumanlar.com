<script setup lang="ts">
import type { IconName } from "~/utils/icons";

export interface ActionItem {
  key: string;
  label: string;
  icon?: IconName;
  to?: string;
  /** When true the item is rendered in error tone. */
  danger?: boolean;
  /** When true, renders a divider above this item. */
  divider?: boolean;
  disabled?: boolean;
}

defineProps<{
  items: ActionItem[];
}>();

const emit = defineEmits<{ action: [key: string] }>();

const open = ref(false);
const root = ref<HTMLElement | null>(null);

function onDocumentClick(event: MouseEvent) {
  if (!open.value || !root.value) return;
  if (!root.value.contains(event.target as Node)) {
    open.value = false;
  }
}

onMounted(() => {
  if (import.meta.client) document.addEventListener("mousedown", onDocumentClick);
});

onBeforeUnmount(() => {
  if (import.meta.client) document.removeEventListener("mousedown", onDocumentClick);
});

function select(item: ActionItem) {
  if (item.disabled) return;
  open.value = false;
  if (!item.to) emit("action", item.key);
}
</script>

<template>
  <div ref="root" class="relative inline-block">
    <button
      type="button"
      class="inline-flex items-center justify-center h-8 w-8 rounded text-ink-tertiary hover:bg-bg-secondary hover:text-ink transition-colors"
      :aria-expanded="open"
      aria-label="Actions"
      @click.stop="open = !open"
    >
      <Icon name="settings" class="h-4 w-4" />
    </button>

    <Transition
      enter-active-class="transition duration-100 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
    >
      <ul
        v-if="open"
        class="absolute right-0 mt-1 min-w-44 rounded-md border border-border bg-bg-elevated shadow-lg py-1 text-sm z-20"
        role="menu"
      >
        <template v-for="item in items" :key="item.key">
          <li v-if="item.divider" role="separator" class="my-1 border-t border-border" />
          <li>
            <NuxtLink
              v-if="item.to"
              :to="item.to"
              class="flex items-center gap-2 px-3 py-1.5"
              :class="item.danger
                ? 'text-error hover:bg-error/5'
                : 'text-ink-secondary hover:bg-bg-secondary hover:text-ink'"
              role="menuitem"
              @click="open = false"
            >
              <Icon v-if="item.icon" :name="item.icon" class="h-4 w-4" />
              {{ item.label }}
            </NuxtLink>
            <button
              v-else
              type="button"
              :disabled="item.disabled"
              class="flex items-center gap-2 w-full text-left px-3 py-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
              :class="item.danger
                ? 'text-error hover:bg-error/5'
                : 'text-ink-secondary hover:bg-bg-secondary hover:text-ink'"
              role="menuitem"
              @click="select(item)"
            >
              <Icon v-if="item.icon" :name="item.icon" class="h-4 w-4" />
              {{ item.label }}
            </button>
          </li>
        </template>
      </ul>
    </Transition>
  </div>
</template>
