<template>
  <div class="simulation-shell">
    <div v-if="!source || !source.images.length" class="simulation-empty">
      <div class="text-subtitle-2 mb-2">暂无可用预览素材</div>
      <div class="text-caption text-medium-emphasis">请先配置媒体库或自定义图片目录。</div>
    </div>

    <div
      v-else
      class="simulation-canvas"
      :style="canvasStyle"
    >
      <div
        ref="previewStageEl"
        class="sim-stage-shell"
        :class="{ 'sim-stage-shell--layout': usesEditorLayoutPreview }"
      >
        <SvgTemplatePreview
          v-if="usesEditorLayoutPreview"
          class="sim-layout-preview"
          :template="source?.custom_static_layout"
          :source="source"
          :params="params"
          :auto-blend-color="autoBlendColor"
        />
        <div v-else class="sim-stage" :style="previewStageFixedStyle">
      <template v-if="styleBase === 'static_1'">
        <div class="sim-bg" :style="backgroundStyle" />
        <div class="sim-overlay" :style="overlayStyle" />
        <div v-if="shouldUseLayoutDrivenPresetStage" class="sim-custom-stage-shell">
          <div class="sim-custom-stage">
            <div
              v-for="layer in sortedLayers"
              :key="layer.id"
              class="sim-custom-layer"
              :style="getLayerStyle(layer)"
            >
              <template v-if="layer.type === 'image'">
                <img
                  v-if="getLayerPreviewImage(layer)?.src"
                  class="sim-custom-image"
                  :src="getLayerPreviewImage(layer)?.src"
                  :alt="getLayerPreviewImage(layer)?.label || `image-${layer.sourceIndex}`"
                  :style="getImageStyle(layer)"
                />
              </template>
              <template v-else-if="layer.type === 'main_title' || layer.type === 'title_zh'">
                <div class="sim-custom-text sim-custom-text-zh" :style="getTitleStyle(layer)">
                  <span
                    v-for="(line, index) in getMeasuredLayerLines(layer)"
                    :key="`${layer.id}-zh-${index}`"
                    class="sim-custom-text-line"
                    :style="getMeasuredLineStyle(layer, index)"
                  >
                    {{ line.text }}
                  </span>
                </div>
              </template>
              <template v-else>
                <div class="sim-custom-text sim-custom-text-en" :style="getTitleStyle(layer)">
                  <span
                    v-for="(line, index) in getMeasuredLayerLines(layer)"
                    :key="`${layer.id}-text-${index}`"
                    class="sim-custom-text-line"
                    :style="getMeasuredLineStyle(layer, index)"
                  >
                    {{ line.text }}
                  </span>
                </div>
              </template>
            </div>
          </div>
        </div>
        <div v-else class="sim-grid sim-grid-style-1">
          <div class="sim-style-1-copy">
            <div class="sim-title-zh" :style="mainTitleStyle">{{ titles.zh || '未配置中文标题' }}</div>
            <div class="sim-title-en" :style="subtitleStyle">{{ titles.en || 'UNTITLED' }}</div>
          </div>
          <div class="sim-style-1-stage">
            <div class="sim-style-1-card sim-style-1-card-back" />
            <div class="sim-style-1-card sim-style-1-card-mid" />
            <div class="sim-style-1-card sim-style-1-card-front">
              <img class="sim-main-image" :src="firstImage?.src" :alt="firstImage?.label || 'preview image'" />
            </div>
          </div>
        </div>
      </template>

      <template v-else-if="styleBase === 'static_2'">
        <div class="sim-bg" :style="backgroundStyle" />
        <div class="sim-overlay" :style="overlayStyle" />
        <div v-if="shouldUseLayoutDrivenPresetStage" class="sim-custom-stage-shell">
          <div class="sim-custom-stage">
            <div
              v-for="layer in sortedLayers"
              :key="layer.id"
              class="sim-custom-layer"
              :style="getLayerStyle(layer)"
            >
              <template v-if="layer.type === 'image'">
                <img
                  v-if="getLayerPreviewImage(layer)?.src"
                  class="sim-custom-image"
                  :src="getLayerPreviewImage(layer)?.src"
                  :alt="getLayerPreviewImage(layer)?.label || `image-${layer.sourceIndex}`"
                  :style="getImageStyle(layer)"
                />
              </template>
              <template v-else-if="layer.type === 'main_title' || layer.type === 'title_zh'">
                <div class="sim-custom-text sim-custom-text-zh" :style="getTitleStyle(layer)">
                  <span
                    v-for="(line, index) in getMeasuredLayerLines(layer)"
                    :key="`${layer.id}-zh-${index}`"
                    class="sim-custom-text-line"
                    :style="getMeasuredLineStyle(layer, index)"
                  >
                    {{ line.text }}
                  </span>
                </div>
              </template>
              <template v-else>
                <div class="sim-custom-text sim-custom-text-en" :style="getTitleStyle(layer)">
                  <span
                    v-for="(line, index) in getMeasuredLayerLines(layer)"
                    :key="`${layer.id}-text-${index}`"
                    class="sim-custom-text-line"
                    :style="getMeasuredLineStyle(layer, index)"
                  >
                    {{ line.text }}
                  </span>
                </div>
              </template>
            </div>
          </div>
        </div>
        <template v-else>
          <div class="sim-style-2-shadow" />
          <div class="sim-style-2-foreground">
            <img class="sim-style-2-image" :src="firstImage?.src" :alt="firstImage?.label || 'preview image'" />
          </div>
        </template>
        <div v-if="!shouldUseLayoutDrivenPresetStage" class="sim-grid sim-grid-style-2">
          <div class="sim-style-2-copy">
            <div class="sim-title-zh" :style="mainTitleStyle">{{ titles.zh || '未配置中文标题' }}</div>
            <div class="sim-title-en" :style="subtitleStyle">{{ titles.en || 'UNTITLED' }}</div>
          </div>
        </div>
      </template>

      <template v-else-if="styleBase === 'static_3'">
        <div class="sim-style-3-bg" :style="style3BackgroundStyle" />
        <div v-if="shouldUseLayoutDrivenPresetStage" class="sim-custom-stage-shell">
          <div class="sim-custom-stage">
            <div
              v-for="layer in sortedLayers"
              :key="layer.id"
              class="sim-custom-layer"
              :style="getLayerStyle(layer)"
            >
              <template v-if="layer.type === 'image'">
                <img
                  v-if="getLayerPreviewImage(layer)?.src"
                  class="sim-custom-image"
                  :src="getLayerPreviewImage(layer)?.src"
                  :alt="getLayerPreviewImage(layer)?.label || `image-${layer.sourceIndex}`"
                  :style="getImageStyle(layer)"
                />
              </template>
              <template v-else-if="layer.type === 'main_title' || layer.type === 'title_zh'">
                <div class="sim-custom-text sim-custom-text-zh" :style="getTitleStyle(layer)">
                  <span
                    v-for="(line, index) in getMeasuredLayerLines(layer)"
                    :key="`${layer.id}-zh-${index}`"
                    class="sim-custom-text-line"
                    :style="getMeasuredLineStyle(layer, index)"
                  >
                    {{ line.text }}
                  </span>
                </div>
              </template>
              <template v-else>
                <div class="sim-custom-text sim-custom-text-en" :style="getTitleStyle(layer)">
                  <span
                    v-for="(line, index) in getMeasuredLayerLines(layer)"
                    :key="`${layer.id}-text-${index}`"
                    class="sim-custom-text-line"
                    :style="getMeasuredLineStyle(layer, index)"
                  >
                    {{ line.text }}
                  </span>
                </div>
              </template>
            </div>
          </div>
        </div>
        <template v-else>
        <div class="sim-style-3-header">
          <div class="sim-style-3-title" :style="mainTitleStyle">{{ titles.zh || '未配置中文标题' }}</div>
          <div class="sim-style-3-subtitle-row">
            <div class="sim-style-3-accent" :style="style3AccentStyle" />
            <div class="sim-style-3-subtitle" :style="subtitleStyle">
              <span
                v-for="(line, index) in style3SubtitleLines"
                :key="`style3-subtitle-${index}`"
                class="sim-style-3-subtitle-line"
              >
                {{ line }}
              </span>
            </div>
          </div>
        </div>
        <div class="sim-style-3-stage">
          <div
            v-for="(column, columnIndex) in style3Columns"
            :key="`column-${columnIndex}`"
            class="sim-style-3-column"
            :class="`sim-style-3-column-${columnIndex + 1}`"
          >
            <div
              v-for="image in column"
              :key="image.key"
              class="sim-style-3-item"
            >
              <img :src="image.src" :alt="image.label || `image-${image.slot}`" />
            </div>
          </div>
        </div>
        </template>
      </template>

      <template v-else-if="styleBase === 'static_4'">
        <div class="sim-bg" :style="fullBackgroundStyle" />
        <div class="sim-overlay sim-overlay-strong" :style="overlayStyle" />
        <div v-if="shouldUseLayoutDrivenPresetStage" class="sim-custom-stage-shell">
          <div class="sim-custom-stage">
            <div
              v-for="layer in sortedLayers"
              :key="layer.id"
              class="sim-custom-layer"
              :style="getLayerStyle(layer)"
            >
              <template v-if="layer.type === 'image'">
                <img
                  v-if="getLayerPreviewImage(layer)?.src"
                  class="sim-custom-image"
                  :src="getLayerPreviewImage(layer)?.src"
                  :alt="getLayerPreviewImage(layer)?.label || `image-${layer.sourceIndex}`"
                  :style="getImageStyle(layer)"
                />
              </template>
              <template v-else-if="layer.type === 'main_title' || layer.type === 'title_zh'">
                <div class="sim-custom-text sim-custom-text-zh" :style="getTitleStyle(layer)">
                  <span
                    v-for="(line, index) in getMeasuredLayerLines(layer)"
                    :key="`${layer.id}-zh-${index}`"
                    class="sim-custom-text-line"
                    :style="getMeasuredLineStyle(layer, index)"
                  >
                    {{ line.text }}
                  </span>
                </div>
              </template>
              <template v-else>
                <div class="sim-custom-text sim-custom-text-en" :style="getTitleStyle(layer)">
                  <span
                    v-for="(line, index) in getMeasuredLayerLines(layer)"
                    :key="`${layer.id}-text-${index}`"
                    class="sim-custom-text-line"
                    :style="getMeasuredLineStyle(layer, index)"
                  >
                    {{ line.text }}
                  </span>
                </div>
              </template>
            </div>
          </div>
        </div>
        <div v-else class="sim-style-4-copy">
          <div class="sim-title-zh sim-title-center" :style="mainTitleStyle">{{ titles.zh || '未配置中文标题' }}</div>
          <div class="sim-title-en sim-title-center" :style="subtitleStyle">{{ titles.en || 'UNTITLED' }}</div>
        </div>
      </template>

      <template v-else>
        <div class="sim-bg" :style="backgroundStyle" />
        <div class="sim-overlay" :style="overlayStyle" />
        <div v-if="hasCustomLayout" class="sim-custom-stage-shell">
          <div class="sim-custom-stage">
            <div
              v-for="layer in sortedLayers"
              :key="layer.id"
              class="sim-custom-layer"
              :style="getLayerStyle(layer)"
            >
              <template v-if="layer.type === 'image'">
                <img
                  v-if="getLayerPreviewImage(layer)?.src"
                  class="sim-custom-image"
                  :src="getLayerPreviewImage(layer)?.src"
                  :alt="getLayerPreviewImage(layer)?.label || `image-${layer.sourceIndex}`"
                  :style="getImageStyle(layer)"
                />
              </template>
              <template v-else-if="layer.type === 'main_title' || layer.type === 'title_zh'">
                <div class="sim-custom-text sim-custom-text-zh" :style="getTitleStyle(layer)">
                  <span
                    v-for="(line, index) in getMeasuredLayerLines(layer)"
                    :key="`${layer.id}-zh-${index}`"
                    class="sim-custom-text-line"
                    :style="getMeasuredLineStyle(layer, index)"
                  >
                    {{ line.text }}
                  </span>
                </div>
              </template>
              <template v-else>
                <div class="sim-custom-text sim-custom-text-en" :style="getTitleStyle(layer)">
                  <span
                    v-for="(line, index) in getMeasuredLayerLines(layer)"
                    :key="`${layer.id}-text-${index}`"
                    class="sim-custom-text-line"
                    :style="getMeasuredLineStyle(layer, index)"
                  >
                    {{ line.text }}
                  </span>
                </div>
              </template>
            </div>
          </div>
        </div>
        <div v-else class="sim-custom-empty">
          <div class="text-subtitle-2 mb-2">当前未配置自定义布局</div>
          <div class="text-caption text-medium-emphasis">先在“自定义风格”页保存一个方案，再回到这里预览。</div>
        </div>
      </template>
        </div>
      </div>

      <div v-if="variant === 'animated'" class="sim-live-badge" aria-label="动态预览" title="动态预览">
        <span class="sim-live-icon" aria-hidden="true">
          <span />
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import type {
  CustomTextFontFamily,
  CustomMeasuredTextLayout,
  CustomImageLayer,
  CustomStaticLayout,
  CustomTextLayer,
  CustomTitleLayer,
  PreviewSourceImage,
  PreviewSourcePayload,
  SimulationParams,
} from '../types/plugin'
import { getLayerShadowStyle, isCustomTextLayer, normalizeLayerEffects } from '../utils/customLayout'
import {
  buildBackgroundStyle,
  buildOverlayStyle,
  darkenHexColor,
  extractComfortableColor,
  getDocumentSize,
  getLayerFrameStyle,
  getLayerTransformStyle,
  getPreviewFontFamily,
  hexToRgba,
  lightenHexColor,
  resolveBlendColor,
} from '../utils/renderSimulation'
import SvgTemplatePreview from './SvgTemplatePreview.vue'
import { getTemplateFontFaceName } from '../constants/fonts'
import { getThemeColor } from '../utils/themeColors'

