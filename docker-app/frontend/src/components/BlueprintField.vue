<template>
  <label
    class="mcr-blueprint-field"
    :class="[
      rootClass,
      {
        'mcr-blueprint-field--textarea': textarea,
        'mcr-blueprint-field--color': type === 'color',
      },
    ]"
  >
    <span v-if="label" class="mcr-blueprint-field__label">{{ label }}</span>
    <textarea
      v-if="textarea"
      v-bind="controlAttrs"
      class="mcr-blueprint-field__control mcr-blueprint-field__control--textarea"
      :value="modelValue ?? ''"
      :rows="rows"
      :placeholder="placeholder"
      @input="onInput"
    />
    <input
      v-else
      v-bind="controlAttrs"
      class="mcr-blueprint-field__control"
      :type="type"
      :value="modelValue ?? ''"
      :placeholder="placeholder"
      @input="onInput"
    />
    <span v-if="hint" class="mcr-blueprint-field__hint">{{ hint }}</span>
  </label>
</template>

<script setup lang="ts">
import { computed, useAttrs } from 'vue'

defineOptions({ inheritAttrs: false })

const props = withDefaults(defineProps<{
  modelValue?: string | number | null
  label?: string
  type?: string
  placeholder?: string
  hint?: string
  rows?: string | number
  textarea?: boolean
  modelModifiers?: Record<string, boolean>
}>(), {
  modelValue: '',
  label: '',
  type: 'text',
  placeholder: '',
  hint: '',
  rows: 3,
  textarea: false,
  modelModifiers: () => ({}),
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string | number | null): void
}>()

const attrs = useAttrs()

const rootClass = computed(() => attrs.class)

const controlAttrs = computed(() => {
  const { class: _class, ...rest } = attrs
  return rest
})

function normalizeValue(value: string) {
  if (props.modelModifiers?.number || props.type === 'number') {
    return value === '' ? null : Number(value)
  }
  return value
}

function onInput(event: Event) {
  const target = event.target as HTMLInputElement | HTMLTextAreaElement
  emit('update:modelValue', normalizeValue(target.value))
}
</script>

<style scoped>
.mcr-blueprint-field {
  display: grid;
  gap: 7px;
  width: 100%;
  min-width: 0;
  color: rgba(var(--mcr-rgb-on-surface), 0.94);
  font-family: 'Geist', 'Be Vietnam Pro', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei',
    ui-sans-serif, system-ui, sans-serif;
}

.mcr-blueprint-field__label {
  min-width: 0;
  color: rgba(var(--mcr-rgb-primary-fixed), 0.9);
  font-size: 11px;
  font-weight: 700;
  line-height: 1.25;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.mcr-blueprint-field__control {
  width: 100%;
  min-width: 0;
  min-height: 44px;
  padding: 11px 12px;
  border: 1px solid rgba(var(--mcr-rgb-primary-container), 0.44);
  border-radius: 0;
  outline: none;
  background:
    linear-gradient(rgba(var(--mcr-rgb-surface-container-lowest), 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(var(--mcr-rgb-surface-container-lowest), 0.03) 1px, transparent 1px),
    rgba(var(--mcr-rgb-surface-container-lowest), 0.86);
  background-size: 20px 20px, 20px 20px, cover;
  color: rgba(var(--mcr-rgb-on-surface), 0.96);
  box-shadow:
    inset 0 0 0 1px rgba(var(--mcr-rgb-surface-container-lowest), 0.035),
    0 0 0 rgba(var(--mcr-rgb-primary-container), 0);
  caret-color: var(--mcr-color-primary-container);
  font: inherit;
  font-size: 13px;
  line-height: 1.45;
  transition:
    border-color 220ms ease,
    box-shadow 220ms ease,
    background-color 220ms ease;
}

.mcr-blueprint-field__control::placeholder {
  color: rgba(var(--mcr-rgb-primary-fixed-dim), 0.42);
  opacity: 1;
}

.mcr-blueprint-field__control:focus {
  border-color: rgba(var(--mcr-rgb-primary-container), 0.92);
  background-color: rgba(var(--mcr-rgb-surface-container-lowest), 0.96);
  box-shadow:
    inset 0 0 0 1px rgba(var(--mcr-rgb-primary-container), 0.18),
    0 0 22px rgba(var(--mcr-rgb-primary-container), 0.18);
}

.mcr-blueprint-field__control--textarea {
  min-height: 92px;
  resize: vertical;
}

.mcr-blueprint-field--color .mcr-blueprint-field__control {
  min-height: 44px;
  padding: 6px;
  cursor: pointer;
}

.mcr-blueprint-field__hint {
  color: rgba(var(--mcr-rgb-primary-fixed-dim), 0.62);
  font-size: 11px;
  line-height: 1.45;
}

.mcr-blueprint-field__control::-webkit-outer-spin-button,
.mcr-blueprint-field__control::-webkit-inner-spin-button {
  margin: 0;
}

/* Studio control skin. Kept in this component so every page exits the old blueprint look. */
.mcr-blueprint-field {
  color: var(--mcr-color-on-surface);
  font-family: 'Geist', 'Be Vietnam Pro', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei',
    ui-sans-serif, system-ui, sans-serif;
}

.mcr-blueprint-field__label {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.72);
  font-size: 12px;
  font-weight: 650;
  letter-spacing: 0;
  text-transform: none;
}

.mcr-blueprint-field__control {
  min-height: 42px;
  border: 1px solid rgba(var(--mcr-rgb-outline-variant), 0.70);
  border-radius: 12px;
  background: var(--mcr-color-surface-container-lowest);
  background-image: none;
  color: var(--mcr-color-on-surface);
  box-shadow: none;
  caret-color: var(--mcr-color-primary-container);
  font-family: inherit;
}

.mcr-blueprint-field__control::placeholder {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.42);
}

