/**
 * After auth bootstrap, load the wishlist id set so heart icons start in
 * the right state. Also keep it in sync when the user logs in/out at
 * runtime — toggling auth without reloading the page would otherwise
 * leave stale ids around.
 */
export default defineNuxtPlugin(async () => {
  const auth = useAuthStore();
  const wishlist = useWishlistStore();

  if (auth.isAuthenticated) {
    await wishlist.ensureLoaded();
  }

  watch(
    () => auth.isAuthenticated,
    async (now, before) => {
      if (now && !before) {
        wishlist.reset();
        await wishlist.ensureLoaded();
      }
      else if (!now && before) {
        wishlist.reset();
      }
    },
  );
});
