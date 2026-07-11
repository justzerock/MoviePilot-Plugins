<template>
  <Teleport to="body"><nav class="yh-settings-anchor" :data-mcr-theme="theme" aria-label="设置分组导航">
    <v-tooltip v-for="section in sections" :key="section.id" location="end" :open-delay="220">
      <template #activator="{ props: tooltipProps }">
        <button v-bind="tooltipProps" type="button" class="yh-settings-anchor__button" :class="{ 'is-active': activeId === section.id }" :aria-label="`跳转到${section.label}`" :aria-current="activeId === section.id ? 'true' : undefined" @click="scrollToSection(section.id)">
          <span class="yh-settings-anchor__line" aria-hidden="true" />
        </button>
      </template>
      <span>{{ section.label }}</span>
    </v-tooltip>
  </nav></Teleport>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
export interface SettingsAnchorSection { id: string; label: string }
const props = withDefaults(defineProps<{ sections: SettingsAnchorSection[]; scrollContainer?: HTMLElement | null; topOffset?: number; theme?: 'light' | 'dark' }>(), { scrollContainer: null, topOffset: 96, theme: 'light' })
const activeId = ref(props.sections[0]?.id || '')
let observer: IntersectionObserver | null = null
let clickLockUntil = 0
let clickUnlockTimer: number | null = null
function observedElements() { return props.sections.map((section) => document.getElementById(section.id)).filter((element): element is HTMLElement => Boolean(element)) }
function setupObserver() {
  observer?.disconnect()
  const elements = observedElements()
  if (!elements.length || typeof IntersectionObserver === 'undefined') return
  observer = new IntersectionObserver((entries) => {
    if (Date.now() < clickLockUntil) return
    const root = props.scrollContainer
    const reachedBottom = root ? root.scrollTop + root.clientHeight >= root.scrollHeight - 2 : window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 2
    if (reachedBottom && props.sections.length) { activeId.value = props.sections[props.sections.length - 1].id; return }
    const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => Math.abs(a.boundingClientRect.top - props.topOffset) - Math.abs(b.boundingClientRect.top - props.topOffset))
    if (visible[0]?.target.id) activeId.value = visible[0].target.id
  }, { root: props.scrollContainer || null, rootMargin: `-${props.topOffset}px 0px -62% 0px`, threshold: [0, 0.05, 0.25, 0.6] })
  elements.forEach((element) => observer?.observe(element))
}
function scrollToSection(id: string) { const target = document.getElementById(id); if (!target) return; activeId.value = id; clickLockUntil = Date.now() + 1800; target.scrollIntoView({ behavior: 'smooth', block: 'start' }); if (clickUnlockTimer !== null) window.clearTimeout(clickUnlockTimer); clickUnlockTimer = window.setTimeout(() => { activeId.value = id; clickUnlockTimer = null }, 950) }
watch(() => [props.sections, props.scrollContainer], () => void nextTick(setupObserver), { deep: true })
onMounted(() => void nextTick(setupObserver))
onBeforeUnmount(() => { observer?.disconnect(); if (clickUnlockTimer !== null) window.clearTimeout(clickUnlockTimer) })
</script>

<style scoped>
.yh-settings-anchor { position: fixed; top: 50%; left: max(12px, env(safe-area-inset-left)); z-index: 28; width: 36px; height: max-content; margin: 0; padding: 4px 0; background: transparent; transform: translateY(-50%); }
.yh-settings-anchor__button { width: 34px; height: 32px; display: grid; place-items: center; padding: 0; border: 0; background: transparent; cursor: pointer; }
.yh-settings-anchor__line { width: 16px; height: 2px; border-radius: 999px; background: rgba(60, 60, 67, 0.25); transition: width 180ms ease, opacity 180ms ease, background-color 180ms ease, transform 180ms ease; }
.yh-settings-anchor__button:hover .yh-settings-anchor__line, .yh-settings-anchor__button:focus-visible .yh-settings-anchor__line { width: 24px; background: rgba(60, 60, 67, 0.55); }
.yh-settings-anchor__button.is-active .yh-settings-anchor__line { width: 32px; background: var(--color-primary, #4f8cff); opacity: 1; transform: translateX(2px); }
.yh-settings-anchor__button:focus-visible { outline: 2px solid color-mix(in srgb, var(--color-primary, #4f8cff) 42%, transparent); outline-offset: -3px; border-radius: 10px; }
:global([data-mcr-theme="dark"]) .yh-settings-anchor__line { background: rgba(235, 235, 245, 0.22); }
:global([data-mcr-theme="dark"]) .yh-settings-anchor__button:hover .yh-settings-anchor__line, :global([data-mcr-theme="dark"]) .yh-settings-anchor__button:focus-visible .yh-settings-anchor__line { background: rgba(235, 235, 245, 0.5); }
:global([data-mcr-theme="dark"]) .yh-settings-anchor__button.is-active .yh-settings-anchor__line { background: var(--color-primary, #6ea2ff); }
@media (max-width: 1023px) { .yh-settings-anchor { display: none; } }
@media (prefers-reduced-motion: reduce) { .yh-settings-anchor__line { transition: none; } }
</style>