.mcr-blueprint-field__control:focus {
  border-color: rgba(var(--mcr-rgb-primary-container), 0.74);
  background: var(--mcr-color-surface-container-lowest);
  box-shadow: 0 0 0 4px rgba(var(--mcr-rgb-primary-container), 0.11);
}

.mcr-blueprint-field__hint {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.58);
}

:global([data-mcr-theme="dark"]) .mcr-blueprint-field,
:global(.v-theme--dark) .mcr-blueprint-field {
  color: var(--mcr-color-on-surface);
}

:global([data-mcr-theme="dark"]) .mcr-blueprint-field__label,
:global(.v-theme--dark) .mcr-blueprint-field__label {
  color: #dce2ed;
}

:global([data-mcr-theme="dark"]) .mcr-blueprint-field__control,
:global(.v-theme--dark) .mcr-blueprint-field__control {
  border-color: rgba(var(--mcr-rgb-outline-variant), 0.92);
  background: var(--mcr-color-surface-container-lowest);
  background-image: none;
  color: #f5f7fb;
  -webkit-text-fill-color: #f5f7fb;
  caret-color: var(--mcr-color-primary-container);
}

:global([data-mcr-theme="dark"]) .mcr-blueprint-field__control::placeholder,
:global(.v-theme--dark) .mcr-blueprint-field__control::placeholder {
  color: #aeb8ca;
  -webkit-text-fill-color: #aeb8ca;
  opacity: 1;
}

:global([data-mcr-theme="dark"]) .mcr-blueprint-field__control:focus,
:global(.v-theme--dark) .mcr-blueprint-field__control:focus {
  border-color: rgba(var(--mcr-rgb-primary-container), 0.74);
  background: var(--mcr-color-surface-container-lowest);
  box-shadow: 0 0 0 4px rgba(var(--mcr-rgb-primary-container), 0.14);
}

:global([data-mcr-theme="dark"]) .mcr-blueprint-field__hint,
:global(.v-theme--dark) .mcr-blueprint-field__hint {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.58);
}

@media (prefers-color-scheme: dark) {
  .mcr-blueprint-field {
    color: var(--mcr-color-on-surface);
  }

  .mcr-blueprint-field__label {
    color: #dce2ed;
  }

  .mcr-blueprint-field__control {
    border-color: rgba(var(--mcr-rgb-outline-variant), 0.92);
    background: var(--mcr-color-surface-container-lowest);
    background-image: none;
    color: #f5f7fb;
    -webkit-text-fill-color: #f5f7fb;
    caret-color: var(--mcr-color-primary-container);
  }

  .mcr-blueprint-field__control::placeholder {
    color: #aeb8ca;
    -webkit-text-fill-color: #aeb8ca;
    opacity: 1;
  }

  .mcr-blueprint-field__control:focus {
    border-color: rgba(var(--mcr-rgb-primary-container), 0.74);
    background: var(--mcr-color-surface-container-lowest);
    box-shadow: 0 0 0 4px rgba(var(--mcr-rgb-primary-container), 0.14);
  }

  .mcr-blueprint-field__hint {
    color: rgba(var(--mcr-rgb-on-surface-variant), 0.58);
  }
}
</style>
