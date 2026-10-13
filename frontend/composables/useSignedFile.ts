import { apiErrorMessage } from "~/composables/useAuth";

/**
 * Opens a private-bucket file (book PDF, review manuscript/response, ...)
 * by first fetching a short-lived signed URL from the backend, then
 * opening that in a new tab — the raw stored URL 403s on its own since
 * these buckets have no public-read policy.
 */
export function useSignedFile() {
  const api = useApi();
  const toast = useToast();
  const { t } = useI18n();
  const opening = ref<string | null>(null);

  async function openSignedFile(endpoint: string, key: string = endpoint) {
    if (opening.value) return;
    opening.value = key;
    try {
      const resp = await api<{ url: string }>(endpoint);
      if (import.meta.client) window.open(resp.url, "_blank", "noopener,noreferrer");
    }
    catch (err) {
      toast.error(apiErrorMessage(err, t("common.error")));
    }
    finally {
      opening.value = null;
    }
  }

  return { opening, openSignedFile };
}
