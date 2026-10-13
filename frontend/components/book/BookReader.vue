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
  /** Shown as a fallback action in the error state when the book allows it. */
  downloadsEnabled?: boolean;
}>();

const emit = defineEmits<{ download: [] }>();

const { t } = useI18n();
const runtime = useRuntimeConfig();
const { accessToken, refresh } = useAuth();

const apiBase = computed(() => {
  const base = (runtime.public.apiBase as string) || "/api/v1";
  return base.replace(/\/$/, "");
});
const streamUrl = computed(() => `${apiBase.value}/libraries/me/${props.bookId}/stream`);

const status = ref<"idle" | "loading" | "ready" | "error">("idle");
const errorMessage = ref<string>("");
/** "not_ready" gets a friendlier message + an auto-retry instead of a dead end. */
const errorKind = ref<"generic" | "auth" | "not_ready">("generic");

const pdfDoc = ref<PDFDocumentProxy | null>(null);
const totalPages = ref(0);
const currentPage = ref(1);
const scale = ref(1.25);
const canvasRef = ref<HTMLCanvasElement | null>(null);
const isFullscreen = ref(false);
const pageInput = ref("1");

const containerRef = ref<HTMLDivElement | null>(null);
const stageRef = ref<HTMLDivElement | null>(null);

let renderTask: { cancel: () => void } | null = null;
let notReadyRetryTimer: ReturnType<typeof setTimeout> | null = null;

async function fetchPdfBytes(): Promise<ArrayBuffer> {
  const headers: Record<string, string> = {};
  if (accessToken.value) headers.Authorization = `Bearer ${accessToken.value}`;

  let response = await fetch(streamUrl.value, { credentials: "include", headers });

  // The access token lives 30 minutes; a reader who's been browsing
  // longer than that will have a stale one by the time they click
  // "read". useApi()'s callers each handle 401 themselves (no global
  // refresh-and-retry yet) — this is that handling for the reader.
  if (response.status === 401) {
    const refreshed = await refresh();
    if (refreshed && accessToken.value) {
      response = await fetch(streamUrl.value, {
        credentials: "include",
        headers: { Authorization: `Bearer ${accessToken.value}` },
      });
    }
  }

  if (!response.ok) {
    const err = new Error(`HTTP ${response.status}`) as Error & { status?: number };
    err.status = response.status;
    throw err;
  }
  return response.arrayBuffer();
}

