<template>
  <article
    ref="rootEl"
    class="yh-history-poster-stack"
    :class="[
      `is-${phase}`,
      { 'is-expanded': expanded, 'is-time-machine': mode === 'time-machine' },
    ]"
    :data-history-group="groupKey"
    :aria-expanded="expanded"
    tabindex="0"
    @keydown.enter.prevent="handlePrimaryAction"
    @keydown.space.prevent="handlePrimaryAction"
    @keydown.esc.prevent="emit('close')"
  >
    <header class="yh-history-poster-stack__header">
      <div class="yh-history-poster-stack__heading">
        <strong :title="title">{{ title }}</strong>
        <span>{{ items.length }} 张</span>
      </div>
      <button
        v-if="expanded"
        type="button"
        class="yh-history-poster-stack__close"
        aria-label="收起海报"
        @click.stop="emit('close')"
      >
        <v-icon icon="mdi-close" size="18" />
      </button>
    </header>

    <div
      class="yh-history-poster-stack__surface"
      :role="expanded ? 'group' : 'button'"
      :aria-label="expanded ? `${title} 的历史封面` : `展开 ${title} 的历史封面`"
      @click.self="expanded ? emit('close') : emit('toggle')"
    >
      <button
        v-for="(item, index) in items"
        :key="itemKey(item)"
        type="button"
        class="yh-history-poster-stack__poster"
        :class="{
          'is-selected': selectedKeys.includes(selectionKey(item)),
          'is-beyond-stack': !expanded && index >= stackLimit,
          'has-image-error': failedImages.has(itemKey(item)),
        }"
        :style="stackStyle(index)"
        :aria-selected="expanded ? selectedKeys.includes(selectionKey(item)) : undefined"
        :aria-label="expanded ? `选择 ${item.library || item.name || '封面'}` : `展开 ${title}`"
        :disabled="disabled"
        @click.stop="expanded ? emit('select', item) : emit('toggle')"
      >
        <span class="yh-history-poster-stack__image-shell">
          <img
            v-if="!failedImages.has(itemKey(item))"
            :src="item.src || item.url || ''"
            :alt="item.library || item.name || '历史封面'"
            loading="lazy"
            @error="markImageFailed(item)"
          >
          <span v-else class="yh-history-poster-stack__placeholder" aria-label="图片加载失败">
            <v-icon icon="mdi-image-off-outline" size="24" />
          </span>
          <span v-if="expanded && selectedKeys.includes(selectionKey(item))" class="yh-history-poster-stack__selected-mark" aria-hidden="true">
            <v-icon icon="mdi-check" size="17" />
          </span>
        </span>
        <span v-if="expanded" class="yh-history-poster-stack__meta">
          <strong :title="item.library || item.name || '未知媒体库'">{{ item.library || item.name || '未知媒体库' }}</strong>
          <span :title="item.server || '未知服务器'">{{ item.server || '未知服务器' }}</span>
        </span>
      </button>

      <span v-if="!expanded && items.length > stackLimit" class="yh-history-poster-stack__more">
        +{{ items.length - stackLimit }}
      </span>
    </div>
  </article>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'

interface HistoryPosterItem {
  path: string
  name?: string
  src?: string
  url?: string
  server?: string
  library?: string
  cover_id?: string
  history_record_id?: string
  library_key?: string
}

const props = withDefaults(defineProps<{
  groupKey: string
  title: string
  items: HistoryPosterItem[]
  expanded?: boolean
  phase?: 'collapsed' | 'expanding' | 'expanded' | 'collapsing'
  selectedKeys?: string[]
  stackLimit?: number
  mode?: 'time-machine' | 'library'
  disabled?: boolean
}>(), {
  expanded: false,
  phase: 'collapsed',
  selectedKeys: () => [],
  stackLimit: 5,
  mode: 'time-machine',
  disabled: false,
})

const emit = defineEmits<{
  (event: 'toggle'): void
  (event: 'close'): void
  (event: 'select', item: HistoryPosterItem): void
}>()

const rootEl = ref<HTMLElement | null>(null)
const failedImages = ref(new Set<string>())

