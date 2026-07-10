import type {
  CustomGroupLayer,
  CustomImageLayer,
  CustomStaticLayout,
  CustomTextLayer,
  CustomTitleLayer,
  TemplateLayer,
  TemplateLayerType,
} from '../types/plugin'
import { EDITOR_BASE_HEIGHT, EDITOR_BASE_WIDTH, createLayoutId, normalizeLayerEffects, normalizeLayerType } from './customLayout'
import { getThemeColor } from './themeColors'

const DEFAULT_SHADOW = {
  blur: 0,
  offsetX: 0,
  offsetY: 0,
  opacity: 0.28,
  color: getThemeColor('--mcr-cover-shadow'),
}

function numberOr(value: unknown, fallback: number) {
  const next = Number(value)
  return Number.isFinite(next) ? next : fallback
}

function normalizeGroupLayer(layer: Partial<CustomGroupLayer>): CustomGroupLayer {
  const x = numberOr(layer.x, 0)
  const y = numberOr(layer.y, 0)
  const width = numberOr(layer.width, EDITOR_BASE_WIDTH)
  const height = numberOr(layer.height, EDITOR_BASE_HEIGHT)
  const rotation = numberOr(layer.rotation ?? layer.transform?.rotation, 0)
  const pivotX = numberOr(layer.pivotX ?? layer.transform?.pivotX, 0.5)
  const pivotY = numberOr(layer.pivotY ?? layer.transform?.pivotY, 0.5)
  const opacity = numberOr(layer.opacity ?? layer.transform?.opacity, 1)
  const shadow = {
    ...DEFAULT_SHADOW,
    ...(layer.effects?.shadow || {}),
    blur: numberOr(layer.shadowBlur ?? layer.effects?.shadow?.blur, DEFAULT_SHADOW.blur),
    offsetX: numberOr(layer.shadowOffsetX ?? layer.effects?.shadow?.offsetX, DEFAULT_SHADOW.offsetX),
    offsetY: numberOr(layer.shadowOffsetY ?? layer.effects?.shadow?.offsetY, DEFAULT_SHADOW.offsetY),
    opacity: numberOr(layer.shadowOpacity ?? layer.effects?.shadow?.opacity, DEFAULT_SHADOW.opacity),
  }
  const blur = numberOr(layer.blur ?? layer.effects?.blur, 0)
  return normalizeLayerEffects({
    id: layer.id || createLayoutId(),
    type: 'group',
    x,
    y,
    width,
    height,
    zIndex: numberOr(layer.zIndex, 0),
    rotation,
    pivotX,
    pivotY,
    opacity,
    blur,
    shadowBlur: shadow.blur,
    shadowOffsetX: shadow.offsetX,
    shadowOffsetY: shadow.offsetY,
    shadowOpacity: shadow.opacity,
    children: (layer.children || []).map((child) => normalizeTemplateLayer(child)).filter(Boolean) as TemplateLayer[],
    effects: {
      blur,
      shadow,
    },
  } as CustomGroupLayer)
}

