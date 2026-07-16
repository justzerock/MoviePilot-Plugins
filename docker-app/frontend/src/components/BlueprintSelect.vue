<template>
  <label ref="rootEl" class="mcr-blueprint-select" :class="rootClass">
    <span v-if="label" class="mcr-blueprint-select__label">{{ label }}</span>
    <span v-if="multiple" class="mcr-blueprint-select__multi">
      <button
        type="button"
        class="mcr-blueprint-select__multi-trigger"
        :class="{ 'mcr-blueprint-select__multi-trigger--open': isOpen }"
        :disabled="isDisabled"
        :aria-expanded="isOpen"
        @click.prevent="toggleOpen"
      >
        <span v-if="selectedItems.length" class="mcr-blueprint-select__chips">
          <span
            v-for="item in visibleSelectedItems"
            :key="String(item.value)"
            class="mcr-blueprint-select__chip"
          >
            {{ item.title }}
          </span>
          <span v-if="hiddenSelectedCount > 0" class="mcr-blueprint-select__chip mcr-blueprint-select__chip--more">
            ···
          </span>
        </span>
        <span v-else class="mcr-blueprint-select__placeholder">
          {{ placeholder || '不指定，默认全部' }}
        </span>
        <span class="mcr-blueprint-select__count" aria-hidden="true">
          {{ selectedItems.length || normalizedItems.length }}
        </span>
      </button>
      <Teleport to="body">
        <span
          v-if="isOpen"
          ref="popoverEl"
          class="mcr-blueprint-select__popover"
          :class="`mcr-blueprint-select__popover--${popoverPlacement}`"
          :data-mcr-theme="popoverTheme"
          :style="popoverStyle"
          role="listbox"
          aria-multiselectable="true"
        >
          <button
            v-for="item in normalizedItems"
            :key="String(item.value)"
            type="button"
            class="mcr-blueprint-select__multi-option"
            :class="{ 'mcr-blueprint-select__multi-option--active': isSelected(item.value) }"
            :disabled="isDisabled"
            role="option"
            :aria-selected="isSelected(item.value)"
            @pointerdown.prevent.stop
            @click.prevent.stop="toggleMultiple(item.value)"
          >
            <span class="mcr-blueprint-select__checkbox" aria-hidden="true">
              <span v-if="isSelected(item.value)" class="mcr-blueprint-select__check">✓</span>
            </span>
            <span class="mcr-blueprint-select__multi-title">{{ item.title }}</span>
          </button>
          <button
            type="button"
            class="mcr-blueprint-select__done"
            @pointerdown.prevent.stop
            @click.prevent.stop="closePopover"
          >
            完成
          </button>
        </span>
      </Teleport>
    </span>
    <span v-else class="mcr-blueprint-select__shell">
      <select
        v-bind="controlAttrs"
        class="mcr-blueprint-select__control"
        :value="selectValue"
        @change="onChange"
      >
        <option v-if="clearable" value="">{{ placeholder || '不指定' }}</option>
        <option
          v-for="item in normalizedItems"
          :key="String(item.value)"
          :value="item.value"
        >
          {{ item.title }}
        </option>
      </select>
    </span>
    <button
      v-if="clearable && multiple && selectedCount > 0"
      type="button"
      class="mcr-blueprint-select__clear"
      @click.prevent="clearMultiple"
    >
      清除已选 {{ selectedCount }} 项
    </button>
    <span v-if="hint" class="mcr-blueprint-select__hint">{{ hint }}</span>
  </label>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, useAttrs } from 'vue'
import type { CSSProperties } from 'vue'

defineOptions({ inheritAttrs: false })

type SelectItem = string | number | { title?: string; label?: string; name?: string; value?: string | number | boolean | null }

const props = withDefaults(defineProps<{
  modelValue?: string | number | boolean | null | Array<string | number | boolean | null>
  items?: SelectItem[]
  label?: string
  hint?: string
  placeholder?: string
  multiple?: boolean
  clearable?: boolean
}>(), {
  modelValue: '',
  items: () => [],
  label: '',
  hint: '',
  placeholder: '',
  multiple: false,
  clearable: false,
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string | number | boolean | null | Array<string | number | boolean | null>): void
}>()

