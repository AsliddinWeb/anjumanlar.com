/**
 * Theme registry — each entry maps an admin-selectable name to the
 * concrete CSS variable values applied on :root.
 *
 * The current ``classic`` palette mirrors the values shipped in
 * ``assets/css/main.css``. Switching to another theme calls
 * ``applyTheme(name)`` (see ``composables/useTheme.ts``) which writes
 * each `--color-*` to ``document.documentElement.style``.
 *
 * Adding a theme:
 *   1. Add a new entry below with the full set of tokens.
 *   2. Optionally add a labelKey/descriptionKey if you want i18n.
 *   3. Restart the dev server only if the registry got a new key —
 *      values are read at runtime so a hot-reload picks them up.
 */

export interface ThemePalette {
  // Brand
  primary: string;
  primaryHover: string;
  primaryLight: string;
  // Accents
  accentGold: string;
  accentBurgundy: string;
  accentForest: string;
  // Backgrounds
  bg: string;
  bgSecondary: string;
  bgCard: string;
  bgElevated: string;
  // Text
  textPrimary: string;
  textSecondary: string;
  textTertiary: string;
  textInverse: string;
  // Borders
  border: string;
  borderHover: string;
  // Feedback (kept consistent across themes for accessibility)
  success: string;
  warning: string;
  error: string;
  info: string;
}

export interface ThemeDefinition {
  name: string;
  label: string;
  description: string;
  palette: ThemePalette;
}

