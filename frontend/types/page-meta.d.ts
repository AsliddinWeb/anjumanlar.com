import type { AdminScope } from "~/types/api";

// Augments Nuxt's PageMeta so `definePageMeta({ adminScope: "finance" })`
// type-checks — read by middleware/admin-scope.ts via `to.meta.adminScope`.
declare module "#app" {
  interface PageMeta {
    adminScope?: AdminScope;
  }
}

export {};