const attrs = useAttrs()
const rootEl = ref<HTMLElement | null>(null)
const popoverEl = ref<HTMLElement | null>(null)
const isOpen = ref(false)
const popoverPlacement = ref<'top' | 'bottom'>('bottom')
const popoverTheme = ref<'light' | 'dark'>('light')
const popoverStyle = ref<CSSProperties>({})

const rootClass = computed(() => attrs.class)

const controlAttrs = computed(() => {
  const { class: _class, ...rest } = attrs
  return rest
})

const normalizedItems = computed(() => props.items.map((item) => {
  if (typeof item === 'object' && item !== null) {
    const value = item.value ?? item.title ?? item.label ?? item.name ?? ''
    return {
      title: String(item.title ?? item.label ?? item.name ?? value),
      value,
    }
  }
  return {
    title: String(item),
    value: item,
  }
}))

const selectValue = computed(() => (
  props.multiple
    ? (Array.isArray(props.modelValue) ? props.modelValue.map((item) => String(item)) : [])
    : String(props.modelValue ?? '')
))

const selectedCount = computed(() => (
  Array.isArray(props.modelValue) ? props.modelValue.length : 0
))

const selectedItems = computed(() => (
  Array.isArray(props.modelValue)
    ? normalizedItems.value.filter((item) => isSelected(item.value))
    : []
))
const visibleSelectedItems = computed(() => selectedItems.value.slice(0, 2))
const hiddenSelectedCount = computed(() => Math.max(0, selectedItems.value.length - visibleSelectedItems.value.length))

const isDisabled = computed(() => (
  attrs.disabled === true || attrs.disabled === '' || attrs.disabled === 'true'
))

function denormalizeValue(raw: string) {
  const found = normalizedItems.value.find((item) => String(item.value) === raw)
  return found ? found.value : raw
}

function onChange(event: Event) {
  const select = event.target as HTMLSelectElement
  emit('update:modelValue', denormalizeValue(select.value))
}

function isSelected(value: string | number | boolean | null) {
  if (!Array.isArray(props.modelValue)) return false
  return props.modelValue.some((item) => String(item) === String(value))
}

function toggleMultiple(value: string | number | boolean | null) {
  if (isDisabled.value) return
  const scrollSnapshot = captureScrollSnapshot()
  const current = Array.isArray(props.modelValue) ? props.modelValue : []
  const exists = current.some((item) => String(item) === String(value))
  emit(
    'update:modelValue',
    exists
      ? current.filter((item) => String(item) !== String(value))
      : [...current, value],
  )
  nextTick(() => {
    restoreScrollSnapshot(scrollSnapshot)
    updatePopoverPosition()
  })
}

function toggleOpen() {
  if (isDisabled.value) return
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    nextTick(updatePopoverPosition)
  }
}

function clearMultiple() {
  const scrollSnapshot = captureScrollSnapshot()
  emit('update:modelValue', [])
  isOpen.value = false
  nextTick(() => restoreScrollSnapshot(scrollSnapshot))
}

function closePopover() {
  const scrollSnapshot = captureScrollSnapshot()
  isOpen.value = false
  nextTick(() => restoreScrollSnapshot(scrollSnapshot))
}

function captureScrollSnapshot() {
  if (typeof window === 'undefined' || typeof document === 'undefined') return null
  return {
    windowX: window.scrollX,
    windowY: window.scrollY,
    docTop: document.documentElement.scrollTop,
    bodyTop: document.body?.scrollTop || 0,
  }
}

function restoreScrollSnapshot(snapshot: ReturnType<typeof captureScrollSnapshot>) {
  if (!snapshot || typeof window === 'undefined' || typeof document === 'undefined') return
  document.documentElement.scrollTop = snapshot.docTop
  if (document.body) document.body.scrollTop = snapshot.bodyTop
  window.scrollTo(snapshot.windowX, snapshot.windowY)
  window.requestAnimationFrame?.(() => {
    document.documentElement.scrollTop = snapshot.docTop
    if (document.body) document.body.scrollTop = snapshot.bodyTop
    window.scrollTo(snapshot.windowX, snapshot.windowY)
  })
}

function onDocumentPointerDown(event: PointerEvent) {
  if (!isOpen.value || !rootEl.value) return
  const target = event.target as Node
  if (!rootEl.value.contains(target) && !popoverEl.value?.contains(target)) {
    isOpen.value = false
  }
}

function onDocumentKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    isOpen.value = false
  }
}