function historyPosterItemKey(item: HistoryPosterItem) {
  return String(item.cover_id || item.history_record_id || item.library_key || item.path)
}

function itemKey(item: HistoryPosterItem) {
  return historyPosterItemKey(item)
}

function selectionKey(item: HistoryPosterItem) {
  return String(item.path || historyPosterItemKey(item))
}

function markImageFailed(item: HistoryPosterItem) {
  failedImages.value = new Set(failedImages.value).add(itemKey(item))
}

function stackStyle(index: number) {
  const offsets = [0, 18, 36, 54, 72]
  const vertical = [0, -5, 4, -2, 5]
  const rotation = [-1.4, 1.2, -0.7, 1.5, -1]
  const variant = index % offsets.length
  return {
    '--history-stack-index': String(index),
    '--history-stack-offset-x-current': `${offsets[variant]}px`,
    '--history-stack-hover-x-current': `${Math.round(offsets[variant] * 1.16)}px`,
    '--history-stack-offset-y-current': `${vertical[variant]}px`,
    '--history-stack-rotation-current': `${rotation[variant]}deg`,
    '--history-stack-z': String(30 - index),
  }
}

function handlePrimaryAction() {
  if (props.expanded) return
  emit('toggle')
}

watch(
  () => props.expanded,
  (expanded) => {
    if (!expanded) return
    void nextTick(() => rootEl.value?.focus({ preventScroll: true }))
  },
)
</script>

