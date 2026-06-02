/**
 * National-motif ornament registry — ten Turkic / Central Asian SVG
 * patterns the admin can pick from.
 *
 * Each entry ships:
 *   - `label` + `description` for the picker card
 *   - `divider`  — inline SVG path content for UiOrnamentDivider
 *                  (drawn inside viewBox 0 0 42 42, stroke=currentColor)
 *   - `corner`   — inline SVG path content for UiOrnamentCorner
 *                  (drawn inside viewBox 0 0 120 120, stroke=currentColor)
 *
 * Both fields are rendered as `<g v-html="…" />` so each motif is just a
 * string of SVG primitives — keeps the registry compact and the
 * component generic.
 */

export interface OrnamentDefinition {
  name: string;
  label: string;
  description: string;
  divider: string;
  corner: string;
  /** Single repeating tile drawn inside viewBox 0 0 80 80. Used as a
   *  hero / section background watermark via UiOrnamentPattern. */
  pattern: string;
}

/* -------- divider SVG snippets (viewBox 0 0 42 42) -------- */

const D_CLASSIC = `
  <rect x="11" y="11" width="20" height="20" />
  <rect x="11" y="11" width="20" height="20" transform="rotate(45 21 21)" />
  <path d="M21 8 L34 21 L21 34 L8 21 Z" />
  <circle cx="21" cy="21" r="2" fill="currentColor" stroke="none" />
`;

const D_SUZANI = `
  <circle cx="21" cy="21" r="6" />
  <path d="M21 4 Q26 12 21 21 Q16 12 21 4 Z" />
  <path d="M21 38 Q26 30 21 21 Q16 30 21 38 Z" />
  <path d="M4 21 Q12 26 21 21 Q12 16 4 21 Z" />
  <path d="M38 21 Q30 26 21 21 Q30 16 38 21 Z" />
  <circle cx="21" cy="21" r="2" fill="currentColor" stroke="none" />
`;

const D_CHEVRON = `
  <path d="M4 28 L13 14 L21 28 L29 14 L38 28" />
  <path d="M4 22 L13 8 L21 22 L29 8 L38 22" opacity="0.6" />
`;

const D_MEDALLION = `
  <circle cx="21" cy="21" r="14" />
  <circle cx="21" cy="21" r="10" opacity="0.6" />
  <circle cx="21" cy="21" r="6" />
  <circle cx="21" cy="21" r="2" fill="currentColor" stroke="none" />
  <line x1="21" y1="3" x2="21" y2="9" />
  <line x1="21" y1="33" x2="21" y2="39" />
  <line x1="3" y1="21" x2="9" y2="21" />
  <line x1="33" y1="21" x2="39" y2="21" />
`;

const D_LATTICE = `
  <path d="M6 21 L21 6 L36 21 L21 36 Z" />
  <path d="M14 21 L21 14 L28 21 L21 28 Z" />
  <line x1="6" y1="21" x2="36" y2="21" />
  <line x1="21" y1="6" x2="21" y2="36" />
`;

const D_ARCH = `
  <path d="M9 30 L9 22 Q9 12 21 12 Q33 12 33 22 L33 30" />
  <path d="M15 30 L15 24 Q15 18 21 18 Q27 18 27 24 L27 30" opacity="0.55" />
  <line x1="6" y1="30" x2="36" y2="30" />
  <circle cx="21" cy="9" r="2" fill="currentColor" stroke="none" />
`;

const D_PAISLEY = `
  <path d="M14 30 Q6 22 14 14 Q22 6 30 14 Q34 22 26 26 Q18 28 22 22 Q26 16 20 18 Q14 22 18 26 Q22 30 14 30 Z" />
  <circle cx="20" cy="20" r="1.6" fill="currentColor" stroke="none" />
`;

const D_CRESCENT = `
  <path d="M14 8 A13 13 0 1 0 14 34 A10 10 0 1 1 14 8 Z" />
  <circle cx="30" cy="14" r="1.6" fill="currentColor" stroke="none" />
  <circle cx="33" cy="21" r="1.4" fill="currentColor" stroke="none" />
  <circle cx="30" cy="28" r="1.6" fill="currentColor" stroke="none" />
`;

