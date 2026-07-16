<template>
  <Teleport to="body">
    <nav
      v-if="navigationEnabled"
      class="yh-settings-anchor"
      :style="{ left: `${navLeft}px` }"
      :data-mcr-theme="theme"
      aria-label="设置分组导航"
    >
      <v-tooltip v-for="section in sections" :key="section.id" location="end" :open-delay="220">
        <template #activator="{ props: tooltipProps }">
          <button
            v-bind="tooltipProps"
            type="button"
            class="yh-settings-anchor__button"
            :class="{ 'is-active': activeId === section.id }"
            :aria-label="`跳转到${section.label}`"
            :aria-current="activeId === section.id ? 'true' : undefined"
            @pointerdown.prevent
            @click="scrollToSection(section.id)"
          >
            <span class="yh-settings-anchor__line" aria-hidden="true" />
          </button>
        </template>
        <span>{{ section.label }}</span>
      </v-tooltip>
    </nav>
  </Teleport>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

export interface SettingsAnchorSection { id: string; label: string }

const props = withDefaults(defineProps<{
  sections: SettingsAnchorSection[]
  contentElement?: HTMLElement | null
  scrollContainer?: HTMLElement | null
  topOffset?: number
  theme?: 'light' | 'dark'
  desktopMinWidth?: number
}>(), {
  contentElement: null,
  scrollContainer: null,
  topOffset: 96,
  theme: 'light',
  desktopMinWidth: 1024,
})

const activeId = ref(props.sections[0]?.id || '')
const navLeft = ref(12)
const navigationEnabled = ref(false)
const navWidth = 36
const viewportPadding = 12
const anchorGap = 18
let observer: IntersectionObserver | null = null
let resizeObserver: ResizeObserver | null = null
let scrollRoot: HTMLElement | null = null
let targetId = ''
let releaseFrame = 0
let releaseDeadline = 0
let scrollFrame = 0

const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max)

function findSectionElement(id: string) {
  return props.contentElement?.querySelector<HTMLElement>(`#${CSS.escape(id)}`)
    || document.getElementById(id)
}

function observedElements() {
  return props.sections
    .map((section) => findSectionElement(section.id))
    .filter((element): element is HTMLElement => Boolean(element))
}

function isScrollable(element: HTMLElement) {
  const style = window.getComputedStyle(element)
  const overflowY = style.overflowY
  return /(auto|scroll|overlay)/.test(overflowY) && element.scrollHeight > element.clientHeight + 2
}

function resolveScrollRoot() {
  if (props.scrollContainer && isScrollable(props.scrollContainer)) {
    scrollRoot = props.scrollContainer
    return
  }
  let current: HTMLElement | null = props.contentElement || null
  while (current && current !== document.body && current !== document.documentElement) {
    if (isScrollable(current)) {
      scrollRoot = current
      return
    }
    current = current.parentElement
  }
  scrollRoot = null
}

function updatePosition() {
  if (!navigationEnabled.value) return
  const rect = props.contentElement?.getBoundingClientRect()
  const host = props.contentElement?.closest<HTMLElement>('.mcr-config-app, .mcr-frame')
  const hostRect = host?.getBoundingClientRect()
  const minLeft = Math.max(viewportPadding, (hostRect?.left ?? 0) + 8)
  const maxLeft = Math.max(
    minLeft,
    Math.min(
      window.innerWidth - navWidth - viewportPadding,
      (hostRect?.right ?? window.innerWidth) - navWidth - 8,
    ),
  )
  const outsideLeft = rect ? rect.left - navWidth - anchorGap : minLeft
  const desiredLeft = outsideLeft >= minLeft ? outsideLeft : minLeft
  navLeft.value = Math.round(clamp(desiredLeft, minLeft, maxLeft))
}

function currentScrollTop() {
  return scrollRoot ? scrollRoot.scrollTop : window.scrollY
}