async function loadDocument() {
  if (notReadyRetryTimer) {
    clearTimeout(notReadyRetryTimer);
    notReadyRetryTimer = null;
  }
  status.value = "loading";
  errorMessage.value = "";
  errorKind.value = "generic";

  try {
    const { getDocument, GlobalWorkerOptions } = await import("pdfjs-dist");
    // The worker ships as an ESM bundle next to the main entry. Vite
    // rewrites the ?url import to a hashed asset path at build time.
    const workerSrc = (await import("pdfjs-dist/build/pdf.worker.min.mjs?url")).default;
    GlobalWorkerOptions.workerSrc = workerSrc;

    const data = await fetchPdfBytes();
    const loadingTask = getDocument({ data });
    const doc = await loadingTask.promise;
    pdfDoc.value = doc;
    totalPages.value = doc.numPages;
    currentPage.value = 1;
    pageInput.value = "1";
    status.value = "ready";
    await nextTick();
    await renderCurrent();
  }
  catch (err) {
    status.value = "error";
    const httpStatus = (err as { status?: number } | null)?.status;
    if (httpStatus === 401) {
      errorKind.value = "auth";
      errorMessage.value = t("library.reader.session_expired");
    }
    else if (httpStatus === 404) {
      // Watermarking runs async right after purchase — a freshly bought
      // book can land here for a few seconds. Worth one quiet auto-retry
      // before treating it as a real failure.
      errorKind.value = "not_ready";
      errorMessage.value = t("library.reader.not_ready");
      notReadyRetryTimer = setTimeout(() => void loadDocument(), 6000);
    }
    else {
      errorKind.value = "generic";
      errorMessage.value = apiErrorMessage(err, t("library.reader.load_failed"));
    }
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
  pageInput.value = String(currentPage.value);
  void renderCurrent();
}
function goNext() {
  if (currentPage.value >= totalPages.value) return;
  currentPage.value += 1;
  pageInput.value = String(currentPage.value);
  void renderCurrent();
}
function jumpTo(p: number) {
  if (!Number.isFinite(p)) { pageInput.value = String(currentPage.value); return; }
  const target = Math.min(Math.max(1, Math.floor(p)), totalPages.value || 1);
  pageInput.value = String(target);
  if (target === currentPage.value) return;
  currentPage.value = target;
  void renderCurrent();
}

const progressPercent = computed(() =>
  totalPages.value > 0 ? Math.round((currentPage.value / totalPages.value) * 100) : 0,
);

function zoomIn() {
  scale.value = Math.min(3, Math.round((scale.value + 0.25) * 100) / 100);
  void renderCurrent();
}
function zoomOut() {
  scale.value = Math.max(0.5, Math.round((scale.value - 0.25) * 100) / 100);
  void renderCurrent();
}

async function toggleFullscreen() {
  if (!containerRef.value) return;
  try {
    if (!document.fullscreenElement) {
      await containerRef.value.requestFullscreen();
      isFullscreen.value = true;
    }
    else {
      await document.exitFullscreen();
      isFullscreen.value = false;
    }
  }
  catch { /* some mobile browsers refuse fullscreen — not fatal */ }
}
function onFullscreenChange() {
  isFullscreen.value = document.fullscreenElement === containerRef.value;
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
  else if (e.key === "Escape" && isFullscreen.value) {
    void toggleFullscreen();
  }
}

function preventContext(e: Event) {
  e.preventDefault();
}

// --- touch swipe (mobile page turning) ---
let touchStartX = 0;
let touchStartY = 0;
const SWIPE_MIN_DISTANCE = 50;

function onTouchStart(e: TouchEvent) {
  const t0 = e.touches[0];
  if (!t0) return;
  touchStartX = t0.clientX;
  touchStartY = t0.clientY;
}
function onTouchEnd(e: TouchEvent) {
  const t0 = e.changedTouches[0];
  if (!t0) return;
  const dx = t0.clientX - touchStartX;
  const dy = t0.clientY - touchStartY;
  if (Math.abs(dx) < SWIPE_MIN_DISTANCE || Math.abs(dx) < Math.abs(dy)) return;
  if (dx < 0) goNext();
  else goPrev();
}

onMounted(() => {
  window.addEventListener("keydown", onKeydown);
  document.addEventListener("fullscreenchange", onFullscreenChange);
  void loadDocument();
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", onKeydown);
  document.removeEventListener("fullscreenchange", onFullscreenChange);
  if (notReadyRetryTimer) clearTimeout(notReadyRetryTimer);
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
  <div
    ref="containerRef"
    class="bg-bg-secondary/40 rounded-md border border-border overflow-hidden"
    :class="isFullscreen ? 'fixed inset-0 z-50 rounded-none border-0' : ''"
  >
    <!-- Toolbar -->
    <div class="flex items-center justify-between gap-2 px-2 sm:px-3 py-2 border-b border-border bg-bg-card flex-wrap">
      <div class="flex items-center gap-1">
        <UiButton
          size="sm"
          variant="ghost"
          :disabled="currentPage <= 1 || status !== 'ready'"
          :aria-label="t('library.reader.prev_page')"
          @click="goPrev"
        >
          <Icon name="arrow-left" class="h-4 w-4" />
        </UiButton>
        <input
          v-model="pageInput"
          type="number"
          min="1"
          :max="totalPages || 1"
          :disabled="status !== 'ready'"
          class="w-12 sm:w-14 px-1.5 py-1 rounded border border-border bg-bg text-center text-sm tabular-nums disabled:opacity-50"
          :aria-label="t('library.reader.page_number')"
          @change="jumpTo(Number(pageInput))"
          @keydown.enter="jumpTo(Number(pageInput))"
        >
        <span class="text-xs text-ink-tertiary tabular-nums shrink-0">/ {{ totalPages || "—" }}</span>
        <UiButton
          size="sm"
          variant="ghost"
          :disabled="currentPage >= totalPages || status !== 'ready'"
          :aria-label="t('library.reader.next_page')"
          @click="goNext"
        >
          <Icon name="arrow-right" class="h-4 w-4" />
        </UiButton>
      </div>
      <div class="flex items-center gap-1">
        <UiButton size="sm" variant="ghost" :disabled="status !== 'ready'" :aria-label="t('library.reader.zoom_out')" @click="zoomOut">
          <Icon name="minus" class="h-3.5 w-3.5" />
        </UiButton>
        <span class="text-xs text-ink-tertiary tabular-nums px-1 w-11 text-center shrink-0">{{ Math.round(scale * 100) }}%</span>
        <UiButton size="sm" variant="ghost" :disabled="status !== 'ready'" :aria-label="t('library.reader.zoom_in')" @click="zoomIn">
          <Icon name="plus" class="h-3.5 w-3.5" />
        </UiButton>
        <span class="w-px h-5 bg-border mx-1 hidden sm:block" />
        <UiButton
          size="sm"
          variant="ghost"
          class="hidden sm:inline-flex"
          :disabled="status !== 'ready'"
          :aria-label="isFullscreen ? t('library.reader.exit_fullscreen') : t('library.reader.enter_fullscreen')"
          @click="toggleFullscreen"
        >
          <Icon :name="isFullscreen ? 'fullscreen-exit' : 'fullscreen'" class="h-3.5 w-3.5" />
        </UiButton>
      </div>
    </div>

    <!-- Progress bar -->
    <div v-if="status === 'ready'" class="h-1 bg-border/60">
      <div
        class="h-full bg-primary transition-all duration-200"
        :style="{ width: `${progressPercent}%` }"
      />
    </div>

    <!-- Stage -->
    <div
      ref="stageRef"
      class="overflow-auto bg-[#525659] flex items-start justify-center p-2 sm:p-4 select-none"
      :class="isFullscreen ? 'h-[calc(100vh-41px)]' : ''"
      style="min-height: 60vh;"
      @contextmenu="preventContext"
      @touchstart.passive="onTouchStart"
      @touchend.passive="onTouchEnd"
    >
      <!-- Loading -->
      <div v-if="status === 'loading'" class="flex flex-col items-center gap-3 py-24 text-white/80">
        <svg class="h-8 w-8 animate-spin" viewBox="0 0 24 24" fill="none">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
          <path class="opacity-80" fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" />
        </svg>
        <span class="text-sm">{{ t("library.reader.loading") }}</span>
      </div>

      <!-- Error -->
      <div v-else-if="status === 'error'" class="text-white/90 py-16 text-center max-w-sm px-4">
        <Icon
          :name="errorKind === 'not_ready' ? 'arrow-path' : 'warning-solid'"
          class="h-7 w-7 mx-auto mb-3"
          :class="errorKind === 'not_ready' ? 'animate-spin text-white/60' : 'text-warning'"
        />
        <p class="text-sm leading-relaxed">{{ errorMessage || t("library.reader.load_failed") }}</p>
        <div class="flex items-center justify-center gap-2 mt-4 flex-wrap">
          <UiButton v-if="errorKind !== 'not_ready'" size="sm" @click="loadDocument">
            <Icon name="arrow-path" class="h-3.5 w-3.5" />
            {{ t("library.reader.retry") }}
          </UiButton>
          <UiButton v-if="downloadsEnabled" size="sm" variant="ghost" @click="emit('download')">
            <Icon name="upload" class="h-3.5 w-3.5 rotate-180" />
            {{ t("library.reader.download") }}
          </UiButton>
        </div>
      </div>

      <canvas
        v-show="status === 'ready'"
        ref="canvasRef"
        class="shadow-2xl bg-white"
      />
    </div>

    <!-- Mobile hint -->
    <p v-if="status === 'ready'" class="sm:hidden text-center text-[11px] text-ink-tertiary py-1.5 bg-bg-card border-t border-border">
      {{ t("library.reader.swipe_hint") }}
    </p>
  </div>
</template>

<style scoped>
canvas {
  -webkit-user-select: none;
  user-select: none;
  pointer-events: none;
}
</style>
