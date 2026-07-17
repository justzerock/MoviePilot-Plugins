<template>
  <Teleport to="body">
    <Transition name="yh-history-expansion">
      <div v-if="open" class="yh-history-expansion" :data-mcr-theme="theme" @keydown.esc.prevent="emit('close')">
        <button type="button" class="yh-history-expansion__dismiss" aria-label="收起历史封面" @click="emit('close')" />
        <section ref="panelEl" class="yh-history-expansion__panel" :style="panelStyle" role="region" tabindex="-1" :aria-label="`${title} 的历史封面`">
          <header class="yh-history-expansion__header">
            <div><strong>{{ title }}</strong><span>{{ items.length }} 张封面</span></div>
            <div class="yh-history-expansion__actions">
              <button v-if="canRestore" type="button" class="yh-history-expansion__restore" :disabled="restoring" @click="emit('restore')">
                <v-icon icon="mdi-history" size="17" />
                <span>回溯</span>
              </button>
              <button type="button" class="yh-history-expansion__close" aria-label="收起" @click="emit('close')"><v-icon icon="mdi-close" size="19" /></button>
            </div>
          </header>
          <div class="yh-history-expansion__grid">
            <button v-for="item in items" :key="itemKey(item)" type="button" class="yh-history-expansion__card" :class="{ 'is-selected': selectedKeys.includes(selectionKey(item)), 'has-error': failedImages.has(itemKey(item)) }" :aria-selected="selectedKeys.includes(selectionKey(item))" @click="emit('select', item)">
              <span class="yh-history-expansion__image">
                <img v-if="!failedImages.has(itemKey(item))" :src="item.src || item.url || ''" :alt="item.library || item.name || '历史封面'" loading="lazy" @error="markFailed(item)">
                <span v-else><v-icon icon="mdi-image-off-outline" size="24" /></span>
                <i v-if="selectedKeys.includes(selectionKey(item))"><v-icon icon="mdi-check" size="16" /></i>
              </span>
              <span class="yh-history-expansion__meta"><strong :title="item.library || item.name || '未知媒体库'">{{ item.library || item.name || '未知媒体库' }}</strong><span :title="item.server || '未知服务器'">{{ item.server || '未知服务器' }}</span></span>
            </button>
          </div>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'

interface HistoryPosterItem { path: string; name?: string; src?: string; url?: string; server?: string; library?: string; cover_id?: string; history_record_id?: string; library_key?: string }
interface AnchorRect { left: number; top: number; width: number; height: number }
const props = withDefaults(defineProps<{ open: boolean; title: string; items: HistoryPosterItem[]; selectedKeys?: string[]; anchorRect?: AnchorRect | null; theme?: 'light' | 'dark'; canRestore?: boolean; restoring?: boolean }>(), { selectedKeys: () => [], anchorRect: null, theme: 'light', canRestore: false, restoring: false })
const emit = defineEmits<{ (event: 'close'): void; (event: 'restore'): void; (event: 'select', item: HistoryPosterItem): void }>()
const panelEl = ref<HTMLElement | null>(null)
const failedImages = ref(new Set<string>())
const itemKey = (item: HistoryPosterItem) => String(item.cover_id || item.history_record_id || item.library_key || item.path)
const selectionKey = (item: HistoryPosterItem) => String(item.path || itemKey(item))
function markFailed(item: HistoryPosterItem) { failedImages.value = new Set(failedImages.value).add(itemKey(item)) }
const panelStyle = computed(() => {
  if (!props.anchorRect || typeof window === 'undefined') return {}
  const x = props.anchorRect.left + props.anchorRect.width / 2 - window.innerWidth / 2
  const y = props.anchorRect.top + props.anchorRect.height / 2 - window.innerHeight / 2
  return { '--yh-expand-from-x': `${Math.round(x)}px`, '--yh-expand-from-y': `${Math.round(y)}px` }
})
watch(() => props.open, (open) => { if (open) void nextTick(() => panelEl.value?.focus({ preventScroll: true })) })
</script>