function readPopoverTheme() {
  const themedRoot = rootEl.value?.closest('[data-mcr-theme]')
  const explicitTheme = themedRoot?.getAttribute('data-mcr-theme')
  if (explicitTheme === 'dark' || explicitTheme === 'light') {
    popoverTheme.value = explicitTheme
    return
  }
  popoverTheme.value = typeof window !== 'undefined'
    && typeof window.matchMedia === 'function'
    && window.matchMedia('(prefers-color-scheme: dark)').matches
    ? 'dark'
    : 'light'
}

function updatePopoverPosition() {
  if (!isOpen.value || typeof window === 'undefined') return
  const trigger = rootEl.value?.querySelector<HTMLElement>('.mcr-blueprint-select__multi-trigger')
  const anchor = trigger || rootEl.value
  if (!anchor) return

  readPopoverTheme()
  const rect = anchor.getBoundingClientRect()
  const viewportWidth = window.innerWidth || document.documentElement.clientWidth
  const viewportHeight = window.innerHeight || document.documentElement.clientHeight
  const gutter = 12
  const desiredWidth = viewportWidth < 680
    ? viewportWidth - gutter * 2
    : Math.min(Math.max(rect.width, 560), viewportWidth - gutter * 2)
  const left = Math.min(
    Math.max(gutter, rect.left),
    Math.max(gutter, viewportWidth - desiredWidth - gutter),
  )
  const spaceBelow = viewportHeight - rect.bottom - gutter
  const spaceAbove = rect.top - gutter
  const shouldOpenTop = spaceBelow < 260 && spaceAbove > spaceBelow
  const maxHeight = Math.max(
    180,
    Math.min(360, (shouldOpenTop ? spaceAbove : spaceBelow) - 8),
  )

  popoverPlacement.value = shouldOpenTop ? 'top' : 'bottom'
  popoverStyle.value = shouldOpenTop
    ? {
        left: `${left}px`,
        bottom: `${viewportHeight - rect.top + 8}px`,
        width: `${desiredWidth}px`,
        maxHeight: `${maxHeight}px`,
      }
    : {
        left: `${left}px`,
        top: `${rect.bottom + 8}px`,
        width: `${desiredWidth}px`,
        maxHeight: `${maxHeight}px`,
      }
}

onMounted(() => {
  document.addEventListener('pointerdown', onDocumentPointerDown)
  document.addEventListener('keydown', onDocumentKeydown)
  window.addEventListener('resize', updatePopoverPosition)
  window.addEventListener('scroll', updatePopoverPosition, true)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', onDocumentPointerDown)
  document.removeEventListener('keydown', onDocumentKeydown)
  window.removeEventListener('resize', updatePopoverPosition)
  window.removeEventListener('scroll', updatePopoverPosition, true)
})
</script>

<style scoped>
.mcr-blueprint-select {
  display: grid;
  gap: 7px;
  width: 100%;
  min-width: 0;
  color: rgba(var(--mcr-rgb-on-surface), 0.94);
  font-family: 'Geist', 'Be Vietnam Pro', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei',
    ui-sans-serif, system-ui, sans-serif;
}