function maxScrollTop() {
  return scrollRoot
    ? Math.max(0, scrollRoot.scrollHeight - scrollRoot.clientHeight)
    : Math.max(0, document.documentElement.scrollHeight - window.innerHeight)
}

function sectionDistanceFromAnchor(target: HTMLElement) {
  const targetRect = target.getBoundingClientRect()
  if (!scrollRoot) return targetRect.top - props.topOffset
  const rootRect = scrollRoot.getBoundingClientRect()
  return targetRect.top - rootRect.top - props.topOffset
}

function targetScrollTop(target: HTMLElement) {
  return clamp(currentScrollTop() + sectionDistanceFromAnchor(target), 0, maxScrollTop())
}

function isAtBottom() {
  return currentScrollTop() >= maxScrollTop() - 2
}

function refreshActiveSection() {
  if (!navigationEnabled.value || targetId) return
  const elements = observedElements()
  if (!elements.length) return
  if (isAtBottom()) {
    activeId.value = props.sections.at(-1)?.id || activeId.value
    return
  }
  const nearest = elements
    .map((element) => ({ element, distance: Math.abs(sectionDistanceFromAnchor(element)) }))
    .sort((a, b) => a.distance - b.distance)[0]
  if (nearest?.element.id) activeId.value = nearest.element.id
}

function scheduleScrollUpdate() {
  if (scrollFrame) return
  scrollFrame = window.requestAnimationFrame(() => {
    scrollFrame = 0
    refreshActiveSection()
    updatePosition()
  })
}

function finishProgrammaticScroll() {
  if (!targetId) return
  targetId = ''
  if (releaseFrame) window.cancelAnimationFrame(releaseFrame)
  releaseFrame = 0
  refreshActiveSection()
}

function monitorProgrammaticScroll() {
  if (!targetId) return
  const target = findSectionElement(targetId)
  const nearTarget = Boolean(target && Math.abs(sectionDistanceFromAnchor(target)) <= 3)
  const atBoundary = currentScrollTop() <= 1 || isAtBottom()
  if (nearTarget || atBoundary || performance.now() >= releaseDeadline) {
    finishProgrammaticScroll()
    return
  }
  releaseFrame = window.requestAnimationFrame(monitorProgrammaticScroll)
}

function cancelProgrammaticScroll() {
  finishProgrammaticScroll()
}

function scrollToSection(id: string) {
  const target = findSectionElement(id)
  if (!target) return
  finishProgrammaticScroll()
  if (scrollRoot && !scrollRoot.isConnected) {
    unbindScrollTarget()
    resolveScrollRoot()
    bindScrollTarget()
  }
  activeId.value = id
  targetId = id
  releaseDeadline = performance.now() + 1800
  const top = targetScrollTop(target)
  if (scrollRoot) scrollRoot.scrollTo({ top, behavior: 'smooth' })
  else window.scrollTo({ top, behavior: 'smooth' })
  releaseFrame = window.requestAnimationFrame(monitorProgrammaticScroll)
}

function bindScrollTarget() {
  if (scrollRoot) {
    scrollRoot.addEventListener('scroll', scheduleScrollUpdate, { passive: true })
    scrollRoot.addEventListener('scrollend', finishProgrammaticScroll)
  } else {
    window.addEventListener('scroll', scheduleScrollUpdate, { passive: true })
    window.addEventListener('scrollend', finishProgrammaticScroll)
  }
}

function unbindScrollTarget() {
  scrollRoot?.removeEventListener('scroll', scheduleScrollUpdate)
  scrollRoot?.removeEventListener('scrollend', finishProgrammaticScroll)
  window.removeEventListener('scroll', scheduleScrollUpdate)
  window.removeEventListener('scrollend', finishProgrammaticScroll)
}

function syncResizeObserver() {
  if (!navigationEnabled.value || typeof ResizeObserver === 'undefined' || !props.contentElement) {
    resizeObserver?.disconnect()
    resizeObserver = null
    return
  }
  if (resizeObserver) return
  resizeObserver = new ResizeObserver(handleResize)
  resizeObserver.observe(props.contentElement)
}

