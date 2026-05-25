<script setup lang="ts">
import { apiErrorMessage } from "~/composables/useAuth";

const props = defineProps<{
  /** Card heading (e.g. "Cover" / "Book PDF"). */
  title: string;
  /** Sub-text under the heading. */
  hint?: string;
  /** Current URL the backend has — if set, we render a preview/link. */
  url?: string | null;
  /** `image` renders a thumbnail; `pdf` renders an icon + filename. */
  variant?: "image" | "pdf";
  /** Accept attribute for the file picker, e.g. ``image/jpeg,image/png`` or ``application/pdf``. */
  accept: string;
  /** Max upload size (MB) — checked before the network call. */
  maxSizeMb: number;
  /** API endpoint relative to the API base, e.g. `/books/{id}/cover`. */
  endpoint: string;
  /** When true the picker is disabled (book in wrong status). */
  readOnly?: boolean;
}>();

const emit = defineEmits<{
  /** New URL the backend stored. */
  uploaded: [url: string];
}>();

const { t } = useI18n();
const api = useApi();
const toast = useToast();

const fileInput = ref<HTMLInputElement | null>(null);
const uploading = ref(false);
const error = ref<string | null>(null);

function trigger() {
  if (props.readOnly || uploading.value) return;
  fileInput.value?.click();
}

async function onPick(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;

  error.value = null;

  if (file.size > props.maxSizeMb * 1024 * 1024) {
    error.value = t("account_books.upload.size_too_large");
    input.value = "";
    return;
  }
  if (props.accept && !props.accept.split(",").some((a) => file.type.match(a.trim()))) {
    error.value = t("account_books.upload.wrong_type");
    input.value = "";
    return;
  }

  uploading.value = true;
  try {
    const fd = new FormData();
    fd.append("file", file);
    const res = await api<{ cover_url?: string; file_url?: string } & Record<string, unknown>>(
      props.endpoint,
      { method: "POST", body: fd },
    );
    const next = (res?.cover_url || res?.file_url || "") as string;
    if (next) emit("uploaded", next);
  }
  catch (err) {
    error.value = apiErrorMessage(err, t("account_books.upload.upload_failed"));
    toast.error(error.value);
  }
  finally {
    uploading.value = false;
    input.value = "";
  }
}

const isImage = computed(() => props.variant !== "pdf");
const hasFile = computed(() => Boolean(props.url));
</script>

<template>
  <div class="rounded-md border border-border bg-bg-card p-4 space-y-3">
    <header class="flex items-start justify-between gap-3">
      <div class="min-w-0">
        <h3 class="font-medium text-ink">{{ title }}</h3>
        <p v-if="hint" class="text-xs text-ink-tertiary mt-0.5">{{ hint }}</p>
      </div>
      <span
        class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium shrink-0"
        :class="hasFile
          ? 'bg-success/10 text-success'
          : 'bg-bg-secondary text-ink-tertiary'"
      >
        <Icon :name="hasFile ? 'check' : 'inbox'" class="h-3 w-3" />
        {{ hasFile ? t("account_books.upload.uploaded") : t("account_books.upload.no_file") }}
      </span>
    </header>

    <div class="flex items-center gap-3">
      <div
        v-if="isImage"
        class="h-20 w-16 rounded border border-border bg-bg-secondary overflow-hidden shrink-0 flex items-center justify-center"
      >
        <img v-if="url" :src="url" :alt="title" class="h-full w-full object-cover" >
        <Icon v-else name="book" class="h-6 w-6 text-ink-tertiary" />
      </div>
      <div
        v-else
        class="h-12 w-12 rounded border border-border bg-bg-secondary shrink-0 flex items-center justify-center"
      >
        <Icon :name="hasFile ? 'document' : 'inbox'" class="h-5 w-5" :class="hasFile ? 'text-primary' : 'text-ink-tertiary'" />
      </div>

      <div class="flex-1 flex flex-wrap items-center gap-2">
        <UiButton
          v-if="!readOnly"
          size="sm"
          variant="ghost"
          :loading="uploading"
          :disabled="uploading"
          @click="trigger"
        >
          <Icon name="upload" class="h-4 w-4" />
          {{ hasFile ? t("account_books.upload.replace_file") : t("account_books.upload.select_file") }}
        </UiButton>
        <a
          v-if="hasFile && url"
          :href="url"
          target="_blank"
          rel="noopener noreferrer"
          class="inline-flex items-center gap-1 text-xs text-primary hover:underline"
        >
          <Icon name="external-link" class="h-3 w-3" />
          {{ t("account_books.upload.view") }}
        </a>
      </div>
    </div>

    <p v-if="error" class="flex items-center gap-1.5 text-xs text-error">
      <Icon name="warning-solid" class="h-3.5 w-3.5" />
      {{ error }}
    </p>

    <input
      ref="fileInput"
      type="file"
      :accept="accept"
      class="sr-only"
      @change="onPick"
    >
  </div>
</template>