.mcr-blueprint-select__label {
  min-width: 0;
  color: rgba(var(--mcr-rgb-primary-fixed), 0.9);
  font-size: 11px;
  font-weight: 700;
  line-height: 1.25;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.mcr-blueprint-select__shell {
  position: relative;
  display: block;
}

.mcr-blueprint-select__shell::after {
  content: '';
  position: absolute;
  top: 50%;
  right: 13px;
  width: 8px;
  height: 8px;
  pointer-events: none;
  border-right: 1px solid rgba(var(--mcr-rgb-primary-fixed), 0.95);
  border-bottom: 1px solid rgba(var(--mcr-rgb-primary-fixed), 0.95);
  transform: translateY(-64%) rotate(45deg);
}

.mcr-blueprint-select__shell--multiple::after {
  display: none;
}

.mcr-blueprint-select__control {
  width: 100%;
  min-width: 0;
  min-height: 44px;
  padding: 11px 34px 11px 12px;
  border: 1px solid rgba(var(--mcr-rgb-primary-container), 0.44);
  border-radius: 0;
  outline: none;
  appearance: none;
  background:
    linear-gradient(rgba(var(--mcr-rgb-surface-container-lowest), 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(var(--mcr-rgb-surface-container-lowest), 0.03) 1px, transparent 1px),
    rgba(var(--mcr-rgb-surface-container-lowest), 0.88);
  background-size: 20px 20px, 20px 20px, cover;
  color: rgba(var(--mcr-rgb-on-surface), 0.96);
  box-shadow:
    inset 0 0 0 1px rgba(var(--mcr-rgb-surface-container-lowest), 0.035),
    0 0 0 rgba(var(--mcr-rgb-primary-container), 0);
  font: inherit;
  font-size: 13px;
  line-height: 1.45;
  transition:
    border-color 220ms ease,
    box-shadow 220ms ease,
    background-color 220ms ease;
}

.mcr-blueprint-select__control:focus {
  border-color: rgba(var(--mcr-rgb-primary-container), 0.92);
  background-color: rgba(var(--mcr-rgb-surface-container-lowest), 0.96);
  box-shadow:
    inset 0 0 0 1px rgba(var(--mcr-rgb-primary-container), 0.18),
    0 0 22px rgba(var(--mcr-rgb-primary-container), 0.18);
}

.mcr-blueprint-select__control[multiple] {
  min-height: 116px;
  padding-right: 12px;
}

.mcr-blueprint-select__control option {
  background: var(--mcr-color-surface-container-lowest);
  color: rgba(var(--mcr-rgb-on-surface), 0.96);
}

.mcr-blueprint-select__control option:checked {
  background: var(--mcr-color-primary);
  color: var(--mcr-color-surface-container-lowest);
}

.mcr-blueprint-select__multi-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 8px;
}

.mcr-blueprint-select__multi {
  position: relative;
  display: grid;
  gap: 8px;
  min-width: 0;
}

.mcr-blueprint-select__multi-trigger {
  display: flex;
  height: 42px;
  min-height: 42px;
  max-height: 42px;
  width: 100%;
  min-width: 0;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 10px;
  border: 1px solid rgba(var(--mcr-rgb-outline-variant), 0.70);
  border-radius: 12px;
  background: var(--mcr-color-surface-container-lowest);
  color: var(--mcr-color-on-surface);
  cursor: pointer;
  font: inherit;
  text-align: left;
  box-shadow: none;
  transition:
    border-color 180ms ease,
    box-shadow 180ms ease,
    background-color 180ms ease;
}

.mcr-blueprint-select__multi-trigger:hover,
.mcr-blueprint-select__multi-trigger--open {
  border-color: rgba(var(--mcr-rgb-primary-container), 0.74);
  box-shadow: 0 0 0 4px rgba(var(--mcr-rgb-primary-container), 0.11);
}

.mcr-blueprint-select__multi-trigger:disabled {
  cursor: not-allowed;
  opacity: 0.58;
}

.mcr-blueprint-select__chips {
  display: flex;
  min-width: 0;
  flex: 1 1 auto;
  flex-wrap: nowrap;
  gap: 6px;
  overflow: hidden;
}

.mcr-blueprint-select__chip {
  max-width: min(180px, 48%);
  overflow: hidden;
  padding: 4px 8px;
  border: 1px solid rgba(var(--mcr-rgb-primary-container), 0.24);
  border-radius: 999px;
  background: rgba(var(--mcr-rgb-primary-container), 0.12);
  color: var(--mcr-color-on-primary-container);
  font-size: 12px;
  font-weight: 650;
  line-height: 1.2;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mcr-blueprint-select__chip--more {
  flex: 0 0 auto;
  max-width: 34px;
  padding-inline: 8px;
  letter-spacing: 0.06em;
}

.mcr-blueprint-select__placeholder {
  min-width: 0;
  flex: 1 1 auto;
  overflow: hidden;
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.62);
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mcr-blueprint-select__count {
  min-width: 28px;
  height: 24px;
  display: inline-grid;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 999px;
  background: rgba(var(--mcr-rgb-surface-container-highest), 0.72);
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.78);
  font-size: 12px;
  font-weight: 800;
}

.mcr-blueprint-select__popover {
  position: fixed;
  z-index: 2600;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  align-content: start;
  overflow: auto;
  overscroll-behavior: contain;
  gap: 6px;
  padding: 8px;
  border: 1px solid rgba(var(--mcr-rgb-outline-variant), 0.76);
  border-radius: 14px;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.98);
  box-shadow: var(--mcr-depth-shadow-2, 0 18px 42px rgba(var(--mcr-rgb-shadow), 0.12));
  backdrop-filter: blur(16px);
}

