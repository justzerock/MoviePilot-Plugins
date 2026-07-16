<template>
  <label class="blueprint-range">
    <input
      class="blueprint-range__input"
      type="range"
      :min="min"
      :max="max"
      :step="step"
      :value="sliderValue"
      :style="rangeStyle"
      @pointerdown="emit('start')"
      @pointerup="emit('end')"
      @pointercancel="emit('end')"
      @blur="emit('end')"
      @input="onInput"
      @change="onChange"
    />
    <span class="blueprint-range__content">
      <span class="blueprint-range__label">{{ label }}</span>
      <input
        class="blueprint-range__value"
        type="number"
        :min="manualMin"
        :max="manualMax"
        :step="step"
        :value="displayValue"
        @focus="emit('start')"
        @input="onNumberInput"
        @change="onNumberChange"
        @blur="emit('end')"
      >
    </span>
  </label>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  modelValue?: number | string | null
  min?: number
  max?: number
  step?: number
  label?: string
}>(), {
  modelValue: 0,
  min: 0,
  max: 100,
  step: 1,
  label: '',
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: number): void
  (e: 'change', value: number): void
  (e: 'start'): void
  (e: 'end'): void
}>()

const numericValue = computed(() => {
  const next = Number(props.modelValue ?? props.min)
  return Number.isFinite(next) ? next : props.min
})

const sliderValue = computed(() => Math.max(props.min, Math.min(props.max, numericValue.value)))

const manualMin = computed(() => (props.min < 0 ? props.min * 10 : props.min))

const manualMax = computed(() => (props.max > 0 ? props.max * 10 : props.max))

const percent = computed(() => {
  const span = props.max - props.min
  if (!span) return 0
  return Math.max(0, Math.min(100, ((sliderValue.value - props.min) / span) * 100))
})

const displayValue = computed(() => {
  const stepText = String(props.step)
  const decimals = stepText.includes('.') ? stepText.split('.')[1].length : 0
  if (!decimals) return String(Math.round(numericValue.value))
  return numericValue.value.toFixed(decimals).replace(/(\.\d*?)0+$/, '$1').replace(/\.$/, '')
})

const rangeStyle = computed(() => ({
  '--blueprint-range-progress': `${percent.value}%`,
}))

function readValue(event: Event) {
  const value = Number((event.target as HTMLInputElement).value)
  return Number.isFinite(value) ? value : props.min
}

function onInput(event: Event) {
  emit('update:modelValue', readValue(event))
}

function onChange(event: Event) {
  emit('change', readValue(event))
}

function normalizeManualValue(raw: string) {
  const value = Number(raw)
  if (!Number.isFinite(value)) return numericValue.value
  return Math.max(manualMin.value, Math.min(manualMax.value, value))
}

function onNumberInput(event: Event) {
  emit('update:modelValue', normalizeManualValue((event.target as HTMLInputElement).value))
}

function onNumberChange(event: Event) {
  const value = normalizeManualValue((event.target as HTMLInputElement).value)
  emit('update:modelValue', value)
  emit('change', value)
}
</script>

<style scoped>
.blueprint-range {
  position: relative;
  isolation: isolate;
  display: block;
  width: 100%;
  min-height: 46px;
  margin-block: 4px 8px;
  overflow: hidden;
  border: 1px solid var(--color-border, var(--mcr-color-outline-variant));
  border-radius: 14px;
  background: var(--color-surface, var(--mcr-color-surface-container-lowest));
  color: var(--color-text-main, var(--mcr-color-on-surface));
  font-family: inherit;
  box-shadow:
    inset 0 1px 2px rgba(0, 0, 0, 0.035),
    inset 0 1px 0 rgba(var(--color-rgb-surface, 255, 255, 255), 0.42),
    0 5px 14px rgba(var(--color-rgb-shadow, 47, 76, 128), 0.045);
  transition:
    border-color 220ms ease,
    box-shadow 220ms ease,
    background-color 220ms ease;
}

@media (hover: hover) and (pointer: fine) {
  .blueprint-range:hover {
    border-color: rgba(0, 122, 255, 0.30);
  }
}

