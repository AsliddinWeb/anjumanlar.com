import type { IconName } from "~/components/ui/Icon.vue";

export type ToastTone = "success" | "error" | "warning" | "info";

export interface Toast {
  id: number;
  tone: ToastTone;
  title?: string;
  message: string;
  icon?: IconName;
  timeout: number;
}

const TONE_ICON: Record<ToastTone, IconName> = {
  success: "check-circle-solid",
  error: "warning-solid",
  warning: "warning-solid",
  info: "sparkles",
};

let nextId = 1;

export function useToast() {
  const toasts = useState<Toast[]>("admin-toasts", () => []);

  function dismiss(id: number) {
    toasts.value = toasts.value.filter((t) => t.id !== id);
  }

  function push(input: Omit<Toast, "id" | "icon" | "timeout"> & {
    icon?: IconName;
    timeout?: number;
  }) {
    const id = nextId++;
    const timeout = input.timeout ?? 4000;
    const toast: Toast = {
      id,
      tone: input.tone,
      title: input.title,
      message: input.message,
      icon: input.icon ?? TONE_ICON[input.tone],
      timeout,
    };
    toasts.value = [...toasts.value, toast];
    if (timeout > 0 && import.meta.client) {
      window.setTimeout(() => dismiss(id), timeout);
    }
    return id;
  }

  return {
    toasts,
    dismiss,
    push,
    success: (message: string, title?: string) => push({ tone: "success", message, title }),
    error: (message: string, title?: string) => push({ tone: "error", message, title }),
    warning: (message: string, title?: string) => push({ tone: "warning", message, title }),
    info: (message: string, title?: string) => push({ tone: "info", message, title }),
  };
}