<style scoped>
.yh-history-expansion { position: fixed; inset: 0; z-index: 2147482900; display: grid; place-items: center; padding: clamp(16px, 4vw, 56px); pointer-events: none; }
.yh-history-expansion__dismiss { position: absolute; inset: 0; width: 100%; height: 100%; border: 0; background: color-mix(in srgb, var(--color-bg) 24%, transparent); pointer-events: auto; }
.yh-history-expansion__panel { --yh-expand-from-x: 0px; --yh-expand-from-y: 0px; width: min(980px, 100%); max-height: min(76vh, 760px); display: grid; grid-template-rows: auto minmax(0, 1fr); overflow: hidden; border: 1px solid rgba(255,255,255,.76); border-radius: 20px; background: rgba(245,245,247,.78); box-shadow: 0 20px 54px color-mix(in srgb, var(--color-shadow) 82%, transparent); backdrop-filter: blur(24px) saturate(135%); -webkit-backdrop-filter: blur(24px) saturate(135%); pointer-events: auto; }
[data-mcr-theme="dark"] .yh-history-expansion__panel { border-color: rgba(255,255,255,.15); background: rgba(28,28,30,.82); }
.yh-history-expansion__header { display:flex; align-items:center; justify-content:space-between; gap:16px; padding:14px 16px; border-bottom:1px solid var(--color-border); }
.yh-history-expansion__header > div { min-width:0; display:flex; align-items:baseline; gap:9px; }
.yh-history-expansion__header strong { overflow:hidden; color:var(--color-text-main); font-size:17px; text-overflow:ellipsis; white-space:nowrap; }
.yh-history-expansion__header span { color:var(--color-text-muted); font-size:12px; font-weight:700; white-space:nowrap; }
.yh-history-expansion__actions { flex:0 0 auto; display:flex !important; align-items:center !important; gap:8px !important; }
.yh-history-expansion__actions button { height:36px; display:inline-flex; align-items:center; justify-content:center; border:1px solid var(--color-border); border-radius:11px; background:var(--color-surface); color:var(--color-text-secondary); font:inherit; cursor:pointer; }
.yh-history-expansion__restore { gap:6px; min-width:76px; padding:0 12px; color:var(--color-primary) !important; border-color:color-mix(in srgb,var(--color-primary) 26%,var(--color-border)) !important; background:color-mix(in srgb,var(--color-primary-soft) 70%,var(--color-surface)) !important; font-size:12px !important; font-weight:800 !important; }
.yh-history-expansion__restore:disabled { cursor:wait; opacity:.56; }
.yh-history-expansion__close { width:36px; padding:0; }
.yh-history-expansion__grid { display:flex; flex-wrap:wrap; align-content:flex-start; justify-content:center; gap:14px; overflow:auto; padding:16px; overscroll-behavior:contain; }
.yh-history-expansion__card { width:clamp(190px,22vw,236px); min-width:190px; flex:0 0 auto; display:grid; gap:7px; padding:0; overflow:hidden; border:1px solid var(--color-border); border-radius:13px; background:var(--color-surface); color:var(--color-text-main); box-shadow:0 6px 16px var(--color-shadow); text-align:left; }
.yh-history-expansion__card.is-selected { border-color:var(--color-primary); background:var(--color-primary-soft); box-shadow:0 0 0 2px color-mix(in srgb,var(--color-primary) 18%,transparent),0 8px 18px var(--color-shadow); }
.yh-history-expansion__image { position:relative; aspect-ratio:16/9; display:grid; place-items:center; overflow:hidden; background:var(--color-surface-soft); color:var(--color-text-muted); }
.yh-history-expansion__image img { width:100%; height:100%; display:block; object-fit:cover; }
.yh-history-expansion__image i { position:absolute; top:8px; right:8px; width:28px; height:28px; display:grid; place-items:center; border-radius:9px; background:var(--color-primary); color:#fff; }
.yh-history-expansion__meta { min-width:0; display:flex; align-items:center; gap:6px; padding:0 9px 9px; font-size:11px; }
.yh-history-expansion__meta strong,.yh-history-expansion__meta span { min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.yh-history-expansion__meta strong { flex:1; color:var(--color-text-secondary); }.yh-history-expansion__meta span { max-width:42%; color:var(--color-text-muted); }.yh-history-expansion__meta span::before { content:'·'; margin-right:6px; }
.yh-history-expansion-enter-active,.yh-history-expansion-leave-active { transition:opacity 280ms ease; }.yh-history-expansion-enter-active .yh-history-expansion__panel,.yh-history-expansion-leave-active .yh-history-expansion__panel { transition:transform 300ms cubic-bezier(.2,.78,.25,1),opacity 220ms ease; }
.yh-history-expansion-enter-from,.yh-history-expansion-leave-to { opacity:0; }.yh-history-expansion-enter-from .yh-history-expansion__panel,.yh-history-expansion-leave-to .yh-history-expansion__panel { opacity:.2; transform:translate(var(--yh-expand-from-x),var(--yh-expand-from-y)) scale(.34); }
@supports not ((backdrop-filter:blur(1px)) or (-webkit-backdrop-filter:blur(1px))) { .yh-history-expansion__panel { background:var(--color-surface); } }
@media(max-width:768px){.yh-history-expansion{padding:12px}.yh-history-expansion__panel{max-height:82vh;border-radius:17px}.yh-history-expansion__grid{gap:9px;padding:10px}.yh-history-expansion__card{width:calc((100% - 9px)/2);min-width:0}.yh-history-expansion__header{padding:10px 12px}.yh-history-expansion__meta{font-size:10px}}
@media(max-width:340px){.yh-history-expansion__grid{gap:7px;padding:8px}.yh-history-expansion__card{width:calc((100% - 7px)/2)}.yh-history-expansion__meta{padding-inline:7px}}
@media(prefers-reduced-motion:reduce){.yh-history-expansion-enter-active,.yh-history-expansion-leave-active,.yh-history-expansion-enter-active .yh-history-expansion__panel,.yh-history-expansion-leave-active .yh-history-expansion__panel{transition:none}}
.yh-history-expansion__card { width:236px; min-width:236px; flex-basis:236px; }
@media(max-width:768px) { .yh-history-expansion__card { width:calc((100% - 9px)/2); min-width:0; flex-basis:calc((100% - 9px)/2); } }
@media(max-width:340px) { .yh-history-expansion__card { width:calc((100% - 7px)/2); flex-basis:calc((100% - 7px)/2); } }
</style>
