import { defineStore } from "pinia";
import type { WishlistList } from "~/types/api";

/**
 * Wishlist store — caches book ids the user has wishlisted so heart icons
 * across the catalogue can render the right state without a per-card API
 * call. Mutations optimistically update the local set and roll back on
 * server error.
 *
 * The full enriched list (book payloads + timestamps) is fetched lazily
 * on the dedicated /account/wishlist page; this store only holds the id
 * set + an in-flight loaded flag.
 */
export const useWishlistStore = defineStore("wishlist", () => {
  const ids = ref<Set<string>>(new Set());
  const loaded = ref(false);
  const pending = ref<Set<string>>(new Set());

  function isWishlisted(bookId: string): boolean {
    return ids.value.has(bookId);
  }

  function isPending(bookId: string): boolean {
    return pending.value.has(bookId);
  }

  async function ensureLoaded() {
    if (loaded.value) return;
    const auth = useAuthStore();
    if (!auth.isAuthenticated) {
      loaded.value = true;
      return;
    }
    const api = useApi();
    try {
      const data = await api<WishlistList>("/users/me/wishlist", {
        query: { page_size: 100 },
      });
      ids.value = new Set(data.items.map((it) => it.book.id));
    }
    catch {
      // Silent — the heart just stays unset.
    }
    loaded.value = true;
  }

  async function add(bookId: string) {
    if (pending.value.has(bookId)) return;
    const api = useApi();
    pending.value.add(bookId);
    ids.value.add(bookId);
    try {
      await api(`/users/me/wishlist/${bookId}`, { method: "POST" });
    }
    catch (err) {
      ids.value.delete(bookId);
      throw err;
    }
    finally {
      pending.value.delete(bookId);
    }
  }

  async function remove(bookId: string) {
    if (pending.value.has(bookId)) return;
    const api = useApi();
    pending.value.add(bookId);
    ids.value.delete(bookId);
    try {
      await api(`/users/me/wishlist/${bookId}`, { method: "DELETE" });
    }
    catch (err) {
      ids.value.add(bookId);
      throw err;
    }
    finally {
      pending.value.delete(bookId);
    }
  }

  async function toggle(bookId: string) {
    if (ids.value.has(bookId)) await remove(bookId);
    else await add(bookId);
  }

  function reset() {
    ids.value = new Set();
    loaded.value = false;
    pending.value = new Set();
  }

  return {
    ids,
    loaded,
    pending,
    isWishlisted,
    isPending,
    ensureLoaded,
    add,
    remove,
    toggle,
    reset,
  };
});
