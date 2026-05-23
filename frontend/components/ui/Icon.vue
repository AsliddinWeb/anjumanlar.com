<script setup lang="ts">
/**
 * Project-wide icon wrapper. Every emoji on the site is replaced with an
 * entry from this map so we get a consistent stroke weight, sizing and
 * dark-mode colour story for free.
 *
 * Uses @heroicons/vue (24px outline + solid sets). Tree-shaking keeps
 * the bundle lean because each icon is imported by name — only icons
 * registered here ship to the client.
 *
 * Variants:
 *  - default = outline (24px, 1.5px stroke) — used everywhere
 *  - "*-solid" suffix swaps to the solid set
 *
 * Usage:
 *  <Icon name="heart" class="h-5 w-5" />
 *  <Icon name="heart-solid" class="h-5 w-5 text-error" />
 */
import {
  AcademicCapIcon,
  ArrowLeftIcon,
  ArrowPathIcon,
  ArrowRightIcon,
  ArrowTopRightOnSquareIcon,
  Bars3Icon,
  BanknotesIcon,
  BookOpenIcon,
  BuildingLibraryIcon,
  BuildingOfficeIcon,
  CheckCircleIcon,
  CheckIcon,
  ChartBarIcon,
  ChatBubbleLeftEllipsisIcon,
  ChevronDownIcon,
  ClipboardDocumentCheckIcon,
  ClipboardDocumentListIcon,
  Cog6ToothIcon,
  ComputerDesktopIcon,
  CurrencyDollarIcon,
  DocumentTextIcon,
  EnvelopeIcon,
  EnvelopeOpenIcon,
  ExclamationTriangleIcon,
  EyeIcon,
  EyeSlashIcon,
  FolderOpenIcon,
  GiftIcon,
  HandRaisedIcon,
  HeartIcon,
  HomeIcon,
  InboxIcon,
  InboxStackIcon,
  KeyIcon,
  LockClosedIcon,
  MagnifyingGlassIcon,
  MoonIcon,
  NewspaperIcon,
  PencilSquareIcon,
  PlusIcon,
  ScaleIcon,
  ShoppingCartIcon,
  SparklesIcon,
  SunIcon,
  StarIcon,
  TrashIcon,
  UserCircleIcon,
  UserPlusIcon,
  UsersIcon,
  WrenchScrewdriverIcon,
  XMarkIcon,
} from "@heroicons/vue/24/outline";
import {
  CheckCircleIcon as CheckCircleSolidIcon,
  ExclamationTriangleIcon as ExclamationTriangleSolidIcon,
  HeartIcon as HeartSolidIcon,
  StarIcon as StarSolidIcon,
} from "@heroicons/vue/24/solid";

const ICONS = {
  // --- generic ---
  "home": HomeIcon,
  "settings": Cog6ToothIcon,
  "search": MagnifyingGlassIcon,
  "menu": Bars3Icon,
  "close": XMarkIcon,
  "plus": PlusIcon,
  "check": CheckIcon,
  "check-circle": CheckCircleIcon,
  "check-circle-solid": CheckCircleSolidIcon,
  "warning": ExclamationTriangleIcon,
  "warning-solid": ExclamationTriangleSolidIcon,
  "arrow-left": ArrowLeftIcon,
  "arrow-right": ArrowRightIcon,
  "arrow-path": ArrowPathIcon,
  "external": ArrowTopRightOnSquareIcon,
  "chevron-down": ChevronDownIcon,
  "trash": TrashIcon,
  "pencil": PencilSquareIcon,
  "document": DocumentTextIcon,
  "key": KeyIcon,
  "lock": LockClosedIcon,
  "eye": EyeIcon,
  "eye-slash": EyeSlashIcon,
  "envelope": EnvelopeIcon,
  "envelope-open": EnvelopeOpenIcon,
  "sparkles": SparklesIcon,
  "moon": MoonIcon,
  "sun": SunIcon,
  "desktop": ComputerDesktopIcon,
  "user-circle": UserCircleIcon,
  "user-plus": UserPlusIcon,
  "users": UsersIcon,
  "hand": HandRaisedIcon,

  // --- commerce / content ---
  "book": BookOpenIcon,
  "library": BuildingLibraryIcon,
  "institution": BuildingOfficeIcon,
  "inbox": InboxIcon,
  "inbox-stack": InboxStackIcon,
  "cart": ShoppingCartIcon,
  "heart": HeartIcon,
  "heart-solid": HeartSolidIcon,
  "gift": GiftIcon,
  "star": StarIcon,
  "star-solid": StarSolidIcon,
  "chat": ChatBubbleLeftEllipsisIcon,
  "news": NewspaperIcon,
  "folder": FolderOpenIcon,
  "chart": ChartBarIcon,
  "clipboard-list": ClipboardDocumentListIcon,
  "clipboard-check": ClipboardDocumentCheckIcon,
  "money": BanknotesIcon,
  "currency": CurrencyDollarIcon,
  "scale": ScaleIcon,
  "wrench": WrenchScrewdriverIcon,
  "academic": AcademicCapIcon,
} as const;

export type IconName = keyof typeof ICONS;

const props = defineProps<{
  /** Accepts any string at runtime to tolerate user-supplied category icons. */
  name: IconName | string | null | undefined;
  /** Tailwind size class — h-5 w-5 default. Pass empty string to opt out. */
  class?: string;
  /** Fallback icon when ``name`` doesn't match a known entry. */
  fallback?: IconName;
}>();

const component = computed(() => {
  const key = props.name as IconName;
  if (key && key in ICONS) return ICONS[key];
  return props.fallback ? ICONS[props.fallback] : null;
});
const sizeClass = computed(() => (props.class === undefined ? "h-5 w-5" : props.class));
</script>

<template>
  <component :is="component" v-if="component" :class="sizeClass" aria-hidden="true" />
</template>
