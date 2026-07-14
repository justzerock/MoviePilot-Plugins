<template>
  <Teleport to="body"><nav class="yh-settings-anchor" :style="{ left: `${navLeft}px` }" :data-mcr-theme="theme" aria-label="设置分组导航">
    <v-tooltip v-for="section in sections" :key="section.id" location="end" :open-delay="220">
      <template #activator="{ props: tooltipProps }"><button v-bind="tooltipProps" type="button" class="yh-settings-anchor__button" :class="{ 'is-active': activeId === section.id }" :aria-label="`跳转到${section.label}`" :aria-current="activeId === section.id ? 'true' : undefined" @click="scrollToSection(section.id)"><span class="yh-settings-anchor__line" aria-hidden="true" /></button></template>
      <span>{{ section.label }}</span>
    </v-tooltip>
  </nav></Teleport>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
export interface SettingsAnchorSection { id: string; label: string }
const props = withDefaults(defineProps<{ sections: SettingsAnchorSection[]; contentElement?: HTMLElement | null; scrollContainer?: HTMLElement | null; topOffset?: number; theme?: 'light' | 'dark' }>(), { contentElement: null, scrollContainer: null, topOffset: 96, theme: 'light' })
const activeId = ref(props.sections[0]?.id || '')
const navLeft = ref(12)
const navWidth = 36
const viewportPadding = 12
let observer: IntersectionObserver | null = null
let resizeObserver: ResizeObserver | null = null
let scrollRoot: HTMLElement | null = null
let targetId = ''
let releaseFrame = 0
let releaseDeadline = 0
const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max)
function observedElements() { return props.sections.map((section) => document.getElementById(section.id)).filter((element): element is HTMLElement => Boolean(element)) }
function resolveScrollRoot() { scrollRoot = props.scrollContainer || null }
function updatePosition() { const rect = props.contentElement?.getBoundingClientRect(); const desired = rect ? rect.left - navWidth - 18 : viewportPadding; navLeft.value = Math.round(clamp(desired, viewportPadding, Math.max(viewportPadding, window.innerWidth - navWidth - viewportPadding))) }
function isAtBottom() { return scrollRoot ? scrollRoot.scrollTop + scrollRoot.clientHeight >= scrollRoot.scrollHeight - 2 : window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 2 }
function releaseProgrammaticScroll() { if (!targetId) return; const target = document.getElementById(targetId); const nearTarget = Boolean(target && Math.abs(target.getBoundingClientRect().top - props.topOffset) < 4); if (nearTarget || performance.now() >= releaseDeadline) { targetId = ''; releaseFrame = 0; return }; releaseFrame = requestAnimationFrame(releaseProgrammaticScroll) }
function cancelProgrammaticScroll() { targetId = ''; if (releaseFrame) cancelAnimationFrame(releaseFrame); releaseFrame = 0 }
function setupObserver() { observer?.disconnect(); resolveScrollRoot(); updatePosition(); const elements = observedElements(); if (!elements.length || typeof IntersectionObserver === 'undefined') return; observer = new IntersectionObserver((entries) => { if (targetId) return; if (isAtBottom() && props.sections.length) { activeId.value = props.sections.at(-1)?.id || activeId.value; return }; const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => Math.abs(a.boundingClientRect.top - props.topOffset) - Math.abs(b.boundingClientRect.top - props.topOffset)); if (visible[0]?.target.id) activeId.value = visible[0].target.id }, { root: scrollRoot, rootMargin: `-${props.topOffset}px 0px -62% 0px`, threshold: [0, .05, .25, .6] }); elements.forEach((element) => observer?.observe(element)) }
function scrollToSection(id: string) { const target = document.getElementById(id); if (!target) return; cancelProgrammaticScroll(); activeId.value = id; targetId = id; releaseDeadline = performance.now() + 1400; if (scrollRoot) { const rootRect = scrollRoot.getBoundingClientRect(); const targetTop = scrollRoot.scrollTop + target.getBoundingClientRect().top - rootRect.top - props.topOffset; const maxTop = Math.max(0, scrollRoot.scrollHeight - scrollRoot.clientHeight); scrollRoot.scrollTo({ top: clamp(targetTop, 0, maxTop), behavior: 'smooth' }) } else { const targetTop = target.getBoundingClientRect().top + window.scrollY - props.topOffset; const maxTop = Math.max(0, document.documentElement.scrollHeight - window.innerHeight); window.scrollTo({ top: clamp(targetTop, 0, maxTop), behavior: 'smooth' }) }; releaseFrame = requestAnimationFrame(releaseProgrammaticScroll) }
watch(() => [props.sections, props.scrollContainer, props.contentElement], () => void nextTick(setupObserver), { deep: true })
onMounted(() => void nextTick(() => { setupObserver(); if (typeof ResizeObserver !== 'undefined' && props.contentElement) { resizeObserver = new ResizeObserver(updatePosition); resizeObserver.observe(props.contentElement) } window.addEventListener('resize', updatePosition); window.addEventListener('wheel', cancelProgrammaticScroll, { passive: true }); window.addEventListener('touchstart', cancelProgrammaticScroll, { passive: true }); window.addEventListener('pointerdown', cancelProgrammaticScroll, { passive: true }) }))
onBeforeUnmount(() => { observer?.disconnect(); resizeObserver?.disconnect(); cancelProgrammaticScroll(); window.removeEventListener('resize', updatePosition); window.removeEventListener('wheel', cancelProgrammaticScroll); window.removeEventListener('touchstart', cancelProgrammaticScroll); window.removeEventListener('pointerdown', cancelProgrammaticScroll) })
</script>

<style scoped>
.yh-settings-anchor { position: fixed; top: 50%; z-index: 2147483000; width: 36px; height: max-content; margin: 0; padding: 4px 0; background: transparent; pointer-events: auto; transform: translateY(-50%); }
.yh-settings-anchor__button { width: 34px; height: 32px; display: grid; place-items: center; padding: 0; border: 0; background: transparent; cursor: pointer; }
.yh-settings-anchor__line { width: 16px; height: 2px; border-radius: 999px; background: rgba(60,60,67,.25); transition: width 180ms ease, opacity 180ms ease, background-color 180ms ease, transform 180ms ease; }
.yh-settings-anchor__button:hover .yh-settings-anchor__line, .yh-settings-anchor__button:focus-visible .yh-settings-anchor__line { width: 24px; background: rgba(60,60,67,.55); }
.yh-settings-anchor__button.is-active .yh-settings-anchor__line { width: 32px; background: var(--color-primary, #4f8cff); opacity: 1; transform: translateX(2px); }
.yh-settings-anchor__button:focus-visible { outline: 2px solid color-mix(in srgb, var(--color-primary, #4f8cff) 42%, transparent); outline-offset: -3px; border-radius: 10px; }
:global([data-mcr-theme="dark"]) .yh-settings-anchor__line { background: rgba(235,235,245,.22); }
:global([data-mcr-theme="dark"]) .yh-settings-anchor__button.is-active .yh-settings-anchor__line { background: var(--color-primary, #6ea2ff); }
@media (max-width: 480px) { .yh-settings-anchor { display: none; } }
@media (prefers-reduced-motion: reduce) { .yh-settings-anchor__line { transition: none; } }
</style>
