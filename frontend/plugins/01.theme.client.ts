/**
 * Apply the active site theme on app start.
 *
 * Two-stage to avoid a "flash of default" on themes other than classic:
 *   1. Immediately read the cached value from localStorage and apply it
 *      so the page paints with the right palette on first frame.
 *   2. Refresh from /settings in the background — that's the source of
 *      truth and corrects the local cache if the admin changed the
 *      theme on another device.
 */
export default defineNuxtPlugin(() => {
  const theme = useTheme();
  theme.loadFromCache();
  void theme.loadFromServer();
});