<style scoped>
.yh-history-poster-stack {
  --history-poster-width: clamp(140px, 18vw, 210px);
  --history-stack-offset-x: 18px;
  --history-stack-offset-y: 5px;
  --history-stack-rotation: 1.4deg;
  --history-glass-background: rgba(245, 245, 247, 0.72);
  --history-glass-border: rgba(255, 255, 255, 0.78);
  --history-glass-blur: 24px;
  --history-grid-gap: 14px;
  min-width: 0;
  padding: 10px;
  border: 1px solid transparent;
  border-radius: 18px;
  outline: none;
  transition: background-color 260ms ease, border-color 260ms ease, box-shadow 260ms ease;
}
.yh-history-poster-stack:focus-visible {
  border-color: color-mix(in srgb, var(--color-primary) 52%, transparent);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-primary) 16%, transparent);
}
.yh-history-poster-stack.is-expanded {
  grid-column: 1 / -1;
  background: var(--history-glass-background);
  border-color: var(--history-glass-border);
  box-shadow: 0 16px 38px color-mix(in srgb, var(--color-shadow) 76%, transparent);
  backdrop-filter: blur(var(--history-glass-blur)) saturate(135%);
  -webkit-backdrop-filter: blur(var(--history-glass-blur)) saturate(135%);
}
.yh-history-poster-stack__header {
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
}
.yh-history-poster-stack__heading {
  min-width: 0;
  display: flex;
  align-items: baseline;
  gap: 8px;
}
.yh-history-poster-stack__heading strong {
  min-width: 0;
  overflow: hidden;
  color: var(--color-text-main);
  font-size: 15px;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.yh-history-poster-stack__heading span {
  flex: 0 0 auto;
  color: var(--color-text-muted);
  font-size: 11px;
  font-weight: 700;
}
.yh-history-poster-stack__close {
  width: 34px;
  height: 34px;
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  border: 1px solid var(--color-border);
  border-radius: 11px;
  background: color-mix(in srgb, var(--color-surface) 84%, transparent);
  color: var(--color-text-secondary);
  cursor: pointer;
}
.yh-history-poster-stack__surface {
  position: relative;
  min-width: 0;
  height: calc(var(--history-poster-width) * .5625 + 18px);
  cursor: pointer;
  transition: height 280ms ease;
}
.yh-history-poster-stack.is-expanded .yh-history-poster-stack__surface {
  height: auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(190px, 100%), 1fr));
  gap: var(--history-grid-gap);
  cursor: default;
}
.yh-history-poster-stack__poster {
  position: absolute;
  top: 8px;
  left: max(0px, calc((100% - var(--history-poster-width) - 72px) / 2));
  z-index: var(--history-stack-z);
  width: var(--history-poster-width);
  display: grid;
  gap: 7px;
  padding: 0;
  border: 1px solid var(--color-border);
  border-radius: 13px;
  background: var(--color-surface);
  color: var(--color-text-main);
  cursor: pointer;
  box-shadow: 0 8px 20px var(--color-shadow);
  transform: translate(var(--history-stack-offset-x-current), var(--history-stack-offset-y-current)) rotate(var(--history-stack-rotation-current));
  transform-origin: center;
  transition: transform 280ms cubic-bezier(.2,.75,.25,1), width 280ms ease, box-shadow 220ms ease, border-color 180ms ease, opacity 180ms ease;
}
.yh-history-poster-stack:not(.is-expanded):hover .yh-history-poster-stack__poster {
  transform: translate(var(--history-stack-hover-x-current), var(--history-stack-offset-y-current)) rotate(var(--history-stack-rotation-current));
}
.yh-history-poster-stack.is-expanded .yh-history-poster-stack__poster {
  position: relative;
  inset: auto;
  z-index: auto;
  width: 100%;
  transform: none;
  box-shadow: 0 6px 16px color-mix(in srgb, var(--color-shadow) 62%, transparent);
}
.yh-history-poster-stack__poster.is-beyond-stack {
  visibility: hidden;
  opacity: 0;
  pointer-events: none;
}
.yh-history-poster-stack__poster.is-selected {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--color-primary) 20%, transparent), 0 8px 18px var(--color-shadow);
}
.yh-history-poster-stack__image-shell {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  display: block;
  overflow: hidden;
  border-radius: 12px;
  background: var(--color-surface-soft);
}
.yh-history-poster-stack__image-shell img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}
.yh-history-poster-stack__placeholder {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  color: var(--color-text-muted);
  background: var(--color-surface-soft);
}
.yh-history-poster-stack__selected-mark {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  border-radius: 9px;
  background: var(--color-primary);
  color: white;
}
.yh-history-poster-stack__meta {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 9px 9px;
  font-size: 11px;
}
.yh-history-poster-stack__meta strong,
.yh-history-poster-stack__meta span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.yh-history-poster-stack__meta strong {
  flex: 1 1 auto;
  color: var(--color-text-secondary);
}
.yh-history-poster-stack__meta span {
  max-width: 42%;
  color: var(--color-text-muted);
}
.yh-history-poster-stack__meta span::before {
  content: '·';
  margin-right: 6px;
}
.yh-history-poster-stack__more {
  position: absolute;
  right: 8px;
  bottom: 12px;
  z-index: 40;
  padding: 6px 9px;
  border-radius: 999px;
  background: var(--color-primary);
  color: white;
  box-shadow: 0 6px 14px var(--color-shadow);
  font-size: 11px;
  font-weight: 800;
}
:global([data-mcr-theme="dark"]) .yh-history-poster-stack {
  --history-glass-background: rgba(32, 32, 35, 0.78);
  --history-glass-border: rgba(255, 255, 255, 0.16);
}
@supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
  .yh-history-poster-stack.is-expanded {
    background: color-mix(in srgb, var(--color-surface) 96%, var(--color-surface-soft));
  }
}
@media (max-width: 1023px) {
  .yh-history-poster-stack {
    --history-poster-width: clamp(112px, 27vw, 150px);
    --history-grid-gap: 10px;
    padding: 8px;
  }
  .yh-history-poster-stack.is-expanded .yh-history-poster-stack__surface {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
@media (max-width: 430px) {
  .yh-history-poster-stack {
    --history-poster-width: clamp(90px, 28vw, 122px);
    padding: 6px;
  }
  .yh-history-poster-stack__heading strong {
    font-size: 13px;
  }
  .yh-history-poster-stack__poster {
    left: max(0px, calc((100% - var(--history-poster-width) - 48px) / 2));
  }
  .yh-history-poster-stack__meta {
    padding: 0 7px 7px;
    font-size: 10px;
  }
}
@media (prefers-reduced-motion: reduce) {
  .yh-history-poster-stack,
  .yh-history-poster-stack__surface,
  .yh-history-poster-stack__poster {
    transition: none;
  }
}
</style>