.mcr-blueprint-select__done {
  grid-column: 1 / -1;
  justify-self: end;
  padding: 7px 11px;
  border: 1px solid rgba(var(--mcr-rgb-primary-container), 0.44);
  border-radius: 999px;
  background: rgba(var(--mcr-rgb-primary-container), 0.12);
  color: var(--mcr-color-primary);
  cursor: pointer;
  font: inherit;
  font-size: 12px;
  font-weight: 700;
}

.mcr-blueprint-select__multi-option {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 10px;
  padding: 9px 10px;
  border: 1px solid rgba(var(--mcr-rgb-outline-variant), 0.64);
  border-radius: 12px;
  background: var(--mcr-color-surface-container-lowest);
  color: rgba(var(--mcr-rgb-on-surface), 0.88);
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  line-height: 1.25;
  text-align: left;
  transition:
    border-color 180ms ease,
    background-color 180ms ease,
    box-shadow 180ms ease,
    color 180ms ease;
}

.mcr-blueprint-select__multi-option:hover {
  border-color: rgba(var(--mcr-rgb-primary-container), 0.42);
  background: rgba(var(--mcr-rgb-primary-fixed), 0.22);
}

.mcr-blueprint-select__multi-option--active {
  border-color: rgba(var(--mcr-rgb-primary-container), 0.72);
  background: rgba(var(--mcr-rgb-primary-fixed), 0.38);
  color: var(--mcr-color-on-primary-container);
  box-shadow: inset 3px 0 0 var(--mcr-color-primary-container);
}

.mcr-blueprint-select__multi-option:disabled {
  cursor: not-allowed;
  opacity: 0.58;
}

.mcr-blueprint-select__checkbox {
  display: inline-grid;
  width: 18px;
  height: 18px;
  flex: 0 0 auto;
  place-items: center;
  border: 1px solid rgba(var(--mcr-rgb-outline), 0.58);
  border-radius: 5px;
  background: rgba(var(--mcr-rgb-surface-container-lowest), 0.96);
  color: var(--mcr-color-surface-container-lowest);
  font-size: 12px;
  font-weight: 900;
}

.mcr-blueprint-select__multi-option--active .mcr-blueprint-select__checkbox {
  border-color: var(--mcr-color-primary-container);
  background: var(--mcr-color-primary-container);
}

.mcr-blueprint-select__multi-title {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mcr-blueprint-select__clear {
  justify-self: start;
  border: 1px solid rgba(var(--mcr-rgb-primary-container), 0.46);
  border-radius: 0;
  background: rgba(var(--mcr-rgb-primary-container), 0.08);
  color: var(--mcr-color-primary);
  cursor: pointer;
  font: inherit;
  font-size: 11px;
  line-height: 1;
  padding: 7px 9px;
}

.mcr-blueprint-select__clear:hover {
  border-color: rgba(var(--mcr-rgb-primary-container), 0.9);
  color: var(--mcr-color-primary);
  box-shadow: 0 0 16px rgba(var(--mcr-rgb-primary-container), 0.16);
}

.mcr-blueprint-select__hint {
  color: rgba(var(--mcr-rgb-primary-fixed-dim), 0.62);
  font-size: 11px;
  line-height: 1.45;
}

html.dark .mcr-blueprint-select,
.v-theme--dark .mcr-blueprint-select,
[data-mcr-theme="dark"] .mcr-blueprint-select {
  color: var(--mcr-color-on-surface);
}

html.dark .mcr-blueprint-select__label,
.v-theme--dark .mcr-blueprint-select__label,
[data-mcr-theme="dark"] .mcr-blueprint-select__label {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.72);
}

