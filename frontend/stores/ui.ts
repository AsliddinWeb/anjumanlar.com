import { defineStore } from "pinia";

/**
 * UI store — non-route UI state (sidebar/drawer open, toast queue, …).
 * Theme + locale live in their respective Nuxt modules; we don't duplicate
 * that state here.
 */
export const useUiStore = defineStore("ui", () => {
  const mobileMenuOpen = ref(false);

  function toggleMobileMenu() {
    mobileMenuOpen.value = !mobileMenuOpen.value;
  }

  return { mobileMenuOpen, toggleMobileMenu };
});
