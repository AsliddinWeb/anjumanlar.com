<script setup lang="ts">
/**
 * Client-only PDF reader for owned books.
 *
 * The PDF is streamed through an authenticated backend endpoint
 * (`/libraries/me/{book_id}/stream`) so the underlying MinIO URL never
 * leaves the server. PDF.js renders each page to a canvas, which means:
 *
 *  - The browser never offers a "save as" dialog.
 *  - There is no <object>/<iframe>/<embed> tag a determined user can
 *    right-click to download the raw PDF.
 *  - Text-selection + native context menu are disabled at the canvas
 *    level so casual scraping pulls images instead of plain text.
 *
 * Someone with browser devtools can still extract page images one by
 * one; the email watermark (added by the backend Celery task) is what
 * carries chain-of-custody when that happens. The viewer's job is to
 * raise the bar for casual leakage, not implement DRM.
 */
import type { PDFDocumentProxy } from "pdfjs-dist";
import { apiErrorMessage } from "~/composables/useAuth";

const props = defineProps<{
  bookId: string;
  title?: string;
}>();

const { t } = useI18n();
const runtime = useRuntimeConfig();
const { accessToken } = useAuth();

const apiBase = computed(() => {
  const base = (runtime.public.apiBase as string) || "/api/v1";
  return base.replace(/\/$/, "");
});
const streamUrl = computed(() => `${apiBase.value}/libraries/me/${props.bookId}/stream`);

const status = ref<"idle" | "loading" | "ready" | "error">("idle");
const errorMessage = ref<string>("");

const pdfDoc = ref<PDFDocumentProxy | null>(null);
const totalPages = ref(0);
const currentPage = ref(1);
const scale = ref(1.25);
const canvasRef = ref<HTMLCanvasElement | null>(null);

const containerRef = ref<HTMLDivElement | null>(null);

let renderTask: { cancel: () => void } | null = null;