const D_TILE = `
  <rect x="6" y="6" width="30" height="30" />
  <path d="M6 21 L21 6 L36 21 L21 36 Z" opacity="0.6" />
  <circle cx="21" cy="21" r="3" />
  <circle cx="6" cy="6" r="1.4" fill="currentColor" stroke="none" />
  <circle cx="36" cy="6" r="1.4" fill="currentColor" stroke="none" />
  <circle cx="6" cy="36" r="1.4" fill="currentColor" stroke="none" />
  <circle cx="36" cy="36" r="1.4" fill="currentColor" stroke="none" />
`;

const D_MINIMAL = `
  <circle cx="21" cy="21" r="3" />
  <circle cx="21" cy="21" r="6" opacity="0.5" />
`;

/* -------- corner SVG snippets (viewBox 0 0 120 120) -------- */

const C_CLASSIC = `
  <path d="M10 10 Q60 10 60 60 Q10 60 10 10 Z" opacity="0.55" />
  <path d="M10 10 Q40 30 60 60" opacity="0.45" />
  <path d="M10 10 Q30 40 60 60" opacity="0.45" />
  <circle cx="22" cy="22" r="2" fill="currentColor" stroke="none" opacity="0.7" />
  <circle cx="38" cy="38" r="1.6" fill="currentColor" stroke="none" opacity="0.55" />
  <g transform="translate(85 25)" opacity="0.6">
    <rect x="-7" y="-7" width="14" height="14" />
    <rect x="-7" y="-7" width="14" height="14" transform="rotate(45)" />
  </g>
`;

const C_SUZANI = `
  <g transform="translate(35 35)" opacity="0.55">
    <circle r="14" />
    <path d="M0 -28 Q9 -14 0 0 Q-9 -14 0 -28 Z" />
    <path d="M0 28 Q9 14 0 0 Q-9 14 0 28 Z" />
    <path d="M-28 0 Q-14 9 0 0 Q-14 -9 -28 0 Z" />
    <path d="M28 0 Q14 9 0 0 Q14 -9 28 0 Z" />
    <circle r="3" fill="currentColor" stroke="none" />
  </g>
`;

const C_CHEVRON = `
  <g opacity="0.55">
    <path d="M0 30 L30 0 L60 30 L90 0" />
    <path d="M0 50 L30 20 L60 50 L90 20" opacity="0.7" />
    <path d="M0 70 L30 40 L60 70 L90 40" opacity="0.5" />
  </g>
`;

const C_MEDALLION = `
  <g transform="translate(40 40)" opacity="0.55">
    <circle r="30" />
    <circle r="22" opacity="0.7" />
    <circle r="14" />
    <circle r="6" fill="currentColor" stroke="none" />
  </g>
`;

const C_LATTICE = `
  <g opacity="0.5">
    <path d="M10 50 L50 10 L90 50 L50 90 Z" />
    <path d="M30 50 L50 30 L70 50 L50 70 Z" />
    <line x1="10" y1="50" x2="90" y2="50" />
    <line x1="50" y1="10" x2="50" y2="90" />
  </g>
`;

const C_ARCH = `
  <g opacity="0.55">
    <path d="M15 80 L15 50 Q15 20 50 20 Q85 20 85 50 L85 80" />
    <path d="M30 80 L30 55 Q30 35 50 35 Q70 35 70 55 L70 80" opacity="0.6" />
    <line x1="8" y1="80" x2="92" y2="80" />
    <circle cx="50" cy="15" r="3" fill="currentColor" stroke="none" />
  </g>
`;

const C_PAISLEY = `
  <g transform="translate(30 30)" opacity="0.55">
    <path d="M0 60 Q-25 35 0 10 Q25 -15 50 10 Q65 35 35 45 Q5 50 20 35 Q35 20 15 25 Q-5 35 5 50 Q15 65 0 60 Z" />
    <circle cx="15" cy="20" r="2" fill="currentColor" stroke="none" />
  </g>
`;

const C_CRESCENT = `
  <g opacity="0.55">
    <path d="M25 15 A40 40 0 1 0 25 95 A32 32 0 1 1 25 15 Z" />
    <circle cx="80" cy="35" r="2.5" fill="currentColor" stroke="none" />
    <circle cx="90" cy="50" r="2" fill="currentColor" stroke="none" />
    <circle cx="80" cy="65" r="2.5" fill="currentColor" stroke="none" />
  </g>
`;

