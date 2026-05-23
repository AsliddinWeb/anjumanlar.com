<script setup lang="ts">
const props = defineProps<{
  modelValue: string;
  label: string;
  hint?: string;
  error?: string;
  required?: boolean;
  autocomplete?: "current-password" | "new-password";
  /** When true, renders a strength meter under the input. */
  showStrength?: boolean;
  placeholder?: string;
  minlength?: number;
  autofocus?: boolean;
}>();

defineEmits<{ "update:modelValue": [value: string] }>();

const { t } = useI18n();
const revealed = ref(false);
const capsLock = ref(false);

function handleKey(event: KeyboardEvent) {
  if (typeof event.getModifierState === "function") {
    capsLock.value = event.getModifierState("CapsLock");
  }
}

// Tiny scoring function: counts character classes + length. Good enough
// to give users qualitative feedback without dragging in zxcvbn.
const strength = computed(() => {
  const v = props.modelValue ?? "";
  if (!v) return { score: 0, label: "" };
  let score = 0;
  if (v.length >= 8) score++;
  if (/[A-Z]/.test(v)) score++;
  if (/[a-z]/.test(v)) score++;
  if (/\d/.test(v)) score++;
  if (/[^A-Za-z0-9]/.test(v)) score++;
  const labelKey = ["password.strength.weak", "password.strength.weak", "password.strength.fair", "password.strength.good", "password.strength.strong", "password.strength.strong"][score];
  return { score, label: t(labelKey) };
});
</script>

<template>
  <label class="block space-y-1.5">
    <span class="text-sm text-ink-secondary">
      {{ label }}<span v-if="required" class="text-error"> *</span>
    </span>
    <div class="relative">
      <input
        :value="modelValue"
        :type="revealed ? 'text' : 'password'"
        :placeholder="placeholder"
        :required="required"
        :autocomplete="autocomplete"
        :minlength="minlength"
        :autofocus="autofocus"
        class="w-full pl-3 pr-10 py-2.5 rounded border bg-bg-card text-ink placeholder:text-ink-tertiary transition-colors focus:outline-none"
        :class="[
          error
            ? 'border-error focus:border-error'
            : 'border-border focus:border-primary',
        ]"
        @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
        @keydown="handleKey"
        @keyup="handleKey"
      >
      <button
        type="button"
        class="absolute inset-y-0 right-0 px-3 text-ink-tertiary hover:text-ink"
        :aria-label="revealed ? t('password.hide') : t('password.show')"
        :aria-pressed="revealed"
        @click="revealed = !revealed"
      >
        <span aria-hidden="true">{{ revealed ? "🙈" : "👁" }}</span>
      </button>
    </div>

    <span
      v-if="capsLock"
      class="block text-xs text-warning"
      role="status"
    >
      ⚠ {{ t("password.caps_lock") }}
    </span>

    <!-- Strength meter (register only) -->
    <div v-if="showStrength && modelValue" class="space-y-1">
      <div class="flex gap-1">
        <span
          v-for="i in 5"
          :key="i"
          class="flex-1 h-1 rounded transition-colors"
          :class="
            i <= strength.score
              ? strength.score >= 4
                ? 'bg-success'
                : strength.score >= 3
                  ? 'bg-warning'
                  : 'bg-error'
              : 'bg-border'
          "
        />
      </div>
      <span class="text-xs text-ink-tertiary">{{ strength.label }}</span>
    </div>

    <span v-if="error" class="block text-xs text-error">{{ error }}</span>
    <span v-else-if="hint" class="block text-xs text-ink-tertiary">{{ hint }}</span>
  </label>
</template>