const props = defineProps<{
  source: PreviewSourcePayload | null
  params: SimulationParams
}>()

const styleBase = computed(() => props.source?.cover_style_base || 'static_1')
const variant = computed(() => props.source?.cover_style_variant || 'static')
const titles = computed(() => props.source?.titles || { zh: '', en: '' })
const firstImage = computed(() => props.source?.images?.[0] || null)
const autoBlendColor = ref(getThemeColor('--mcr-cover-auto-blend'))
const previewStageEl = ref<HTMLElement | null>(null)
const previewStageScale = ref(1)
const loadedFontUrls = new Map<string, Promise<void>>()
const textMeasureCanvas = typeof document !== 'undefined' ? document.createElement('canvas') : null
let previewStageResizeObserver: ResizeObserver | null = null
const sortedLayers = computed(() => {
  const layout = props.source?.custom_static_layout as CustomStaticLayout | null | undefined
  return [...(layout?.layers || [])].sort((a, b) => (a.zIndex || 0) - (b.zIndex || 0))
})
const hasCustomLayout = computed(() => sortedLayers.value.length > 0)
const shouldUseLayoutDrivenPresetStage = computed(() =>
  hasCustomLayout.value && styleBase.value !== 'custom_static',
)
const usesEditorLayoutPreview = computed(() =>
  hasCustomLayout.value && (styleBase.value === 'custom_static' || shouldUseLayoutDrivenPresetStage.value),
)
const style3Images = computed(() => {
  const sourceImages = props.source?.images || []
  if (!sourceImages.length) return []
  const style3Order = [3, 1, 5, 4, 2, 6, 9, 8, 7]
  return style3Order.map((slotNumber, index) => {
    const image = sourceImages[(slotNumber - 1) % sourceImages.length]
    return {
      ...image,
      key: `${image.slot}-${slotNumber}-${index}`,
      slot: slotNumber,
    }
  })
})
const style3Columns = computed(() => [
  style3Images.value.slice(0, 3),
  style3Images.value.slice(3, 6),
  style3Images.value.slice(6, 9),
])

