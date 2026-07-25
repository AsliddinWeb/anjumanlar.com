/**
 * Section-level guard for scope-restricted admins. Apply after ``admin``
 * and declare the section via page meta::
 *
 *     definePageMeta({ middleware: ["auth", "admin", "admin-scope"], adminScope: "finance" })
 *
 * A superadmin or an unrestricted admin (``admin_scopes === null``) always
 * passes — this only ever turns a scoped admin away, mirroring the
 * backend's ``require_admin_scope``. Redirects to ``/admin`` rather than
 * showing a 403 page, same rationale as ``admin.ts``.
 */
export default defineNuxtRouteMiddleware((to) => {
  if (import.meta.server) return;
  const scope = to.meta.adminScope;
  if (!scope) return;
  const auth = useAuthStore();
  if (!auth.hasAdminScope(scope)) {
    const localePath = useLocalePath();
    return navigateTo(localePath("/admin"));
  }
});