function setupNavigation() {
  const shouldEnable = window.innerWidth >= props.desktopMinWidth
  navigationEnabled.value = shouldEnable
  observer?.disconnect()
  observer = null
  unbindScrollTarget()
  if (!shouldEnable) {
    finishProgrammaticScroll()
    syncResizeObserver()
    return
  }
  resolveScrollRoot()
  bindScrollTarget()
  updatePosition()
  const elements = observedElements()
  if (elements.length && typeof IntersectionObserver !== 'undefined') {
    observer = new IntersectionObserver(() => refreshActiveSection(), {
      root: scrollRoot,
      rootMargin: `-${props.topOffset}px 0px -58% 0px`,
      threshold: [0, 0.05, 0.25, 0.6],
    })
    elements.forEach((element) => observer?.observe(element))
  }
  refreshActiveSection()
  syncResizeObserver()
}

function handleResize() {
  void nextTick(setupNavigation)
}

watch(
  () => [props.sections, props.scrollContainer, props.contentElement, props.topOffset, props.desktopMinWidth],
  () => void nextTick(setupNavigation),
  { deep: true },
)

onMounted(() => void nextTick(() => {
  setupNavigation()
  window.addEventListener('resize', handleResize)
  window.addEventListener('wheel', cancelProgrammaticScroll, { passive: true })
  window.addEventListener('touchstart', cancelProgrammaticScroll, { passive: true })
  window.addEventListener('pointerdown', cancelProgrammaticScroll, { passive: true })
}))

onBeforeUnmount(() => {
  observer?.disconnect()
  resizeObserver?.disconnect()
  unbindScrollTarget()
  finishProgrammaticScroll()
  if (scrollFrame) window.cancelAnimationFrame(scrollFrame)
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('wheel', cancelProgrammaticScroll)
  window.removeEventListener('touchstart', cancelProgrammaticScroll)
  window.removeEventListener('pointerdown', cancelProgrammaticScroll)
})
</script>

<style scoped>
.yh-settings-anchor { position: fixed; top: 50%; z-index: 2147483000; width: 36px; height: max-content; margin: 0; padding: 4px 0; background: transparent; pointer-events: auto; transform: translateY(-50%); }
.yh-settings-anchor__button { width: 34px; height: 32px; display: grid; place-items: center; padding: 0; border: 0; border-radius: 10px; background: transparent; cursor: pointer; touch-action: manipulation; transition: transform 100ms ease-out, background-color 180ms ease; }
.yh-settings-anchor__button:active { transform: scale(.94); background: rgba(0,122,255,.08); }
.yh-settings-anchor__line { width: 16px; height: 2px; border-radius: 999px; background: rgba(60,60,67,.25); transition: width 220ms cubic-bezier(.2,.78,.25,1), opacity 180ms ease, background-color 180ms ease, transform 220ms cubic-bezier(.2,.78,.25,1); }
.yh-settings-anchor__button:hover .yh-settings-anchor__line, .yh-settings-anchor__button:focus-visible .yh-settings-anchor__line { width: 24px; background: rgba(60,60,67,.55); }
.yh-settings-anchor__button.is-active .yh-settings-anchor__line { width: 32px; background: #007aff; opacity: 1; transform: translateX(2px); }
.yh-settings-anchor__button:focus-visible { outline: 2px solid color-mix(in srgb, var(--color-primary, #4f8cff) 42%, transparent); outline-offset: -3px; border-radius: 10px; }
:global([data-mcr-theme="dark"]) .yh-settings-anchor__line { background: rgba(235,235,245,.22); }
:global([data-mcr-theme="dark"]) .yh-settings-anchor__button.is-active .yh-settings-anchor__line { background: #0a84ff; }
@media (prefers-reduced-motion: reduce) { .yh-settings-anchor__line { transition: none; } }
</style>