const C_TILE = `
  <g opacity="0.55">
    <rect x="15" y="15" width="60" height="60" />
    <path d="M15 45 L45 15 L75 45 L45 75 Z" opacity="0.7" />
    <circle cx="45" cy="45" r="6" />
    <circle cx="15" cy="15" r="2" fill="currentColor" stroke="none" />
    <circle cx="75" cy="15" r="2" fill="currentColor" stroke="none" />
    <circle cx="15" cy="75" r="2" fill="currentColor" stroke="none" />
    <circle cx="75" cy="75" r="2" fill="currentColor" stroke="none" />
  </g>
`;

const C_MINIMAL = `
  <g transform="translate(40 40)" opacity="0.45">
    <circle r="8" />
    <circle r="16" opacity="0.6" />
  </g>
`;

/* -------- pattern SVG snippets (viewBox 0 0 80 80, tileable) -------- */

const P_CLASSIC = `
  <g transform="translate(40 40)">
    <rect x="-12" y="-12" width="24" height="24" />
    <rect x="-12" y="-12" width="24" height="24" transform="rotate(45)" />
    <circle r="3" fill="currentColor" stroke="none" />
  </g>
  <g transform="translate(0 0)" opacity="0.6">
    <rect x="-6" y="-6" width="12" height="12" transform="rotate(45)" />
  </g>
  <g transform="translate(80 0)" opacity="0.6">
    <rect x="-6" y="-6" width="12" height="12" transform="rotate(45)" />
  </g>
  <g transform="translate(0 80)" opacity="0.6">
    <rect x="-6" y="-6" width="12" height="12" transform="rotate(45)" />
  </g>
  <g transform="translate(80 80)" opacity="0.6">
    <rect x="-6" y="-6" width="12" height="12" transform="rotate(45)" />
  </g>
`;

const P_SUZANI = `
  <g transform="translate(40 40)">
    <circle r="8" />
    <path d="M0 -16 Q5 -8 0 0 Q-5 -8 0 -16 Z" />
    <path d="M0 16 Q5 8 0 0 Q-5 8 0 16 Z" />
    <path d="M-16 0 Q-8 5 0 0 Q-8 -5 -16 0 Z" />
    <path d="M16 0 Q8 5 0 0 Q8 -5 16 0 Z" />
    <circle r="2" fill="currentColor" stroke="none" />
  </g>
`;

const P_CHEVRON = `
  <path d="M0 30 L20 10 L40 30 L60 10 L80 30" />
  <path d="M0 50 L20 30 L40 50 L60 30 L80 50" opacity="0.55" />
  <path d="M0 70 L20 50 L40 70 L60 50 L80 70" opacity="0.4" />
`;

const P_MEDALLION = `
  <g transform="translate(40 40)">
    <circle r="22" />
    <circle r="14" opacity="0.6" />
    <circle r="6" />
    <circle r="2" fill="currentColor" stroke="none" />
  </g>
`;

const P_LATTICE = `
  <path d="M0 40 L40 0 L80 40 L40 80 Z" />
  <path d="M20 40 L40 20 L60 40 L40 60 Z" opacity="0.6" />
  <line x1="0" y1="40" x2="80" y2="40" opacity="0.3" />
  <line x1="40" y1="0" x2="40" y2="80" opacity="0.3" />
`;

const P_ARCH = `
  <g opacity="0.7">
    <path d="M20 60 L20 45 Q20 28 40 28 Q60 28 60 45 L60 60" />
    <path d="M28 60 L28 48 Q28 37 40 37 Q52 37 52 48 L52 60" opacity="0.6" />
    <line x1="14" y1="60" x2="66" y2="60" />
    <circle cx="40" cy="22" r="2" fill="currentColor" stroke="none" />
  </g>
`;

const P_PAISLEY = `
  <g transform="translate(40 40)">
    <path d="M-12 16 Q-22 6 -12 -6 Q-2 -16 8 -6 Q14 6 4 12 Q-6 16 -2 6 Q4 -2 -4 0 Q-12 4 -8 12 Q-4 18 -12 16 Z" />
    <circle cx="-4" cy="4" r="1.6" fill="currentColor" stroke="none" />
  </g>
`;