const documentSize = computed(() => getDocumentSize(props.source?.custom_static_layout))

const backgroundStyle = computed(() => buildBackgroundStyle(firstImage.value?.src, props.params.blur))

const fullBackgroundStyle = computed(() => buildBackgroundStyle(firstImage.value?.src, props.params.blur, true))

const effectiveBlendColor = computed(() => {
  return resolveBlendColor(props.source, props.params, autoBlendColor.value)
})

const overlayStyle = computed(() => buildOverlayStyle(effectiveBlendColor.value, props.params.colorRatio))

const canvasStyle = computed(() => ({
  backgroundColor: effectiveBlendColor.value,
}))
const mainTitleStyle = computed(() => ({
  fontFamily: getPreviewFontFamily('main_title', titles.value.zh),
}))
const subtitleStyle = computed(() => ({
  fontFamily: getPreviewFontFamily('subtitle', titles.value.en),
}))
const previewStageFixedStyle = computed(() => ({
  transform: `scale(${previewStageScale.value})`,
  width: `${documentSize.value.width}px`,
  height: `${documentSize.value.height}px`,
  '--sim-main-image': firstImage.value?.src ? `url(${firstImage.value.src})` : 'none',
}))
const style3BackgroundStyle = computed(() => {
  const base = effectiveBlendColor.value
  return {
    background: `linear-gradient(90deg, ${hexToRgba(darkenHexColor(base, 0.08), 1)} 0%, ${hexToRgba(lightenHexColor(base, 0.24), 0.92)} 100%)`,
  }
})
const style3AccentStyle = computed(() => ({
  background: lightenHexColor(effectiveBlendColor.value, 0.08),
}))
const style3SubtitleLines = computed(() => {
  const text = (titles.value.en || 'UNTITLED').trim()
  if (!text) return ['UNTITLED']
  const words = text.split(/\s+/).filter(Boolean)
  if (words.length <= 1) return [text]
  if (text.length <= 16 && words.length <= 3) return [text]

  let bestSplitIndex = 1
  let bestScore = Number.POSITIVE_INFINITY
  for (let index = 1; index < words.length; index += 1) {
    const first = words.slice(0, index).join(' ')
    const second = words.slice(index).join(' ')
    const balancePenalty = Math.abs(first.length - second.length)
    const midpointPenalty = Math.abs(index - words.length / 2) * 0.6
    const score = balancePenalty + midpointPenalty
    if (score < bestScore) {
      bestScore = score
      bestSplitIndex = index
    }
  }

  return [
    words.slice(0, bestSplitIndex).join(' '),
    words.slice(bestSplitIndex).join(' '),
  ]
})

