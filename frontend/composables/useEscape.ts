/**
 * Bind a keyboard handler so pressing ``Esc`` calls ``onEscape``. Used
 * by modals + drawers so keyboard users have a non-mouse way out.
 *
 * Registers on ``window`` on mount and tears down on unmount — same
 * lifecycle as the calling component.
 */
export function useEscape(
  onEscape: () => void,
  options: { enabled?: Ref<boolean> | ComputedRef<boolean> } = {},
) {
  if (!import.meta.client) return;

  function handler(event: KeyboardEvent) {
    if (event.key !== "Escape") return;
    if (options.enabled && options.enabled.value === false) return;
    onEscape();
  }

  onMounted(() => window.addEventListener("keydown", handler));
  onBeforeUnmount(() => window.removeEventListener("keydown", handler));
}