export const THEMES: Record<string, ThemeDefinition> = {
  classic: {
    name: "classic",
    label: "Klassik",
    description: "Issiq qog'oz va siyoh — kutubxona muhiti",
    palette: {
      primary: "#8b4513",
      primaryHover: "#6b3410",
      primaryLight: "#d2691e",
      accentGold: "#c9a961",
      accentBurgundy: "#722f37",
      accentForest: "#2d5016",
      bg: "#faf7f2",
      bgSecondary: "#f5f0e8",
      bgCard: "#ffffff",
      bgElevated: "#ffffff",
      textPrimary: "#1a1410",
      textSecondary: "#4a3f35",
      textTertiary: "#8b7e70",
      textInverse: "#faf7f2",
      border: "#e8dfd0",
      borderHover: "#d4c5a9",
      success: "#2d5016",
      warning: "#b8860b",
      error: "#8b0000",
      info: "#4682b4",
    },
  },
  royal: {
    name: "royal",
    label: "Royal Blue",
    description: "Akademik nayv — diqqat va ishonch",
    palette: {
      primary: "#1e3a8a",
      primaryHover: "#172e6f",
      primaryLight: "#3b5fc9",
      accentGold: "#d4af37",
      accentBurgundy: "#7c2d12",
      accentForest: "#166534",
      bg: "#f8fafc",
      bgSecondary: "#f1f5f9",
      bgCard: "#ffffff",
      bgElevated: "#ffffff",
      textPrimary: "#0f172a",
      textSecondary: "#334155",
      textTertiary: "#64748b",
      textInverse: "#f8fafc",
      border: "#e2e8f0",
      borderHover: "#cbd5e1",
      success: "#166534",
      warning: "#b45309",
      error: "#b91c1c",
      info: "#1e3a8a",
    },
  },
  midnight: {
    name: "midnight",
    label: "Midnight",
    description: "Tungi rejim — tilla aksentlar bilan",
    palette: {
      primary: "#d4af37",
      primaryHover: "#b8941f",
      primaryLight: "#e8c554",
      accentGold: "#d4af37",
      accentBurgundy: "#a04050",
      accentForest: "#4a7c2a",
      bg: "#0a0a0f",
      bgSecondary: "#13131a",
      bgCard: "#1c1c25",
      bgElevated: "#24242f",
      textPrimary: "#f5f5f0",
      textSecondary: "#c8c8b8",
      textTertiary: "#7f7f70",
      textInverse: "#0a0a0f",
      border: "#2a2a35",
      borderHover: "#3a3a45",
      success: "#4ade80",
      warning: "#fbbf24",
      error: "#f87171",
      info: "#60a5fa",
    },
  },
  forest: {
    name: "forest",
    label: "Forest",
    description: "O'rmon — yashil tabiat tonalligida",
    palette: {
      primary: "#166534",
      primaryHover: "#14532d",
      primaryLight: "#22c55e",
      accentGold: "#ca8a04",
      accentBurgundy: "#9f1239",
      accentForest: "#14532d",
      bg: "#f7faf7",
      bgSecondary: "#eef4ed",
      bgCard: "#ffffff",
      bgElevated: "#ffffff",
      textPrimary: "#14271c",
      textSecondary: "#3f5447",
      textTertiary: "#778880",
      textInverse: "#f7faf7",
      border: "#dde7dd",
      borderHover: "#c5d4c5",
      success: "#166534",
      warning: "#a16207",
      error: "#b91c1c",
      info: "#0e7490",
    },
  },
  cherry: {
    name: "cherry",
    label: "Cherry",
    description: "Vino-kirpich — qadimiy elegant",
    palette: {
      primary: "#9f1239",
      primaryHover: "#7f0d2e",
      primaryLight: "#e11d48",
      accentGold: "#d4a017",
      accentBurgundy: "#7f1d1d",
      accentForest: "#15803d",
      bg: "#fdf8f7",
      bgSecondary: "#faedee",
      bgCard: "#ffffff",
      bgElevated: "#ffffff",
      textPrimary: "#1c0c10",
      textSecondary: "#46282e",
      textTertiary: "#85666d",
      textInverse: "#fdf8f7",
      border: "#ead2d6",
      borderHover: "#d8b6bc",
      success: "#15803d",
      warning: "#b45309",
      error: "#991b1b",
      info: "#1e40af",
    },
  },
  steppe: {
    name: "steppe",
    label: "Steppe",
    description: "Cho'l qum-firuza — Markaziy Osiyo",
    palette: {
      primary: "#0e7490",
      primaryHover: "#155e75",
      primaryLight: "#06b6d4",
      accentGold: "#c9a84c",
      accentBurgundy: "#a16207",
      accentForest: "#166534",
      bg: "#fefcf7",
      bgSecondary: "#fbf5e8",
      bgCard: "#ffffff",
      bgElevated: "#ffffff",
      textPrimary: "#1a1f1d",
      textSecondary: "#3e4a47",
      textTertiary: "#7a8a86",
      textInverse: "#fefcf7",
      border: "#e6dcc6",
      borderHover: "#d4c5a0",
      success: "#166534",
      warning: "#b45309",
      error: "#991b1b",
      info: "#0e7490",
    },
  },
  samarkand: {
    name: "samarkand",
    label: "Samarkand",
    description: "Binafsha-tilla — Samarqand naqshi",
    palette: {
      primary: "#5b21b6",
      primaryHover: "#4c1d95",
      primaryLight: "#8b5cf6",
      accentGold: "#d4af37",
      accentBurgundy: "#7c2d12",
      accentForest: "#166534",
      bg: "#faf8fd",
      bgSecondary: "#f3edfb",
      bgCard: "#ffffff",
      bgElevated: "#ffffff",
      textPrimary: "#1a0f2e",
      textSecondary: "#3d2e5c",
      textTertiary: "#7d6e9c",
      textInverse: "#faf8fd",
      border: "#e6dbf2",
      borderHover: "#cfbde5",
      success: "#15803d",
      warning: "#b45309",
      error: "#b91c1c",
      info: "#1e40af",
    },
  },
  bukhara: {
    name: "bukhara",
    label: "Bukhara",
    description: "Zumrad-tilla — Buxoro klassikasi",
    palette: {
      primary: "#047857",
      primaryHover: "#065f46",
      primaryLight: "#10b981",
      accentGold: "#d4af37",
      accentBurgundy: "#7c2d12",
      accentForest: "#14532d",
      bg: "#f7fdf9",
      bgSecondary: "#e6f7ef",
      bgCard: "#ffffff",
      bgElevated: "#ffffff",
      textPrimary: "#0d1f17",
      textSecondary: "#345242",
      textTertiary: "#6b8478",
      textInverse: "#f7fdf9",
      border: "#d9ead7",
      borderHover: "#b8d4b0",
      success: "#047857",
      warning: "#b45309",
      error: "#991b1b",
      info: "#0e7490",
    },
  },
  academia: {
    name: "academia",
    label: "Dark Academia",
    description: "Eski universitet — qora va tilla",
    palette: {
      primary: "#a16207",
      primaryHover: "#854d0e",
      primaryLight: "#ca8a04",
      accentGold: "#d4af37",
      accentBurgundy: "#7c2d12",
      accentForest: "#3f6212",
      bg: "#faf8f0",
      bgSecondary: "#f5f0dc",
      bgCard: "#fffef9",
      bgElevated: "#fffef9",
      textPrimary: "#1c1408",
      textSecondary: "#3e2f1a",
      textTertiary: "#8a7855",
      textInverse: "#faf8f0",
      border: "#e8d9b8",
      borderHover: "#d4be8a",
      success: "#3f6212",
      warning: "#a16207",
      error: "#7f1d1d",
      info: "#0c4a6e",
    },
  },
  minimal: {
    name: "minimal",
    label: "Minimal",
    description: "Sof oq + qora — tinch va sof",
    palette: {
      primary: "#171717",
      primaryHover: "#000000",
      primaryLight: "#404040",
      accentGold: "#a3a3a3",
      accentBurgundy: "#525252",
      accentForest: "#404040",
      bg: "#ffffff",
      bgSecondary: "#f5f5f5",
      bgCard: "#ffffff",
      bgElevated: "#ffffff",
      textPrimary: "#0a0a0a",
      textSecondary: "#404040",
      textTertiary: "#737373",
      textInverse: "#ffffff",
      border: "#e5e5e5",
      borderHover: "#a3a3a3",
      success: "#15803d",
      warning: "#b45309",
      error: "#b91c1c",
      info: "#1e40af",
    },
  },
  ocean: {
    name: "ocean",
    label: "Ocean",
    description: "Dengiz — chuqurlik va sokinlik",
    palette: {
      primary: "#0369a1",
      primaryHover: "#075985",
      primaryLight: "#0ea5e9",
      accentGold: "#0d9488",
      accentBurgundy: "#9f1239",
      accentForest: "#155e75",
      bg: "#f0f9ff",
      bgSecondary: "#e0f2fe",
      bgCard: "#ffffff",
      bgElevated: "#ffffff",
      textPrimary: "#082f49",
      textSecondary: "#0c4a6e",
      textTertiary: "#0284c7",
      textInverse: "#f0f9ff",
      border: "#bae6fd",
      borderHover: "#7dd3fc",
      success: "#0d9488",
      warning: "#a16207",
      error: "#991b1b",
      info: "#0369a1",
    },
  },
  sunset: {
    name: "sunset",
    label: "Sunset",
    description: "Quyosh botishi — iliq va do'stona",
    palette: {
      primary: "#c2410c",
      primaryHover: "#9a3412",
      primaryLight: "#f97316",
      accentGold: "#d97706",
      accentBurgundy: "#9f1239",
      accentForest: "#166534",
      bg: "#fff7ed",
      bgSecondary: "#ffedd5",
      bgCard: "#ffffff",
      bgElevated: "#ffffff",
      textPrimary: "#1c0d04",
      textSecondary: "#451a03",
      textTertiary: "#92400e",
      textInverse: "#fff7ed",
      border: "#fed7aa",
      borderHover: "#fdba74",
      success: "#15803d",
      warning: "#a16207",
      error: "#991b1b",
      info: "#1e40af",
    },
  },
};