function getCustomLayerText(layer: CustomTitleLayer | CustomTextLayer) {
  if (isCustomTextLayer(layer)) {
    const fallback = layer.content || '未定义文本'
    if ((layer.contentSource || 'fixed') !== 'library') return fallback
    const customTexts = props.source?.custom_texts || {}
    const key = String(layer.contentKey || '').trim()
    if (key && customTexts[key]) return customTexts[key]
    for (const defaultKey of ['default', 'text', 'custom_text', 'content']) {
      if (customTexts[defaultKey]) return customTexts[defaultKey]
    }
    return fallback
  }
  if (layer.type === 'main_title' || layer.type === 'title_zh') {
    return titles.value.zh || '未定义主标题'
  }
  return titles.value.en || '未定义副标题'
}

function getLayerImage(sourceIndex: number): PreviewSourceImage | undefined {
  return props.source?.images.find((image) => image.slot === sourceIndex)
}

function getStickerPathUrl(path: string | undefined) {
  const normalized = String(path || '').trim()
  return normalized
    ? `/api/v1/plugin/YahahaCoverStudio/saved_cover_image?file=${encodeURIComponent(normalized)}`
    : ''
}

function normalizePluginImageUrl(url: string | undefined) {
  const normalized = String(url || '').trim()
  if (!normalized) return ''
  if (normalized.startsWith('plugin/')) return `/api/v1/${normalized}`
  if (normalized.startsWith('/plugin/')) return `/api/v1${normalized}`
  return normalized
}