html.dark .mcr-blueprint-select__control,
html.dark .mcr-blueprint-select__multi-trigger,
html.dark .mcr-blueprint-select__popover,
html.dark .mcr-blueprint-select__multi-option,
.v-theme--dark .mcr-blueprint-select__control,
.v-theme--dark .mcr-blueprint-select__multi-trigger,
.v-theme--dark .mcr-blueprint-select__popover,
.v-theme--dark .mcr-blueprint-select__multi-option,
[data-mcr-theme="dark"] .mcr-blueprint-select__control,
[data-mcr-theme="dark"] .mcr-blueprint-select__multi-trigger,
[data-mcr-theme="dark"] .mcr-blueprint-select__popover,
[data-mcr-theme="dark"] .mcr-blueprint-select__multi-option,
.mcr-blueprint-select__popover[data-mcr-theme="dark"],
.mcr-blueprint-select__popover[data-mcr-theme="dark"] .mcr-blueprint-select__multi-option {
  border-color: rgba(var(--mcr-rgb-outline-variant), 0.92);
  background: var(--mcr-color-surface-container-lowest);
  color: var(--mcr-color-on-surface);
  -webkit-text-fill-color: var(--mcr-color-on-surface);
}

html.dark .mcr-blueprint-select__multi-option--active,
.v-theme--dark .mcr-blueprint-select__multi-option--active,
[data-mcr-theme="dark"] .mcr-blueprint-select__multi-option--active,
.mcr-blueprint-select__popover[data-mcr-theme="dark"] .mcr-blueprint-select__multi-option--active {
  border-color: rgba(var(--mcr-rgb-primary-container), 0.72);
  background: rgba(var(--mcr-rgb-primary-container), 0.14);
  color: var(--mcr-color-primary);
  -webkit-text-fill-color: var(--mcr-color-primary);
  box-shadow: inset 3px 0 0 var(--mcr-color-primary-container);
}

html.dark .mcr-blueprint-select__chip,
.v-theme--dark .mcr-blueprint-select__chip,
[data-mcr-theme="dark"] .mcr-blueprint-select__chip {
  border-color: rgba(var(--mcr-rgb-primary), 0.28);
  background: rgba(var(--mcr-rgb-primary), 0.16);
  color: var(--mcr-color-on-surface);
  -webkit-text-fill-color: var(--mcr-color-on-surface);
}

html.dark .mcr-blueprint-select__hint,
.v-theme--dark .mcr-blueprint-select__hint,
[data-mcr-theme="dark"] .mcr-blueprint-select__hint {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.58);
}

/* Final studio select skin, overriding the legacy blueprint defaults above. */
.mcr-blueprint-select {
  color: var(--mcr-color-on-surface);
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'PingFang SC',
    'Helvetica Neue', Arial, sans-serif;
}

.mcr-blueprint-select__label {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.72);
  font-size: 12px;
  font-weight: 650;
  letter-spacing: 0;
  text-transform: none;
}

.mcr-blueprint-select__control {
  min-height: 42px;
  border: 1px solid rgba(var(--mcr-rgb-outline-variant), 0.70);
  border-radius: 12px;
  background: var(--mcr-color-surface-container-lowest);
  background-image: none;
  color: var(--mcr-color-on-surface);
  box-shadow:
    inset 0 1px 2px rgba(0, 0, 0, 0.035),
    inset 0 1px 0 rgba(255, 255, 255, 0.28);
  font-family: inherit;
}

.mcr-blueprint-select__control:focus {
  border-color: rgba(0, 122, 255, 0.70);
  background: var(--mcr-color-surface-container-lowest);
  box-shadow: 0 0 0 4px rgba(0, 122, 255, 0.14);
}

.mcr-blueprint-select__hint {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.58);
}

:global([data-mcr-theme="dark"]) .mcr-blueprint-select,
:global(.v-theme--dark) .mcr-blueprint-select {
  color: var(--mcr-color-on-surface);
}

:global([data-mcr-theme="dark"]) .mcr-blueprint-select__label,
:global(.v-theme--dark) .mcr-blueprint-select__label {
  color: rgba(var(--mcr-rgb-on-surface-variant), 0.72);
}

:global([data-mcr-theme="dark"]) .mcr-blueprint-select__control,
:global([data-mcr-theme="dark"]) .mcr-blueprint-select__multi-trigger,
:global([data-mcr-theme="dark"]) .mcr-blueprint-select__popover,
:global([data-mcr-theme="dark"]) .mcr-blueprint-select__multi-option,
:global(.mcr-blueprint-select__popover[data-mcr-theme="dark"]),
:global(.mcr-blueprint-select__popover[data-mcr-theme="dark"]) .mcr-blueprint-select__multi-option,
:global(.v-theme--dark) .mcr-blueprint-select__control,
:global(.v-theme--dark) .mcr-blueprint-select__multi-trigger,
:global(.v-theme--dark) .mcr-blueprint-select__popover,
:global(.v-theme--dark) .mcr-blueprint-select__multi-option {
  border-color: rgba(var(--mcr-rgb-outline-variant), 0.92);
  background: var(--mcr-color-surface-container-lowest);
  background-image: none;
  color: var(--mcr-color-on-surface);
  -webkit-text-fill-color: var(--mcr-color-on-surface);
}