export const THEME_NAMES = Object.keys(THEMES);
export const DEFAULT_THEME = "classic";

/**
 * Write the palette to `document.documentElement.style` as
 * `--color-*` CSS variables. No-op on the server.
 */
export function applyTheme(name: string): void {
  if (typeof document === "undefined") return;
  const theme = THEMES[name] ?? THEMES[DEFAULT_THEME];
  const root = document.documentElement;
  const p = theme.palette;
  root.style.setProperty("--color-primary", p.primary);
  root.style.setProperty("--color-primary-hover", p.primaryHover);
  root.style.setProperty("--color-primary-light", p.primaryLight);
  root.style.setProperty("--color-accent-gold", p.accentGold);
  root.style.setProperty("--color-accent-burgundy", p.accentBurgundy);
  root.style.setProperty("--color-accent-forest", p.accentForest);
  root.style.setProperty("--color-bg", p.bg);
  root.style.setProperty("--color-bg-secondary", p.bgSecondary);
  root.style.setProperty("--color-bg-card", p.bgCard);
  root.style.setProperty("--color-bg-elevated", p.bgElevated);
  root.style.setProperty("--color-text-primary", p.textPrimary);
  root.style.setProperty("--color-text-secondary", p.textSecondary);
  root.style.setProperty("--color-text-tertiary", p.textTertiary);
  root.style.setProperty("--color-text-inverse", p.textInverse);
  root.style.setProperty("--color-border", p.border);
  root.style.setProperty("--color-border-hover", p.borderHover);
  root.style.setProperty("--color-success", p.success);
  root.style.setProperty("--color-warning", p.warning);
  root.style.setProperty("--color-error", p.error);
  root.style.setProperty("--color-info", p.info);
  root.setAttribute("data-theme", theme.name);
}