function getLayerPreviewImage(layer: CustomImageLayer): Pick<PreviewSourceImage, 'src' | 'label'> | undefined {
  const stickerSrc = layer.stickerDataUrl
    || normalizePluginImageUrl(layer.stickerUrl)
    || getStickerPathUrl(layer.stickerPath)
  if (layer.assetKind === 'sticker' || stickerSrc) {
    return stickerSrc
      ? {
          src: stickerSrc,
          label: layer.stickerName || 'sticker',
        }
      : undefined
  }
  return getLayerImage(layer.sourceIndex)
}

watch(
  () => firstImage.value?.src,
  async (src) => {
    if (!src) {
      autoBlendColor.value = getThemeColor('--mcr-cover-auto-blend')
      return
    }
    const extracted = await extractComfortableColor(src)
    autoBlendColor.value = extracted || getThemeColor('--mcr-cover-auto-blend')
  },
  { immediate: true },
)

function updatePreviewStageScale() {
  const stage = previewStageEl.value
  if (!stage) return
  if (usesEditorLayoutPreview.value) {
    previewStageScale.value = 1
    return
  }
  const width = stage.clientWidth || 1
  const documentWidth = documentSize.value.width
  previewStageScale.value = width / documentWidth
}

function getLayerStyle(layer: CustomImageLayer | CustomTitleLayer | CustomTextLayer) {
  const normalized = normalizeLayerEffects(layer)
  const isImage = normalized.type === 'image'
  return {
    ...getLayerFrameStyle(normalized),
    boxShadow: isImage ? getLayerShadowStyle(normalized) : 'none',
    overflow: isImage ? 'hidden' : 'visible',
  }
}

function getImageStyle(layer: CustomImageLayer | CustomTitleLayer | CustomTextLayer) {
  const normalized = normalizeLayerEffects(layer)
  const imageLayer = normalized as CustomImageLayer
  const objectPositionX = Math.max(0, Math.min(100, (imageLayer.cropFocusX ?? 0.5) * 100))
  const objectPositionY = Math.max(0, Math.min(100, (imageLayer.cropFocusY ?? 0.5) * 100))
  return {
    borderRadius: `${Math.max(0, normalized.radius || 0)}px`,
    opacity: String(normalized.opacity ?? 1),
    objectPosition: `${objectPositionX}% ${objectPositionY}%`,
    filter: normalized.blur ? `blur(${Math.max(0, normalized.blur)}px)` : 'none',
    ...getLayerTransformStyle(normalized),
  }
}

