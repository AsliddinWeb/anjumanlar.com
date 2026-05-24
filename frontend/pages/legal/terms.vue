<script setup lang="ts">
const { t, locale } = useI18n();
const localePath = useLocalePath();

useSiteSeo({
  title: t("footer.terms"),
  description: t("legal.terms.intro"),
});

const lastUpdated = new Intl.DateTimeFormat(locale.value, {
  year: "numeric",
  month: "long",
  day: "numeric",
}).format(new Date("2026-05-24"));

const sections = computed(() => [
  { id: "intro", label: t("legal.terms.s_intro") },
  { id: "account", label: t("legal.terms.s_account") },
  { id: "content", label: t("legal.terms.s_content") },
  { id: "payments", label: t("legal.terms.s_payments") },
  { id: "authors", label: t("legal.terms.s_authors") },
  { id: "conduct", label: t("legal.terms.s_conduct") },
  { id: "termination", label: t("legal.terms.s_termination") },
  { id: "liability", label: t("legal.terms.s_liability") },
  { id: "changes", label: t("legal.terms.s_changes") },
  { id: "contact", label: t("legal.terms.s_contact") },
]);

useHead({
  link: [
    { rel: "alternate", href: localePath("/legal/privacy"), title: t("footer.privacy") },
  ],
});
</script>

<template>
  <LegalShell
    icon="document"
    :title="t('footer.terms')"
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
      <h2>{{ t("legal.terms.s_intro") }}</h2>
      <p>{{ t("legal.terms.intro") }}</p>
    </section>

    <section id="account">
      <h2>{{ t("legal.terms.s_account") }}</h2>
      <p>{{ t("legal.terms.account_p1") }}</p>
      <ul>
        <li>{{ t("legal.terms.account_l1") }}</li>
        <li>{{ t("legal.terms.account_l2") }}</li>
        <li>{{ t("legal.terms.account_l3") }}</li>
      </ul>
    </section>

    <section id="content">
      <h2>{{ t("legal.terms.s_content") }}</h2>
      <p>{{ t("legal.terms.content_p1") }}</p>
      <p>{{ t("legal.terms.content_p2") }}</p>
    </section>

    <section id="payments">
      <h2>{{ t("legal.terms.s_payments") }}</h2>
      <p>{{ t("legal.terms.payments_p1") }}</p>
      <ul>
        <li>{{ t("legal.terms.payments_l1") }}</li>
        <li>{{ t("legal.terms.payments_l2") }}</li>
        <li>{{ t("legal.terms.payments_l3") }}</li>
      </ul>
    </section>

    <section id="authors">
      <h2>{{ t("legal.terms.s_authors") }}</h2>
      <p>{{ t("legal.terms.authors_p1") }}</p>
      <ul>
        <li>{{ t("legal.terms.authors_l1") }}</li>
        <li>{{ t("legal.terms.authors_l2") }}</li>
        <li>{{ t("legal.terms.authors_l3") }}</li>
      </ul>
    </section>

    <section id="conduct">
      <h2>{{ t("legal.terms.s_conduct") }}</h2>
      <p>{{ t("legal.terms.conduct_p1") }}</p>
      <ul>
        <li>{{ t("legal.terms.conduct_l1") }}</li>
        <li>{{ t("legal.terms.conduct_l2") }}</li>
        <li>{{ t("legal.terms.conduct_l3") }}</li>
      </ul>
    </section>

    <section id="termination">
      <h2>{{ t("legal.terms.s_termination") }}</h2>
      <p>{{ t("legal.terms.termination_p1") }}</p>
    </section>

    <section id="liability">
      <h2>{{ t("legal.terms.s_liability") }}</h2>
      <p>{{ t("legal.terms.liability_p1") }}</p>
    </section>

    <section id="changes">
      <h2>{{ t("legal.terms.s_changes") }}</h2>
      <p>{{ t("legal.terms.changes_p1") }}</p>
    </section>

    <section id="contact">
      <h2>{{ t("legal.terms.s_contact") }}</h2>
      <p>
        {{ t("legal.terms.contact_p1") }}
        <a href="mailto:info@monografiya.com">info@monografiya.com</a>.
      </p>
    </section>
  </LegalShell>
</template>
