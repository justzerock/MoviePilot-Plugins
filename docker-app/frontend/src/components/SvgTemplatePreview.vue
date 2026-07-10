<template>
  <div
    class="mcr-svg-template-preview"
    :class="{
      'mcr-svg-template-preview--interactive': interactive,
      'mcr-svg-template-preview--transparent': template?.background?.type === 'transparent' || hasTextMaskLayer,
    }"
    @click="onPreviewClick"
    @pointerdown="onPreviewPointerDown"
    v-html="svgMarkup"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { CustomStaticLayout, PreviewSourcePayload, SimulationParams } from '../types/plugin'
import { renderTemplateSvg } from '../utils/svgTemplate'

const props = defineProps<{
  template: CustomStaticLayout | null | undefined
  source: PreviewSourcePayload | null
  params: SimulationParams
  selectedLayerId?: string | null
  interactive?: boolean
  autoBlendColor?: string
}>()

const emit = defineEmits<{
  (event: 'select-layer', id: string): void
  (event: 'layer-pointer-down', id: string, pointerEvent: PointerEvent): void
  (event: 'background-click'): void
}>()

const svgMarkup = computed(() =>
  renderTemplateSvg(props.template, props.source, props.params, {
    selectedLayerId: props.selectedLayerId,
    interactive: props.interactive,
    autoBlendColor: props.autoBlendColor,
  }),
)

const hasTextMaskLayer = computed(() => {
  const visit = (layers: any[]): boolean => layers.some((layer) => {
    if (!layer) return false
    if (layer.type === 'group') return visit(layer.children || [])
    return ['main_title', 'subtitle', 'title_zh', 'title_en', 'text'].includes(String(layer.type || ''))
      && ['knockout-text', 'show-text'].includes(String(layer.maskMode || 'normal'))
  })
  return visit(props.template?.layers || [])
})

function onPreviewClick(event: MouseEvent) {
  if (!props.interactive) return
  const target = event.target as Element | null
  const layerNode = target?.closest?.('[data-layer-id]')
  const layerId = layerNode?.getAttribute('data-layer-id')
  if (layerId) {
    emit('select-layer', layerId)
  } else {
    emit('background-click')
  }
}

function onPreviewPointerDown(event: PointerEvent) {
  if (!props.interactive || event.button > 0) return
  const target = event.target as Element | null
  const layerNode = target?.closest?.('[data-layer-id]')
  const layerId = layerNode?.getAttribute('data-layer-id')
  if (layerId) {
    emit('layer-pointer-down', layerId, event)
  }
}
</script>

<style scoped>
.mcr-svg-template-preview {
  width: 100%;
  height: 100%;
  background: var(--mcr-color-surface);
  overflow: hidden;
  contain: paint;
}

.mcr-svg-template-preview--transparent {
  background:
    linear-gradient(45deg, rgba(var(--mcr-rgb-outline-variant), 0.28) 25%, transparent 25%),
    linear-gradient(-45deg, rgba(var(--mcr-rgb-outline-variant), 0.28) 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, rgba(var(--mcr-rgb-outline-variant), 0.28) 75%),
    linear-gradient(-45deg, transparent 75%, rgba(var(--mcr-rgb-outline-variant), 0.28) 75%),
    var(--mcr-color-surface-container-lowest);
  background-position: 0 0, 0 8px, 8px -8px, -8px 0;
  background-size: 16px 16px;
}

.mcr-svg-template-preview :deep(svg) {
  display: block;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.mcr-svg-template-preview--interactive {
  user-select: none;
  cursor: default;
}

.mcr-svg-template-preview--interactive :deep([data-layer-id]) {
  cursor: move;
}
</style>