function getTitleStyle(layer: CustomTitleLayer | CustomTextLayer) {
  const normalized = normalizeLayerEffects(layer)
  const measured = getMeasuredTextLayout(layer)
  const fontFamily = getPreviewFontFamily(normalized.fontFamily, getCustomLayerText(layer))
  return {
    fontFamily,
    fontSize: `${Math.max(12, measured?.font_size || layer.fontSize || 60)}px`,
    lineHeight: String(measured?.line_height ? measured.line_height / Math.max(1, measured.font_size) : 1.1),
    opacity: String(measured?.opacity ?? normalized.opacity ?? 1),
    filter: (measured?.blur ?? normalized.blur)
      ? `blur(${Math.max(0, measured?.blur ?? normalized.blur ?? 0)}px)`
      : 'none',
    textShadow:
      (measured?.shadow.blur ?? normalized.shadowBlur)
      || (measured?.shadow.offset_x ?? normalized.shadowOffsetX)
      || (measured?.shadow.offset_y ?? normalized.shadowOffsetY)
        ? `${Math.round(measured?.shadow.offset_x ?? normalized.shadowOffsetX ?? 0)}px ${Math.round(measured?.shadow.offset_y ?? normalized.shadowOffsetY ?? 0)}px ${Math.max(0, Math.round(measured?.shadow.blur ?? normalized.shadowBlur ?? 0))}px rgba(var(--mcr-rgb-shadow), ${Math.max(0, Math.min(0.9, measured?.shadow.opacity ?? normalized.shadowOpacity ?? 0.28))})`
        : 'none',
    ...getLayerTransformStyle(normalized),
  }
}

function getMeasuredTextLayout(layer: CustomTitleLayer | CustomTextLayer): CustomMeasuredTextLayout | null {
  const layout = props.source?.custom_static_layout
  const textLayout = layout?.computed?.textLayout
  return textLayout?.[layer.id] || null
}

function measureTextWidth(text: string, layer: CustomTitleLayer | CustomTextLayer) {
  const context = textMeasureCanvas?.getContext('2d')
  if (!context) {
    return text.length * Math.max(12, layer.fontSize || 60) * 0.55
  }
  context.font = `700 ${Math.max(12, layer.fontSize || 60)}px ${getPreviewFontFamily(normalizeLayerEffects(layer).fontFamily, text)}`
  return context.measureText(text).width
}

function getWrappedLayerLines(layer: CustomTitleLayer | CustomTextLayer) {
  const text = getCustomLayerText(layer)
  if (!text) return ['']

  const maxWidth = Math.max(1, layer.width)
  const lines: string[] = []
  let current = ''

  for (const char of Array.from(text)) {
    const candidate = `${current}${char}`
    if (!current || measureTextWidth(candidate, layer) <= maxWidth) {
      current = candidate
      continue
    }
    lines.push(current)
    current = char
  }

  if (current) {
    lines.push(current)
  }

  return lines.length ? lines : [text]
}

function getMeasuredLayerLines(layer: CustomTitleLayer | CustomTextLayer) {
  const measured = getMeasuredTextLayout(layer)
  if (measured?.lines?.length) {
    return measured.lines
  }
  const fontSize = Math.max(12, layer.fontSize || 60)
  const lineHeight = fontSize * 1.1
  const wrappedLines = getWrappedLayerLines(layer)
  const totalHeight = wrappedLines.length * lineHeight
  const startY = layer.y + (layer.height - totalHeight) / 2
  return wrappedLines.map((line, index) => {
    const lineWidth = measureTextWidth(line, layer)
    return {
      text: line,
      x: layer.x + (layer.width - lineWidth) / 2,
      y: startY + index * lineHeight,
      width: lineWidth,
      height: fontSize,
    }
  })
}

function getMeasuredLineStyle(layer: CustomTitleLayer | CustomTextLayer, index: number) {
  const measured = getMeasuredTextLayout(layer)
  const lines = getMeasuredLayerLines(layer)
  const line = lines[index]
  const frame = measured?.frame || {
    x: layer.x,
    y: layer.y,
  }
  if (!line) {
    return {}
  }
  return {
    position: 'absolute',
    left: '0',
    top: '0',
    transform: `translate(${Math.round(line.x - frame.x)}px, ${Math.round(line.y - frame.y)}px)`,
  }
}

function ensureFontFace(name: string, url?: string) {
  if (!url || typeof FontFace === 'undefined' || typeof document === 'undefined') {
    return Promise.resolve()
  }
  const cacheKey = `${name}:${url}`
  const cached = loadedFontUrls.get(cacheKey)
  if (cached) return cached
  const pending = new FontFace(name, `url(${url})`).load()
    .then((font) => {
      document.fonts.add(font)
    })
    .catch((error) => {
      console.error(`load font face failed: ${name}`, error)
    })
    .then(() => undefined)
  loadedFontUrls.set(cacheKey, pending)
  return pending
}

watch(
  () => props.source?.font_faces,
  async (fontFaces) => {
    await Promise.all(
      Object.entries(fontFaces || {}).map(([key, url]) => ensureFontFace(getTemplateFontFaceName(key), url)),
    )
  },
  { deep: true, immediate: true },
)