export function normalizeTemplateLayer(layer: Partial<TemplateLayer> | null | undefined): TemplateLayer | null {
  if (!layer) return null
  const normalizedType = (layer.type === 'group' ? 'group' : normalizeLayerType(layer.type)) as TemplateLayerType
  if (normalizedType === 'group') {
    return normalizeGroupLayer(layer as Partial<CustomGroupLayer>)
  }

  const shadow = {
    ...DEFAULT_SHADOW,
    ...(layer.effects?.shadow || {}),
    blur: numberOr(layer.shadowBlur ?? layer.effects?.shadow?.blur, DEFAULT_SHADOW.blur),
    offsetX: numberOr(layer.shadowOffsetX ?? layer.effects?.shadow?.offsetX, DEFAULT_SHADOW.offsetX),
    offsetY: numberOr(layer.shadowOffsetY ?? layer.effects?.shadow?.offsetY, DEFAULT_SHADOW.offsetY),
    opacity: numberOr(layer.shadowOpacity ?? layer.effects?.shadow?.opacity, DEFAULT_SHADOW.opacity),
  }
  const blur = numberOr(layer.blur ?? layer.effects?.blur, 0)
  const textStyle = (layer as Partial<CustomTitleLayer | CustomTextLayer> & { textStyle?: Record<string, unknown> }).textStyle || {}
  const rawMaskMode = (layer as Partial<CustomTitleLayer | CustomTextLayer>).maskMode ?? textStyle.maskMode
  const maskMode = rawMaskMode === 'knockout-text' || rawMaskMode === 'show-text' ? rawMaskMode : 'normal'
  const normalized = normalizeLayerEffects({
    ...layer,
    id: layer.id || createLayoutId(),
    type: normalizedType,
    x: numberOr(layer.x, 0),
    y: numberOr(layer.y, 0),
    width: numberOr(layer.width, 1),
    height: numberOr(layer.height, 1),
    zIndex: numberOr(layer.zIndex, 0),
    rotation: numberOr(layer.rotation ?? layer.transform?.rotation, 0),
    pivotX: numberOr(layer.pivotX ?? layer.transform?.pivotX, 0.5),
    pivotY: numberOr(layer.pivotY ?? layer.transform?.pivotY, 0.5),
    opacity: numberOr(layer.opacity ?? layer.transform?.opacity, 1),
    blur,
    shadowBlur: shadow.blur,
    shadowOffsetX: shadow.offsetX,
    shadowOffsetY: shadow.offsetY,
    shadowOpacity: shadow.opacity,
    fontSize: numberOr((layer as Partial<CustomTitleLayer | CustomTextLayer>).fontSize, normalizedType === 'subtitle' ? 75 : 170),
    textAlign: ['left', 'center', 'right'].includes(String((layer as Partial<CustomTitleLayer | CustomTextLayer>).textAlign))
      ? (layer as Partial<CustomTitleLayer | CustomTextLayer>).textAlign
      : 'center',
    maskMode,
    content: (layer as Partial<CustomTextLayer>).content ?? '自定义文本',
    assetKind: (layer as Partial<CustomImageLayer>).assetKind === 'sticker'
      || Boolean(
        (layer as Partial<CustomImageLayer>).stickerDataUrl
        || (layer as Partial<CustomImageLayer>).stickerPath
        || (layer as Partial<CustomImageLayer>).stickerUrl,
      )
      ? 'sticker'
      : 'source',
    stickerDataUrl: (layer as Partial<CustomImageLayer>).stickerDataUrl,
    stickerPath: (layer as Partial<CustomImageLayer>).stickerPath,
    stickerUrl: (layer as Partial<CustomImageLayer>).stickerUrl,
    stickerName: (layer as Partial<CustomImageLayer>).stickerName,
    stickerWidth: numberOr((layer as Partial<CustomImageLayer>).stickerWidth, 0),
    stickerHeight: numberOr((layer as Partial<CustomImageLayer>).stickerHeight, 0),
    sourceIndex: numberOr((layer as Partial<CustomImageLayer>).sourceIndex ?? (layer as Partial<CustomImageLayer>).source?.slot, 1),
    fit: (layer as Partial<CustomImageLayer>).fit || 'cover',
    source: {
      kind: 'slot',
      slot: numberOr((layer as Partial<CustomImageLayer>).sourceIndex ?? (layer as Partial<CustomImageLayer>).source?.slot, 1),
    },
    maskPolygon: (layer as Partial<CustomImageLayer>).maskPolygon,
    effects: {
      blur,
      shadow,
    },
  } as TemplateLayer)
  return normalized as TemplateLayer
}

export function normalizeTemplate(layout?: CustomStaticLayout | null): CustomStaticLayout {
  const canvas = layout?.canvas || layout?.document || {
    width: EDITOR_BASE_WIDTH,
    height: EDITOR_BASE_HEIGHT,
    unit: 'px' as const,
  }
  const width = numberOr(canvas.width, EDITOR_BASE_WIDTH)
  const height = numberOr(canvas.height, EDITOR_BASE_HEIGHT)
  return {
    ...layout,
    schema: 'mcr-template/v1',
    version: layout?.version || '1.0',
    canvas: {
      width,
      height,
      unit: 'px',
    },
    document: {
      width,
      height,
      unit: 'px',
    },
    background: layout?.background || {
      type: 'blurred-image-color',
      imageSource: { kind: 'slot', slot: 1 },
      colorSource: 'auto',
      color: getThemeColor('--mcr-cover-auto-blend'),
      color2: getThemeColor('--mcr-cover-deep-gradient'),
      colorRatio: 0.8,
      opacity: 1,
      blur: 50,
      grain: 0.18,
      zIndex: 0,
    },
    assets: layout?.assets || {},
    layers: (layout?.layers || [])
      .map((layer) => normalizeTemplateLayer(layer))
      .filter(Boolean) as TemplateLayer[],
    computed: layout?.computed,
  }
}

export function flattenTemplateLayers(layers: TemplateLayer[]): TemplateLayer[] {
  return layers.flatMap((layer) => (
    layer.type === 'group'
      ? [layer, ...flattenTemplateLayers(layer.children || [])]
      : [layer]
  ))
}
