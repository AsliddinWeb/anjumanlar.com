<script setup lang="ts">
const { t } = useI18n();
const localePath = useLocalePath();
const { formatDate } = useFormatDate();

useSiteSeo({
  title: t("footer.privacy"),
  description: t("legal.privacy.intro"),
});

const lastUpdated = formatDate("2026-05-24", { withTime: false });

const sections = computed(() => [
  { id: "intro", label: t("legal.privacy.s_intro") },
  { id: "collect", label: t("legal.privacy.s_collect") },
  { id: "use", label: t("legal.privacy.s_use") },
  { id: "share", label: t("legal.privacy.s_share") },
  { id: "cookies", label: t("legal.privacy.s_cookies") },
  { id: "rights", label: t("legal.privacy.s_rights") },
  { id: "security", label: t("legal.privacy.s_security") },
  { id: "retention", label: t("legal.privacy.s_retention") },
  { id: "changes", label: t("legal.privacy.s_changes") },
  { id: "contact", label: t("legal.privacy.s_contact") },
]);

useHead({
  link: [
    { rel: "alternate", href: localePath("/legal/terms"), title: t("footer.terms") },
  ],
});
</script>

<template>
  <LegalShell
    icon="lock"
    :title="t('footer.privacy')"
    :last-updated="t('legal.last_updated', { date: lastUpdated })"
    :sections="sections"
  >
    <div
      class="mb-8 inline-flex items-start gap-2 px-3 py-2 rounded-md bg-warning/10 border border-warning/30 text-xs text-warning"
    >
      <Icon name="warning" class="h-3.5 w-3.5 mt-0.5 shrink-0" />
      <span>{{ t("legal.draft_notice") }}</span>
    </div>

    <section id="intro">
      <h2>{{ t("legal.privacy.s_intro") }}</h2>
      <p>{{ t("legal.privacy.intro") }}</p>
    </section>

    <section id="collect">
      <h2>{{ t("legal.privacy.s_collect") }}</h2>
      <p>{{ t("legal.privacy.collect_p1") }}</p>
      <ul>
        <li>{{ t("legal.privacy.collect_l1") }}</li>
        <li>{{ t("legal.privacy.collect_l2") }}</li>
        <li>{{ t("legal.privacy.collect_l3") }}</li>
        <li>{{ t("legal.privacy.collect_l4") }}</li>
      </ul>
    </section>

    <section id="use">
      <h2>{{ t("legal.privacy.s_use") }}</h2>
      <p>{{ t("legal.privacy.use_p1") }}</p>
      <ul>
        <li>{{ t("legal.privacy.use_l1") }}</li>
        <li>{{ t("legal.privacy.use_l2") }}</li>
        <li>{{ t("legal.privacy.use_l3") }}</li>
      </ul>
    </section>

    <section id="share">
      <h2>{{ t("legal.privacy.s_share") }}</h2>
      <p>{{ t("legal.privacy.share_p1") }}</p>
      <ul>
        <li>{{ t("legal.privacy.share_l1") }}</li>
        <li>{{ t("legal.privacy.share_l2") }}</li>
        <li>{{ t("legal.privacy.share_l3") }}</li>
      </ul>
    </section>

    <section id="cookies">
      <h2>{{ t("legal.privacy.s_cookies") }}</h2>
      <p>{{ t("legal.privacy.cookies_p1") }}</p>
    </section>

    <section id="rights">
      <h2>{{ t("legal.privacy.s_rights") }}</h2>
      <p>{{ t("legal.privacy.rights_p1") }}</p>
      <ul>
        <li>{{ t("legal.privacy.rights_l1") }}</li>
        <li>{{ t("legal.privacy.rights_l2") }}</li>
        <li>{{ t("legal.privacy.rights_l3") }}</li>
        <li>{{ t("legal.privacy.rights_l4") }}</li>
      </ul>
    </section>

    <section id="security">
      <h2>{{ t("legal.privacy.s_security") }}</h2>
      <p>{{ t("legal.privacy.security_p1") }}</p>
    </section>

    <section id="retention">
      <h2>{{ t("legal.privacy.s_retention") }}</h2>
      <p>{{ t("legal.privacy.retention_p1") }}</p>
    </section>

    <section id="changes">
      <h2>{{ t("legal.privacy.s_changes") }}</h2>
      <p>{{ t("legal.privacy.changes_p1") }}</p>
    </section>

    <section id="contact">
      <h2>{{ t("legal.privacy.s_contact") }}</h2>
      <p>
        {{ t("legal.privacy.contact_p1") }}
        <a href="mailto:info@monografiya.com">info@monografiya.com</a>.
      </p>
    </section>
  </LegalShell>
</template>