watch(
  () => [styleBase.value, hasCustomLayout.value, props.source?.images?.length],
  () => {
    nextTick(() => updatePreviewStageScale())
  },
)

onMounted(() => {
  nextTick(() => {
    updatePreviewStageScale()
    if (previewStageEl.value && typeof ResizeObserver !== 'undefined') {
      previewStageResizeObserver = new ResizeObserver(() => updatePreviewStageScale())
      previewStageResizeObserver.observe(previewStageEl.value)
    } else {
      window.addEventListener('resize', updatePreviewStageScale)
    }
  })
})

onUnmounted(() => {
  previewStageResizeObserver?.disconnect()
  window.removeEventListener('resize', updatePreviewStageScale)
})
</script>

<style scoped>
.simulation-shell {
  width: 100%;
  height: 100%;
}

.simulation-empty,
.simulation-canvas {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--mcr-border, var(--mcr-color-outline-variant));
}

.simulation-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--mcr-cream, var(--mcr-color-surface));
  color: var(--mcr-charcoal, var(--mcr-color-on-surface));
  text-align: center;
}

.sim-stage-shell {
  position: absolute;
  inset: 0;
}

.sim-stage-shell--layout {
  display: block;
}

.sim-layout-preview {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.sim-stage {
  position: absolute;
  inset: 0;
  width: 1920px;
  height: 1080px;
  transform-origin: top left;
}

.sim-bg,
.sim-overlay {
  position: absolute;
  inset: 0;
}

.sim-bg {
  background-position: center;
  background-size: cover;
}

.sim-overlay {
  background: rgba(var(--mcr-rgb-shadow), 0.64);
}

.sim-overlay-strong {
  opacity: 0.72;
}

.sim-grid,
.sim-style-3-header,
.sim-style-4-copy,
.sim-custom-stage {
  position: relative;
  z-index: 2;
}

.sim-grid {
  display: grid;
  height: 100%;
}

.sim-grid-style-1 {
  grid-template-columns: 960px 960px;
  gap: 0;
  padding: 0;
}

.sim-copy,
.sim-style-1-copy,
.sim-style-2-copy,
.sim-style-4-copy {
  color: var(--mcr-color-surface-container-lowest);
}

.sim-style-1-copy {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
}

.sim-title-zh {
  font-size: 170px;
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: 0;
  text-shadow: 12px 12px 20px rgba(var(--mcr-rgb-shadow), 0.26);
}

.sim-title-en {
  margin-top: 40px;
  font-size: 75px;
  line-height: 1.2;
  letter-spacing: 0;
  opacity: 0.9;
  text-transform: none;
  text-shadow: 8px 8px 18px rgba(var(--mcr-rgb-shadow), 0.24);
}

.sim-title-center {
  text-align: center;
}

.sim-main-image-wrap,
.sim-style-2-frame-front {
  position: relative;
  align-self: center;
  justify-self: center;
  width: 100%;
  height: 78%;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 18px 56px rgba(var(--mcr-rgb-shadow), 0.35);
}

.sim-main-image,
.sim-style-3-item img,
.sim-custom-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.sim-style-1-stage {
  position: relative;
  height: 100%;
  min-height: 0;
}

.sim-style-1-card {
  position: absolute;
  left: 42px;
  top: 162px;
  width: 756px;
  height: 756px;
  border-radius: 94px;
  overflow: hidden;
  box-shadow: 20px 26px 36px rgba(var(--mcr-rgb-shadow), 0.42);
  background-size: cover;
  background-position: center;
}

.sim-style-1-card-back {
  background:
    linear-gradient(rgba(var(--mcr-rgb-tertiary-fixed), 0.58), rgba(var(--mcr-rgb-tertiary-fixed), 0.58)),
    var(--sim-main-image, none);
  filter: blur(8px);
  transform: rotate(36deg);
}

.sim-style-1-card-mid {
  background:
    linear-gradient(rgba(var(--mcr-rgb-primary-fixed), 0.5), rgba(var(--mcr-rgb-primary-fixed), 0.5)),
    var(--sim-main-image, none);
  filter: blur(4px);
  transform: rotate(18deg);
}

.sim-style-1-card-front {
  transform: rotate(0deg);
}

.sim-grid-style-2 {
  grid-template-columns: 960px 960px;
  padding: 0;
  gap: 0;
}

.sim-style-2-copy {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  z-index: 2;
}

.sim-style-2-shadow,
.sim-style-2-foreground {
  position: absolute;
  inset: 0;
}

.sim-style-2-shadow {
  background: linear-gradient(90deg, transparent 0%, transparent 43%, rgba(var(--mcr-rgb-shadow), 0.22) 48%, transparent 54%);
  z-index: 1;
}

.sim-style-2-foreground {
  clip-path: polygon(55% 0, 100% 0, 100% 100%, 40% 100%);
  z-index: 1;
}

.sim-style-2-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
}