:global([data-mcr-theme="dark"]) .mcr-blueprint-select__control:focus,
:global(.v-theme--dark) .mcr-blueprint-select__control:focus {
  border-color: rgba(var(--mcr-rgb-primary-container), 0.74);
  box-shadow: 0 0 0 4px rgba(var(--mcr-rgb-primary-container), 0.14);
}

:global([data-mcr-theme="dark"]) .mcr-blueprint-select__multi-option--active,
:global(.mcr-blueprint-select__popover[data-mcr-theme="dark"]) .mcr-blueprint-select__multi-option--active,
:global(.v-theme--dark) .mcr-blueprint-select__multi-option--active {
  border-color: rgba(var(--mcr-rgb-primary-container), 0.72);
  background: rgba(var(--mcr-rgb-primary-container), 0.14);
  color: var(--mcr-color-primary);
  -webkit-text-fill-color: var(--mcr-color-primary);
  box-shadow: inset 3px 0 0 var(--mcr-color-primary-container);
}

:global([data-mcr-theme="dark"]) .mcr-blueprint-select__chip,
:global(.v-theme--dark) .mcr-blueprint-select__chip {
  border-color: rgba(var(--mcr-rgb-primary), 0.28);
  background: rgba(var(--mcr-rgb-primary), 0.16);
  color: var(--mcr-color-on-surface);
  -webkit-text-fill-color: var(--mcr-color-on-surface);
}

/* Selected targets stay unmistakable on light surfaces. */
:global([data-mcr-theme="light"] .mcr-blueprint-select__chip),
:global(.mcr-blueprint-select__popover[data-mcr-theme="light"] .mcr-blueprint-select__multi-option--active) {
  border-color: #007aff;
  background: #007aff;
  color: #fff;
  -webkit-text-fill-color: #fff;
  box-shadow: none;
}

:global(.mcr-blueprint-select__popover[data-mcr-theme="light"] .mcr-blueprint-select__multi-option--active .mcr-blueprint-select__checkbox) {
  border-color: rgba(255, 255, 255, 0.82);
  background: rgba(255, 255, 255, 0.18);
  color: #fff;
}

@media (prefers-color-scheme: dark) {
  .mcr-blueprint-select {
    color: var(--mcr-color-on-surface);
  }

  .mcr-blueprint-select__label {
    color: rgba(var(--mcr-rgb-on-surface-variant), 0.72);
  }

  .mcr-blueprint-select__control,
  .mcr-blueprint-select__multi-trigger,
  .mcr-blueprint-select__popover,
  .mcr-blueprint-select__multi-option {
    border-color: rgba(var(--mcr-rgb-outline-variant), 0.92);
    background: var(--mcr-color-surface-container-lowest);
    background-image: none;
    color: var(--mcr-color-on-surface);
    -webkit-text-fill-color: var(--mcr-color-on-surface);
  }

  .mcr-blueprint-select__control:focus {
    border-color: rgba(var(--mcr-rgb-primary-container), 0.74);
    box-shadow: 0 0 0 4px rgba(var(--mcr-rgb-primary-container), 0.14);
  }

  .mcr-blueprint-select__multi-option--active {
    border-color: rgba(var(--mcr-rgb-primary-container), 0.72);
    background: rgba(var(--mcr-rgb-primary-container), 0.14);
    color: var(--mcr-color-primary);
    -webkit-text-fill-color: var(--mcr-color-primary);
    box-shadow: inset 3px 0 0 var(--mcr-color-primary-container);
  }

  .mcr-blueprint-select__chip {
    border-color: rgba(var(--mcr-rgb-primary), 0.28);
    background: rgba(var(--mcr-rgb-primary), 0.16);
    color: var(--mcr-color-on-surface);
    -webkit-text-fill-color: var(--mcr-color-on-surface);
  }
}
</style>