async function loadDocument() {
  status.value = "loading";
  errorMessage.value = "";

  try {
    const { getDocument, GlobalWorkerOptions } = await import("pdfjs-dist");
    // The worker ships as an ESM bundle next to the main entry. Vite
    // rewrites the ?url import to a hashed asset path at build time.
    const workerSrc = (await import("pdfjs-dist/build/pdf.worker.min.mjs?url")).default;
    GlobalWorkerOptions.workerSrc = workerSrc;

    const headers: Record<string, string> = {};
    if (accessToken.value) headers.Authorization = `Bearer ${accessToken.value}`;

    const response = await fetch(streamUrl.value, {
      credentials: "include",
      headers,
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.arrayBuffer();
    const loadingTask = getDocument({ data });
    const doc = await loadingTask.promise;
    pdfDoc.value = doc;
    totalPages.value = doc.numPages;
    currentPage.value = 1;
    status.value = "ready";
    await nextTick();
    await renderCurrent();
  }
  catch (err) {
    status.value = "error";
    errorMessage.value = apiErrorMessage(err, t("library.reader.load_failed"));
  }
}

async function renderCurrent() {
  if (!pdfDoc.value || !canvasRef.value) return;
  if (renderTask) {
    try { renderTask.cancel(); }
    catch { /* prior task already finished */ }
    renderTask = null;
  }

  const page = await pdfDoc.value.getPage(currentPage.value);
  const viewport = page.getViewport({ scale: scale.value });
  const canvas = canvasRef.value;
  const context = canvas.getContext("2d");
  if (!context) return;

  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.floor(viewport.width * dpr);
  canvas.height = Math.floor(viewport.height * dpr);
  canvas.style.width = `${Math.floor(viewport.width)}px`;
  canvas.style.height = `${Math.floor(viewport.height)}px`;
  context.setTransform(dpr, 0, 0, dpr, 0, 0);

  renderTask = page.render({ canvasContext: context, viewport });
  await (renderTask as unknown as { promise: Promise<void> }).promise;
}

function goPrev() {
  if (currentPage.value <= 1) return;
  currentPage.value -= 1;
  void renderCurrent();
}
function goNext() {
  if (currentPage.value >= totalPages.value) return;
  currentPage.value += 1;
  void renderCurrent();
}
function jumpTo(p: number) {
  const target = Math.min(Math.max(1, Math.floor(p)), totalPages.value);
  if (target === currentPage.value) return;
  currentPage.value = target;
  void renderCurrent();
}

function zoomIn() {
  scale.value = Math.min(3, Math.round((scale.value + 0.25) * 100) / 100);
  void renderCurrent();
}
function zoomOut() {
  scale.value = Math.max(0.5, Math.round((scale.value - 0.25) * 100) / 100);
  void renderCurrent();
}

function onKeydown(e: KeyboardEvent) {
  if (e.target instanceof HTMLInputElement) return;
  if (e.key === "ArrowRight" || e.key === "PageDown") {
    e.preventDefault();
    goNext();
  }
  else if (e.key === "ArrowLeft" || e.key === "PageUp") {
    e.preventDefault();
    goPrev();
  }
}

function preventContext(e: Event) {
  e.preventDefault();
}

onMounted(() => {
  window.addEventListener("keydown", onKeydown);
  void loadDocument();
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", onKeydown);
  if (renderTask) {
    try { renderTask.cancel(); }
    catch { /* ignore */ }
  }
  if (pdfDoc.value) {
    void pdfDoc.value.destroy();
  }
});
</script>

<template>
  <div ref="containerRef" class="bg-bg-secondary/40 rounded-md border border-border overflow-hidden">
    <!-- Toolbar -->
    <div class="flex items-center justify-between gap-3 px-3 py-2 border-b border-border bg-bg-card flex-wrap">
      <div class="flex items-center gap-1">
        <UiButton size="sm" variant="ghost" :disabled="currentPage <= 1 || status !== 'ready'" @click="goPrev">
          <Icon name="arrow-left" class="h-4 w-4" />
        </UiButton>
        <input
          type="number"
          min="1"
          :max="totalPages || 1"
          :value="currentPage"
          class="w-14 px-1.5 py-1 rounded border border-border bg-bg text-center text-sm tabular-nums"
          @change="jumpTo(Number(($event.target as HTMLInputElement).value))"
        >
        <span class="text-xs text-ink-tertiary tabular-nums">/ {{ totalPages || "—" }}</span>
        <UiButton size="sm" variant="ghost" :disabled="currentPage >= totalPages || status !== 'ready'" @click="goNext">
          <Icon name="arrow-right" class="h-4 w-4" />
        </UiButton>
      </div>
      <div class="flex items-center gap-1">
        <UiButton size="sm" variant="ghost" :disabled="status !== 'ready'" @click="zoomOut">
          <Icon name="close" class="h-3.5 w-3.5" />
        </UiButton>
        <span class="text-xs text-ink-tertiary tabular-nums px-2">{{ Math.round(scale * 100) }}%</span>
        <UiButton size="sm" variant="ghost" :disabled="status !== 'ready'" @click="zoomIn">
          <Icon name="plus" class="h-3.5 w-3.5" />
        </UiButton>
      </div>
    </div>

    <!-- Stage -->
    <div
      class="overflow-auto bg-[#525659] flex items-start justify-center p-4 select-none"
      style="min-height: 70vh;"
      @contextmenu="preventContext"
    >
      <div v-if="status === 'loading'" class="text-white/80 py-20">
        {{ t("library.reader.loading") }}
      </div>
      <div v-else-if="status === 'error'" class="text-white/90 py-20 text-center max-w-md">
        <Icon name="warning-solid" class="h-6 w-6 mx-auto mb-2" />
        <p>{{ errorMessage || t("library.reader.load_failed") }}</p>
        <UiButton size="sm" class="mt-3" @click="loadDocument">
          <Icon name="arrow-path" class="h-3.5 w-3.5" />
          {{ t("library.reader.retry") }}
        </UiButton>
      </div>
      <canvas
        v-show="status === 'ready'"
        ref="canvasRef"
        class="shadow-2xl bg-white"
      />
    </div>
  </div>
</template>

<style scoped>
canvas {
  -webkit-user-select: none;
  user-select: none;
  pointer-events: none;
}
</style>