.sim-style-3-header {
  position: absolute;
  left: 73px;
  top: 427px;
  z-index: 3;
  width: 720px;
  color: var(--mcr-color-surface-container-lowest);
}

.sim-style-3-title {
  font-size: 170px;
  font-weight: 700;
  line-height: 1.06;
  letter-spacing: 0;
  text-shadow: 8px 8px 18px rgba(var(--mcr-rgb-shadow), 0.28);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sim-style-3-subtitle-row {
  display: inline-flex;
  align-items: stretch;
  gap: 20px;
  margin-top: 32px;
  margin-left: 11px;
  max-width: 100%;
}

.sim-style-3-subtitle {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 12px;
  font-size: 75px;
  line-height: 1.24;
  letter-spacing: 0;
  opacity: 0.9;
  text-transform: none;
}

.sim-style-3-subtitle-line {
  display: block;
}

.sim-style-3-bg {
  position: absolute;
  inset: 0;
}

.sim-style-3-stage {
  position: relative;
  z-index: 2;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.sim-style-3-column {
  position: absolute;
  display: grid;
  gap: 22px;
  width: 410px;
  transform: rotate(15.8deg);
  transform-origin: center center;
}

.sim-style-3-column-1 {
  left: 835px;
  top: -362px;
}

.sim-style-3-column-2 {
  left: 1195px;
  top: -362px;
}

.sim-style-3-column-3 {
  left: 1595px;
  top: -517px;
}

.sim-style-3-item {
  overflow: hidden;
  border-radius: 46px;
  width: 410px;
  height: 610px;
  aspect-ratio: auto;
  box-shadow:
    20px 20px 40px rgba(var(--mcr-rgb-shadow), 0.42);
}

.sim-style-3-accent {
  flex: 0 0 22px;
  align-self: stretch;
  width: 22px;
  height: auto;
  min-height: 1.2em;
  border-radius: 0;
}

.sim-style-4-copy {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 0 10%;
  color: var(--mcr-color-surface-container-lowest);
}

.sim-custom-stage-shell {
  position: absolute;
  inset: 0;
  overflow: hidden;
  z-index: 2;
}

.sim-custom-stage {
  position: absolute;
  inset: 0;
}

.sim-custom-empty {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 0 10%;
  color: var(--mcr-color-surface-container-lowest);
  text-align: center;
}

.sim-custom-layer {
  position: absolute;
  overflow: hidden;
}

.sim-custom-image {
  border-radius: inherit;
}

.sim-custom-text {
  position: relative;
  width: 100%;
  height: 100%;
  color: var(--mcr-color-surface-container-lowest);
  text-align: center;
  line-height: 1.12;
  text-shadow: 0 8px 24px rgba(var(--mcr-rgb-shadow), 0.35);
  overflow: hidden;
}

.sim-custom-text-line {
  display: block;
  max-width: 100%;
  white-space: nowrap;
}

.sim-custom-text-en {
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.sim-live-badge {
  position: absolute;
  right: 12px;
  top: 12px;
  z-index: 3;
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border-radius: 999px;
  background: rgba(var(--mcr-rgb-surface-container-lowest, 255, 255, 255), 0.82);
  border: 1px solid var(--mcr-border, var(--mcr-color-outline-variant));
  box-shadow: 0 8px 20px rgba(var(--mcr-rgb-shadow, 0, 0, 0), 0.18);
  backdrop-filter: blur(10px);
}

.sim-live-icon {
  position: relative;
  display: block;
  width: 16px;
  height: 16px;
  border: 1.7px solid var(--mcr-blueprint-cyan, var(--mcr-color-primary));
  border-radius: 999px;
}

.sim-live-icon::before,
.sim-live-icon::after {
  content: '';
  position: absolute;
  border: 1.3px solid var(--mcr-blueprint-cyan, var(--mcr-color-primary));
  border-radius: 999px;
}

.sim-live-icon::before {
  inset: 2.5px;
  opacity: 0.78;
}

.sim-live-icon::after {
  inset: 5.8px;
  background: var(--mcr-blueprint-cyan, var(--mcr-color-primary));
}

.sim-live-icon span {
  position: absolute;
  right: -1px;
  bottom: -1px;
  width: 4px;
  height: 4px;
  border-radius: 999px;
  background: var(--mcr-blueprint-danger, var(--mcr-color-tertiary));
}

</style>