const P_CRESCENT = `
  <g transform="translate(40 40)">
    <path d="M-14 -16 A22 22 0 1 0 -14 16 A16 16 0 1 1 -14 -16 Z" opacity="0.7" />
    <circle cx="14" cy="-4" r="2" fill="currentColor" stroke="none" />
    <circle cx="18" cy="6" r="1.6" fill="currentColor" stroke="none" />
    <circle cx="14" cy="14" r="2" fill="currentColor" stroke="none" />
  </g>
`;

const P_TILE = `
  <rect x="10" y="10" width="60" height="60" />
  <path d="M10 40 L40 10 L70 40 L40 70 Z" opacity="0.55" />
  <circle cx="40" cy="40" r="4" />
  <circle cx="10" cy="10" r="1.6" fill="currentColor" stroke="none" />
  <circle cx="70" cy="10" r="1.6" fill="currentColor" stroke="none" />
  <circle cx="10" cy="70" r="1.6" fill="currentColor" stroke="none" />
  <circle cx="70" cy="70" r="1.6" fill="currentColor" stroke="none" />
`;

const P_MINIMAL = `
  <circle cx="40" cy="40" r="3" />
  <circle cx="40" cy="40" r="10" opacity="0.5" />
`;

export const ORNAMENTS: Record<string, OrnamentDefinition> = {
  classic: {
    name: "classic",
    label: "Klassik (8-burchakli yulduz)",
    description: "Turkiy 8-burchakli yulduz + olmos — kutubxonaning standart bezagi",
    divider: D_CLASSIC,
    corner: C_CLASSIC,
    pattern: P_CLASSIC,
  },
  suzani: {
    name: "suzani",
    label: "Suzani",
    description: "O'zbek suzani gulli motivi — markaziy gul va atrof barglar",
    divider: D_SUZANI,
    corner: C_SUZANI,
    pattern: P_SUZANI,
  },
  chevron: {
    name: "chevron",
    label: "Chevron",
    description: "Zigzag chiziq — chegara va arxitektura motivi",
    divider: D_CHEVRON,
    corner: C_CHEVRON,
    pattern: P_CHEVRON,
  },
  medallion: {
    name: "medallion",
    label: "Medalyon",
    description: "Markazlashgan doiraviy medalyon — Buxoro va Hirot uslubi",
    divider: D_MEDALLION,
    corner: C_MEDALLION,
    pattern: P_MEDALLION,
  },
  lattice: {
    name: "lattice",
    label: "Panjara",
    description: "Karkas panjara — Samarqand naqshi",
    divider: D_LATTICE,
    corner: C_LATTICE,
    pattern: P_LATTICE,
  },
  arch: {
    name: "arch",
    label: "Tok (Arch)",
    description: "Islom me'morchiligi tokchasi — masjid va madrasa shakli",
    divider: D_ARCH,
    corner: C_ARCH,
    pattern: P_ARCH,
  },
  paisley: {
    name: "paisley",
    label: "Paisley",
    description: "Bodom shaklidagi paisley — fors-turkiy motivi",
    divider: D_PAISLEY,
    corner: C_PAISLEY,
    pattern: P_PAISLEY,
  },
  crescent: {
    name: "crescent",
    label: "Yarim oy",
    description: "Yarim oy + yulduzli nuqtalar — sharq romantikasi",
    divider: D_CRESCENT,
    corner: C_CRESCENT,
    pattern: P_CRESCENT,
  },
  tile: {
    name: "tile",
    label: "Kafel",
    description: "Geometrik kafel — Termiz va Xiva uslubi",
    divider: D_TILE,
    corner: C_TILE,
    pattern: P_TILE,
  },
  minimal: {
    name: "minimal",
    label: "Minimal",
    description: "Sodda halqalar — minimalist temalar uchun",
    divider: D_MINIMAL,
    corner: C_MINIMAL,
    pattern: P_MINIMAL,
  },
};

export const ORNAMENT_NAMES = Object.keys(ORNAMENTS);
export const DEFAULT_ORNAMENT = "classic";

export function getOrnament(name: string): OrnamentDefinition {
  return ORNAMENTS[name] ?? ORNAMENTS[DEFAULT_ORNAMENT];
}