.blueprint-range:focus-within {
  border-color: rgba(0, 122, 255, 0.68);
  box-shadow:
    0 0 0 4px rgba(0, 122, 255, 0.14),
    inset 0 1px 0 rgba(var(--color-rgb-surface, 255, 255, 255), 0.42);
}

.blueprint-range::before {
  content: '';
  position: absolute;
  z-index: 1;
  inset: 11px 66px 11px max(120px, 34%);
  pointer-events: none;
  opacity: 0.64;
  background: repeating-linear-gradient(
    90deg,
    transparent 0 calc(10% - 1px),
    rgba(var(--color-rgb-primary, 79, 140, 255), 0.24) calc(10% - 1px) 10%,
    transparent 10% 20%
  );
  -webkit-mask-image: linear-gradient(90deg, transparent, #000 10%, #000 90%, transparent);
  mask-image: linear-gradient(90deg, transparent, #000 10%, #000 90%, transparent);
}

.blueprint-range__content {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 44px;
  min-width: 0;
  padding: 0 8px 0 16px;
  pointer-events: none;
}

.blueprint-range__label,
.blueprint-range__value {
  font-size: 13px;
  line-height: 1.2;
  letter-spacing: 0;
}

.blueprint-range__label {
  min-width: 0;
  overflow: hidden;
  color: var(--color-text-secondary, var(--mcr-color-on-surface-variant));
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.blueprint-range__value {
  flex: 0 0 54px;
  width: 54px;
  min-width: 0;
  padding: 6px 6px;
  border: 0;
  border-radius: 9px;
  outline: none;
  background: rgba(120, 120, 128, 0.10);
  color: var(--color-text-main, var(--mcr-color-on-surface));
  text-align: right;
  font: inherit;
  font-size: 13px;
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  pointer-events: auto;
  -moz-appearance: textfield;
}

.blueprint-range__value::-webkit-inner-spin-button,
.blueprint-range__value::-webkit-outer-spin-button {
  margin: 0;
  appearance: none;
}

.blueprint-range__input {
  position: absolute;
  z-index: 0;
  inset: 6px 66px 6px 8px;
  width: calc(100% - 74px);
  height: calc(100% - 12px);
  margin: 0;
  appearance: none;
  border-radius: 10px;
  background: rgba(0, 122, 255, 0.08);
  cursor: pointer;
  touch-action: pan-y;
  user-select: none;
  -webkit-user-select: none;
}

.blueprint-range__input::-webkit-slider-runnable-track {
  width: 100%;
  height: 34px;
  border: 0;
  border-radius: 10px;
  background:
    linear-gradient(
      90deg,
      rgba(0, 122, 255, 0.16),
      rgba(100, 180, 255, 0.12)
    ) 0 / var(--blueprint-range-progress) 100% no-repeat,
    transparent;
}

.blueprint-range__input::-webkit-slider-thumb {
  width: 7px;
  height: 24px;
  margin-top: 5px;
  appearance: none;
  border: 0;
  border-radius: 3px;
  background: rgba(0, 122, 255, 0.82);
  box-shadow:
    0 0 0 4px rgba(0, 122, 255, 0.07),
    0 4px 12px rgba(0, 122, 255, 0.12);
}

.blueprint-range__input::-moz-range-track {
  height: 34px;
  border: 0;
  border-radius: 10px;
  background: rgba(var(--color-rgb-primary, 79, 140, 255), 0.08);
}

.blueprint-range__input::-moz-range-progress {
  height: 34px;
  border-radius: 10px;
  background: linear-gradient(
    90deg,
    rgba(0, 122, 255, 0.16),
    rgba(100, 180, 255, 0.12)
  );
}

.blueprint-range__input::-moz-range-thumb {
  width: 7px;
  height: 24px;
  border: 0;
  border-radius: 3px;
  background: rgba(0, 122, 255, 0.82);
  box-shadow:
    0 0 0 4px rgba(0, 122, 255, 0.07),
    0 4px 12px rgba(0, 122, 255, 0.12);
}

.blueprint-range__input:focus-visible {
  outline: none;
}

.blueprint-range__value:focus-visible {
  border-radius: 7px;
  background: var(--color-surface, var(--mcr-color-surface-container-lowest));
  box-shadow: 0 0 0 2px rgba(var(--color-rgb-primary, 79, 140, 255), 0.18);
}

.blueprint-range__input:focus-visible::-webkit-slider-thumb {
  box-shadow:
    0 0 0 5px rgba(var(--color-rgb-primary, 79, 140, 255), 0.16),
    0 4px 14px rgba(var(--color-rgb-primary, 79, 140, 255), 0.24);
}

.blueprint-range__input:active::-webkit-slider-thumb {
  background: #007aff;
  box-shadow:
    0 0 0 6px rgba(0, 122, 255, 0.12),
    0 5px 16px rgba(0, 122, 255, 0.24);
}

.blueprint-range__input:active::-moz-range-thumb {
  background: #007aff;
  box-shadow:
    0 0 0 6px rgba(0, 122, 255, 0.12),
    0 5px 16px rgba(0, 122, 255, 0.24);
}

:global([data-mcr-theme="dark"]) .blueprint-range,
:global(.v-theme--dark) .blueprint-range {
  border-color: var(--color-border, rgba(230, 236, 245, 0.12));
  background: var(--color-surface, var(--mcr-color-surface-container));
  color: var(--color-text-main, var(--mcr-color-on-surface));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

:global([data-mcr-theme="dark"]) .blueprint-range__label,
:global(.v-theme--dark) .blueprint-range__label {
  color: var(--color-text-secondary, var(--mcr-color-on-surface-variant));
}

:global([data-mcr-theme="dark"]) .blueprint-range__value,
:global(.v-theme--dark) .blueprint-range__value {
  border-color: transparent;
  background: rgba(120, 120, 128, 0.20);
  color: var(--color-text-main, var(--mcr-color-on-surface));
}

:global([data-mcr-theme="dark"]) .blueprint-range__input,
:global(.v-theme--dark) .blueprint-range__input,
:global([data-mcr-theme="dark"]) .blueprint-range__input::-moz-range-track,
:global(.v-theme--dark) .blueprint-range__input::-moz-range-track {
  background: rgba(10, 132, 255, 0.13);
}

:global([data-mcr-theme="dark"]) .blueprint-range__input::-webkit-slider-thumb,
:global(.v-theme--dark) .blueprint-range__input::-webkit-slider-thumb {
  background: rgba(10, 132, 255, 0.88);
}

@media (prefers-reduced-motion: reduce) {
  .blueprint-range {
    transition-duration: 1ms;
  }
}

@media (prefers-color-scheme: dark) {
  .blueprint-range {
    border-color: var(--color-border, rgba(230, 236, 245, 0.12));
    background: var(--color-surface-soft, var(--mcr-color-surface-container));
    color: var(--color-text-main, var(--mcr-color-on-surface));
  }
}

@media (max-width: 599px) {
  .blueprint-range {
    min-height: 44px;
    margin-block: 4px 7px;
    border-radius: 11px;
  }

  .blueprint-range__content {
    min-height: 42px;
    padding: 0 8px 0 12px;
  }

  .blueprint-range__value {
    flex-basis: 50px;
    width: 50px;
    font-size: 12px;
  }

  .blueprint-range__input {
    inset: 6px 60px 6px 7px;
    width: calc(100% - 67px);
  }

  .blueprint-range__input::-webkit-slider-runnable-track,
  .blueprint-range__input::-moz-range-track,
  .blueprint-range__input::-moz-range-progress {
    height: 32px;
  }

  .blueprint-range__input::-webkit-slider-thumb {
    height: 22px;
    margin-top: 5px;
  }

  .blueprint-range__input::-moz-range-thumb {
    height: 22px;
  }

  .blueprint-range::before {
    inset-block: 11px;
    inset-inline: max(104px, 36%) 60px;
  }
}
</style>
