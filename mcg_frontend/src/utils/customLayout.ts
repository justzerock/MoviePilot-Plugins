import type {
  CoverStyleBase,
  CustomBadgeLayer,
  CustomGroupLayer,
  CustomImageLayer,
  CustomLayerBase,
  CustomStaticLayout,
  CustomTextFontFamily,
  CustomTextLayer,
  CustomTitleLayer,
  TemplateLayer,
  TemplateLayerType,
} from '../types/plugin'
import { getThemeColor, getThemeRgba } from './themeColors'

export const EDITOR_BASE_WIDTH = 1920
export const EDITOR_BASE_HEIGHT = 1080

export function createLayoutId() {
  return `layout_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`
}

export function normalizeLayerType(type?: string): TemplateLayerType {
  if (type === 'group') return 'group'
  if (type === 'image') return 'image'
  if (type === 'main_title' || type === 'title_zh') return 'main_title'
  if (type === 'subtitle' || type === 'title_en') return 'subtitle'
  if (type === 'text') return 'text'
  if (type === 'badge') return 'badge'
  return 'image'
}

export function isImageLayer(layer: TemplateLayer): layer is CustomImageLayer {
  return normalizeLayerType(layer.type) === 'image'
}

export function isMainTitleLayer(layer: TemplateLayer) {
  return normalizeLayerType(layer.type) === 'main_title'
}

export function isSubtitleLayer(layer: TemplateLayer) {
  return normalizeLayerType(layer.type) === 'subtitle'
}

export function isTitleLayer(layer: TemplateLayer): layer is CustomTitleLayer {
  const normalized = normalizeLayerType(layer.type)
  return normalized === 'main_title' || normalized === 'subtitle'
}

export function isCustomTextLayer(layer: TemplateLayer): layer is CustomTextLayer {
  return normalizeLayerType(layer.type) === 'text'
}

export function isBadgeLayer(layer: TemplateLayer): layer is CustomBadgeLayer {
  return normalizeLayerType(layer.type) === 'badge'
}

export function isTextLayer(layer: TemplateLayer): layer is CustomTitleLayer | CustomTextLayer | CustomBadgeLayer {
  const normalized = normalizeLayerType(layer.type)
  return normalized === 'main_title' || normalized === 'subtitle' || normalized === 'text' || normalized === 'badge'
}

function withLegacyLayerFields<T extends TemplateLayer>(layer: T): T {
  const normalized = layer as T & {
    frame?: Record<string, number>
    shadow?: Record<string, number>
    textStyle?: Record<string, unknown>
    cornerRadius?: number
  }
  normalized.frame = {
    x: normalized.x,
    y: normalized.y,
    width: normalized.width,
    height: normalized.height,
  }
  normalized.cornerRadius = normalized.radius ?? 0
  normalized.shadow = {
    x: normalized.shadowOffsetX ?? 0,
    y: normalized.shadowOffsetY ?? 0,
    blur: normalized.shadowBlur ?? 0,
    opacity: normalized.shadowOpacity ?? 0.28,
  }
  if (isTextLayer(normalized)) {
    normalized.textStyle = {
      fontFamily: normalized.fontFamily,
      fontSize: normalized.fontSize,
      textAlign: normalized.textAlign ?? 'center',
      ...(!isBadgeLayer(normalized) ? { maskMode: normalized.maskMode ?? 'normal' } : {}),
      ...(isCustomTextLayer(normalized) ? { content: normalized.content } : {}),
      ...(isBadgeLayer(normalized) ? { content: normalized.content } : {}),
    }
  } else {
    delete normalized.textStyle
  }
  return normalized
}

export function normalizeLayerEffects<T extends TemplateLayer>(layer: T): T {
  const normalizedType = normalizeLayerType(layer.type)
  if (normalizedType === 'group') {
    const group = layer as CustomGroupLayer
    const rotation = group.rotation ?? group.transform?.rotation ?? 0
    const pivotX = group.pivotX ?? group.transform?.pivotX ?? 0.5
    const pivotY = group.pivotY ?? group.transform?.pivotY ?? 0.5
    const opacity = group.opacity ?? group.transform?.opacity ?? 1
    const blur = group.blur ?? group.effects?.blur ?? 0
    const grain = group.grain ?? group.effects?.grain ?? 0
    const shadowBlur = group.shadowBlur ?? group.effects?.shadow?.blur ?? 0
    const shadowOffsetX = group.shadowOffsetX ?? group.effects?.shadow?.offsetX ?? 0
    const shadowOffsetY = group.shadowOffsetY ?? group.effects?.shadow?.offsetY ?? 0
    const shadowOpacity = group.shadowOpacity ?? group.effects?.shadow?.opacity ?? 0.28
    return withLegacyLayerFields({
      ...group,
      type: 'group',
      rotation,
      pivotX,
      pivotY,
      opacity,
      blur,
      grain,
      shadowBlur,
      shadowOffsetX,
      shadowOffsetY,
      shadowOpacity,
      transform: {
        rotation,
        pivotX,
        pivotY,
        opacity,
      },
      effects: {
        blur,
        grain,
        shadow: {
          blur: shadowBlur,
          offsetX: shadowOffsetX,
          offsetY: shadowOffsetY,
          opacity: shadowOpacity,
          color: group.effects?.shadow?.color ?? getThemeColor('--mcr-cover-shadow'),
        },
      },
      children: (group.children || []).map((child) => normalizeLayerEffects({ ...child })),
    } as T)
  }
  const shadowBlur = layer.shadowBlur ?? layer.effects?.shadow?.blur ?? 0
  const shadowOffsetX = layer.shadowOffsetX ?? layer.effects?.shadow?.offsetX ?? 0
  const shadowOffsetY = layer.shadowOffsetY ?? layer.effects?.shadow?.offsetY ?? 0
  const shadowOpacity = layer.shadowOpacity ?? layer.effects?.shadow?.opacity ?? 0.28
  const opacity = layer.opacity ?? layer.transform?.opacity ?? 1
  const rotation = layer.rotation ?? layer.transform?.rotation ?? 0
  const pivotX = layer.pivotX ?? layer.transform?.pivotX ?? 0.5
  const pivotY = layer.pivotY ?? layer.transform?.pivotY ?? 0.5
  const blur = layer.blur ?? layer.effects?.blur ?? 0
  const grain = layer.grain ?? layer.effects?.grain ?? 0
  return withLegacyLayerFields({
    ...layer,
    type: normalizedType as T['type'],
    ...(normalizedType === 'image'
      ? {
          assetKind: (layer as CustomImageLayer).assetKind === 'sticker'
            || Boolean(
              (layer as CustomImageLayer).stickerDataUrl
              || (layer as CustomImageLayer).stickerPath
              || (layer as CustomImageLayer).stickerUrl,
            )
            ? 'sticker'
            : 'source',
          stickerDataUrl: (layer as CustomImageLayer).stickerDataUrl,
          stickerPath: (layer as CustomImageLayer).stickerPath,
          stickerUrl: (layer as CustomImageLayer).stickerUrl,
          stickerName: (layer as CustomImageLayer).stickerName,
          stickerWidth: (layer as CustomImageLayer).stickerWidth,
          stickerHeight: (layer as CustomImageLayer).stickerHeight,
          cropFocusX: (layer as CustomImageLayer).cropFocusX ?? 0.5,
          cropFocusY: (layer as CustomImageLayer).cropFocusY ?? 0.5,
          sourceIndex: (layer as CustomImageLayer).sourceIndex ?? (layer as CustomImageLayer).source?.slot ?? 1,
          source: {
            kind: 'slot',
            slot: (layer as CustomImageLayer).sourceIndex ?? (layer as CustomImageLayer).source?.slot ?? 1,
          },
          fit: (layer as CustomImageLayer).fit ?? 'cover',
          maskPolygon: (layer as CustomImageLayer).maskPolygon,
        }
      : {}),
    rotation,
    pivotX,
    pivotY,
    opacity,
    blur,
    grain,
    shadowBlur,
    shadowOffsetX,
    shadowOffsetY,
    shadowOpacity,
    transform: {
      rotation,
      pivotX,
      pivotY,
      opacity,
    },
    effects: {
      blur,
      grain,
      shadow: {
        blur: shadowBlur,
        offsetX: shadowOffsetX,
        offsetY: shadowOffsetY,
        opacity: shadowOpacity,
        color: layer.effects?.shadow?.color ?? getThemeColor('--mcr-cover-shadow'),
      },
    },
    ...(normalizedType !== 'image'
      ? {
          fontFamily:
            (layer as CustomTitleLayer | CustomTextLayer | CustomBadgeLayer).fontFamily
            ?? (normalizedType === 'subtitle' ? 'subtitle' : normalizedType === 'text' ? 'custom_text' : 'main_title'),
          textAlign: (layer as CustomTitleLayer | CustomTextLayer | CustomBadgeLayer).textAlign ?? 'center',
          ...(normalizedType !== 'badge'
            ? { maskMode: (layer as CustomTitleLayer | CustomTextLayer).maskMode ?? 'normal' }
            : {}),
        }
      : {}),
    ...(normalizedType === 'text'
      ? { content: (layer as CustomTextLayer).content ?? '自定义文本' }
      : {}),
    ...(normalizedType === 'badge'
      ? {
          content: (layer as CustomBadgeLayer).content ?? '{count} 部',
          countMode: (layer as CustomBadgeLayer).countMode ?? 'episodes',
          shape: (layer as CustomBadgeLayer).shape ?? 'pill',
          backgroundColor: (layer as CustomBadgeLayer).backgroundColor ?? '#007aff',
          borderColor: (layer as CustomBadgeLayer).borderColor ?? '#ffffff',
          borderWidth: (layer as CustomBadgeLayer).borderWidth ?? 0,
          color: (layer as CustomBadgeLayer).color ?? '#ffffff',
          colorSource: (layer as CustomBadgeLayer).colorSource ?? 'custom',
        }
      : {}),
  } as T)
}

export function cloneLayout(layout: CustomStaticLayout): CustomStaticLayout {
  return {
    ...layout,
    schema: layout.schema ?? 'mcr-template/v1',
    version: layout.version,
    canvas: layout.canvas ? { ...layout.canvas } : layout.document ? { ...layout.document } : undefined,
    document: layout.document ? { ...layout.document } : undefined,
    background: layout.background
      ? {
          ...layout.background,
          imageSource: layout.background.imageSource ? { ...layout.background.imageSource } : undefined,
          colorSource: layout.background.colorSource ?? 'auto',
          opacity: layout.background.opacity ?? (layout.background as any).colorOpacity ?? 1,
          gradientStartOpacity: layout.background.gradientStartOpacity ?? 1,
          gradientEndOpacity: layout.background.gradientEndOpacity ?? 1,
          gradientDirection: layout.background.gradientDirection ?? 'diagonal',
          grain: layout.background.grain ?? 0,
        }
      : undefined,
    assets: layout.assets ? { ...layout.assets } : undefined,
    layers: layout.layers.map((layer) => normalizeLayerEffects({ ...layer })),
    computed: layout.computed
      ? {
          ...layout.computed,
          textLayout: layout.computed.textLayout
            ? Object.fromEntries(
                Object.entries(layout.computed.textLayout).map(([key, value]) => [key, {
                  ...value,
                  frame: { ...value.frame },
                  pivot: { ...value.pivot },
                  shadow: { ...value.shadow },
                  lines: value.lines.map((line) => ({ ...line })),
                }]),
              )
            : undefined,
        }
      : undefined,
  }
}

function createImageLayer(partial: Partial<CustomImageLayer> & Pick<CustomImageLayer, 'sourceIndex' | 'x' | 'y' | 'width' | 'height' | 'zIndex'>): CustomImageLayer {
  return normalizeLayerEffects({
    id: createLayoutId(),
    type: 'image',
    sourceIndex: partial.sourceIndex,
    x: partial.x,
    y: partial.y,
    width: partial.width,
    height: partial.height,
    zIndex: partial.zIndex,
    rotation: partial.rotation ?? 0,
    radius: partial.radius ?? 0,
    pivotX: partial.pivotX ?? 0.5,
    pivotY: partial.pivotY ?? 0.5,
    opacity: partial.opacity,
    blur: partial.blur,
    shadowBlur: partial.shadowBlur,
    shadowOffsetX: partial.shadowOffsetX,
    shadowOffsetY: partial.shadowOffsetY,
    shadowOpacity: partial.shadowOpacity,
    assetKind: partial.assetKind,
    stickerDataUrl: partial.stickerDataUrl,
    stickerPath: partial.stickerPath,
    stickerUrl: partial.stickerUrl,
    stickerName: partial.stickerName,
    stickerWidth: partial.stickerWidth,
    stickerHeight: partial.stickerHeight,
    cropFocusX: partial.cropFocusX ?? 0.5,
    cropFocusY: partial.cropFocusY ?? 0.5,
    fit: partial.fit ?? 'cover',
    maskPolygon: partial.maskPolygon,
    colorSource: partial.colorSource ?? 'none',
    color: partial.color,
    colorRatio: partial.colorRatio ?? 0,
  })
}

function createTitleLayer(partial: Partial<CustomTitleLayer> & Pick<CustomTitleLayer, 'type' | 'x' | 'y' | 'width' | 'height' | 'zIndex' | 'fontSize'>): CustomTitleLayer {
  const normalizedType = normalizeLayerType(partial.type)
  return normalizeLayerEffects({
    id: createLayoutId(),
    type: normalizedType === 'subtitle' ? 'subtitle' : 'main_title',
    x: partial.x,
    y: partial.y,
    width: partial.width,
    height: partial.height,
    zIndex: partial.zIndex,
    fontSize: partial.fontSize,
    fontFamily: partial.fontFamily ?? (normalizedType === 'subtitle' ? 'subtitle' : 'main_title'),
    rotation: partial.rotation ?? 0,
    radius: partial.radius ?? 0,
    pivotX: partial.pivotX ?? 0.5,
    pivotY: partial.pivotY ?? 0.5,
    opacity: partial.opacity,
    blur: partial.blur,
    shadowBlur: partial.shadowBlur,
    shadowOffsetX: partial.shadowOffsetX,
    shadowOffsetY: partial.shadowOffsetY,
    shadowOpacity: partial.shadowOpacity,
    maskMode: partial.maskMode ?? 'normal',
  })
}

export function createTextLayer(partial?: Partial<CustomTextLayer>): CustomTextLayer {
  return normalizeLayerEffects({
    id: createLayoutId(),
    type: 'text',
    content: partial?.content ?? '自定义文本',
    fontFamily: partial?.fontFamily ?? 'custom_text',
    x: partial?.x ?? EDITOR_BASE_WIDTH * 0.1,
    y: partial?.y ?? EDITOR_BASE_HEIGHT * 0.72,
    width: partial?.width ?? EDITOR_BASE_WIDTH * 0.35,
    height: partial?.height ?? EDITOR_BASE_HEIGHT * 0.12,
    zIndex: partial?.zIndex ?? 10,
    fontSize: partial?.fontSize ?? 72,
    textAlign: partial?.textAlign ?? 'center',
    rotation: partial?.rotation ?? 0,
    radius: partial?.radius ?? 0,
    pivotX: partial?.pivotX ?? 0.5,
    pivotY: partial?.pivotY ?? 0.5,
    opacity: partial?.opacity,
    blur: partial?.blur,
    shadowBlur: partial?.shadowBlur ?? 14,
    shadowOffsetX: partial?.shadowOffsetX ?? 0,
    shadowOffsetY: partial?.shadowOffsetY ?? 8,
    shadowOpacity: partial?.shadowOpacity ?? 0.2,
    maskMode: partial?.maskMode ?? 'normal',
  })
}

export function createBadgeLayer(partial?: Partial<CustomBadgeLayer>): CustomBadgeLayer {
  return normalizeLayerEffects({
    id: createLayoutId(),
    type: 'badge',
    content: partial?.content ?? '{count} 部',
    countMode: partial?.countMode ?? 'episodes',
    shape: partial?.shape ?? 'pill',
    backgroundColor: partial?.backgroundColor ?? '#007aff',
    borderColor: partial?.borderColor ?? '#ffffff',
    borderWidth: partial?.borderWidth ?? 0,
    colorSource: partial?.colorSource ?? 'custom',
    color: partial?.color ?? '#ffffff',
    fontFamily: partial?.fontFamily ?? 'main_title',
    x: partial?.x ?? EDITOR_BASE_WIDTH * 0.78,
    y: partial?.y ?? EDITOR_BASE_HEIGHT * 0.07,
    width: partial?.width ?? 250,
    height: partial?.height ?? 92,
    zIndex: partial?.zIndex ?? 12,
    fontSize: partial?.fontSize ?? 46,
    textAlign: partial?.textAlign ?? 'center',
    rotation: partial?.rotation ?? 0,
    radius: partial?.radius ?? 30,
    pivotX: partial?.pivotX ?? 0.5,
    pivotY: partial?.pivotY ?? 0.5,
    opacity: partial?.opacity,
    blur: partial?.blur,
    grain: partial?.grain,
    shadowBlur: partial?.shadowBlur ?? 16,
    shadowOffsetX: partial?.shadowOffsetX ?? 0,
    shadowOffsetY: partial?.shadowOffsetY ?? 8,
    shadowOpacity: partial?.shadowOpacity ?? 0.18,
  } as CustomBadgeLayer)
}

export function getTextLayerFontFamily(layer: CustomTitleLayer | CustomTextLayer | CustomBadgeLayer): CustomTextFontFamily {
  if (layer.fontFamily === 'subtitle') return 'subtitle'
  if (layer.fontFamily === 'custom_text') return 'custom_text'
  if (layer.fontFamily && layer.fontFamily !== 'main_title') return layer.fontFamily
  return 'main_title'
}

export function createDefaultLayout(): CustomStaticLayout {
  const width = EDITOR_BASE_WIDTH
  const height = EDITOR_BASE_HEIGHT
  const imageWidth = width * 0.6
  const imageHeight = height * 0.8

  return {
    schema: 'mcr-template/v1',
    version: '1.0',
    canvas: {
      width,
      height,
      unit: 'px',
    },
    background: {
      type: 'blurred-image-color',
      imageSource: { kind: 'slot', slot: 1 },
      colorSource: 'auto',
      color: getThemeColor('--mcr-cover-auto-blend'),
      color2: getThemeColor('--mcr-cover-deep-gradient'),
      colorRatio: 0.8,
      opacity: 1,
      gradientStartOpacity: 1,
      gradientEndOpacity: 1,
      gradientDirection: 'diagonal',
      blur: 50,
      grain: 0.18,
      zIndex: 0,
    },
    document: {
      width,
      height,
      unit: 'px',
    },
    layers: [
      createImageLayer({
        sourceIndex: 1,
        x: width * 0.35,
        y: height * 0.1,
        width: imageWidth,
        height: imageHeight,
        radius: 32,
        zIndex: 1,
        shadowBlur: 24,
        shadowOffsetX: 0,
        shadowOffsetY: 18,
        shadowOpacity: 0.22,
      }),
      createTitleLayer({
        type: 'main_title',
        x: width * 0.05,
        y: height * 0.25,
        width: width * 0.3,
        height: height * 0.2,
        zIndex: 2,
        fontSize: 180,
        shadowBlur: 18,
        shadowOffsetX: 0,
        shadowOffsetY: 10,
        shadowOpacity: 0.24,
      }),
      createTitleLayer({
        type: 'subtitle',
        x: width * 0.05,
        y: height * 0.5,
        width: width * 0.3,
        height: height * 0.15,
        zIndex: 2,
        fontSize: 75,
        shadowBlur: 14,
        shadowOffsetX: 0,
        shadowOffsetY: 8,
        shadowOpacity: 0.2,
      }),
    ],
  }
}

export function createLayoutFromBuiltInStyle(baseStyle: CoverStyleBase): CustomStaticLayout {
  if (baseStyle === 'static_1') {
    return {
      version: '1.0',
      document: {
        width: EDITOR_BASE_WIDTH,
        height: EDITOR_BASE_HEIGHT,
        unit: 'px',
      },
      layers: [
        createImageLayer({
          sourceIndex: 1,
          x: 1002,
          y: 162,
          width: 756,
          height: 756,
          rotation: 36,
          radius: 94,
          zIndex: 1,
          opacity: 0.56,
          blur: 8,
          shadowBlur: 12,
          shadowOffsetX: 10,
          shadowOffsetY: 16,
          shadowOpacity: 0.4,
        }),
        createImageLayer({
          sourceIndex: 1,
          x: 1002,
          y: 162,
          width: 756,
          height: 756,
          rotation: 18,
          radius: 94,
          zIndex: 2,
          opacity: 0.74,
          blur: 4,
          shadowBlur: 15,
          shadowOffsetX: 15,
          shadowOffsetY: 22,
          shadowOpacity: 0.5,
        }),
        createImageLayer({
          sourceIndex: 1,
          x: 1002,
          y: 162,
          width: 756,
          height: 756,
          rotation: 0,
          radius: 94,
          zIndex: 3,
          shadowBlur: 18,
          shadowOffsetX: 20,
          shadowOffsetY: 26,
          shadowOpacity: 0.6,
        }),
        createTitleLayer({
          type: 'main_title',
          x: 80,
          y: 340,
          width: 800,
          height: 180,
          zIndex: 4,
          fontSize: 170,
          shadowBlur: 12,
          shadowOffsetX: 12,
          shadowOffsetY: 12,
          shadowOpacity: 0.3,
        }),
        createTitleLayer({
          type: 'subtitle',
          x: 100,
          y: 540,
          width: 760,
          height: 140,
          zIndex: 4,
          fontSize: 75,
          shadowBlur: 10,
          shadowOffsetX: 8,
          shadowOffsetY: 8,
          shadowOpacity: 0.26,
        }),
      ],
    }
  }

  if (baseStyle === 'static_2') {
    return {
      version: 1,
      background: {
        type: 'blurred-image-color',
        imageSource: { kind: 'slot', slot: 1 },
        colorSource: 'auto',
        color: getThemeColor('--mcr-cover-auto-blend'),
        color2: getThemeColor('--mcr-cover-deep-gradient'),
        colorRatio: 0.42,
        opacity: 1,
        gradientStartOpacity: 1,
        gradientEndOpacity: 1,
        gradientDirection: 'diagonal',
        blur: 58,
        grain: 0.14,
        zIndex: 0,
      },
      layers: [
        createImageLayer({
          sourceIndex: 1,
          x: 758,
          y: 0,
          width: 1162,
          height: 1080,
          zIndex: 1,
          radius: 0,
          cropFocusX: 0.75,
          cropFocusY: 0.5,
          shadowBlur: 20,
          shadowOffsetX: -18,
          shadowOffsetY: 0,
          shadowOpacity: 0.16,
          maskPolygon: {
            units: 'relative',
            points: [[0.22, 0], [1, 0], [1, 1], [0, 1]],
          },
        }),
        createTitleLayer({
          type: 'main_title',
          x: 80,
          y: 340,
          width: 800,
          height: 180,
          zIndex: 2,
          fontSize: 187,
          shadowBlur: 12,
          shadowOffsetX: 12,
          shadowOffsetY: 12,
          shadowOpacity: 0.24,
        }),
        createTitleLayer({
          type: 'subtitle',
          x: 100,
          y: 545,
          width: 760,
          height: 140,
          zIndex: 2,
          fontSize: 82,
          shadowBlur: 10,
          shadowOffsetX: 8,
          shadowOffsetY: 8,
          shadowOpacity: 0.22,
        }),
      ],
    }
  }

  if (baseStyle === 'static_3') {
    const order = [3, 1, 5, 4, 2, 6, 9, 8, 7]
    const rowOffsets = [
      { x: 0, y: 0 },
      { x: -174, y: 618 },
      { x: -349, y: 1241 },
    ]
    const columnOffsets = [
      { x: 0, y: 0 },
      { x: 466, y: -7 },
      { x: 968, y: -112 },
    ]
    const positions = order.map((_, index) => {
      const column = Math.floor(index / 3)
      const row = index % 3
      return {
        x: 977 + columnOffsets[column].x + rowOffsets[row].x,
        y: -334 + columnOffsets[column].y + rowOffsets[row].y,
      }
    })
    const layers: CustomStaticLayout['layers'] = order.map((sourceIndex, index) =>
      createImageLayer({
        sourceIndex,
        x: positions[index].x,
        y: positions[index].y,
        width: 410,
        height: 610,
        rotation: 15.8,
        radius: 46,
        zIndex: index + 1,
        shadowBlur: 18,
        shadowOffsetX: 10,
        shadowOffsetY: 14,
        shadowOpacity: 0.2,
      }),
    )
    layers.push(
      createTitleLayer({
        type: 'main_title',
        x: -18,
        y: 383,
        width: 902,
        height: 124,
        zIndex: 20,
        fontSize: 170,
        shadowBlur: 10,
        shadowOffsetX: 8,
        shadowOffsetY: 8,
        shadowOpacity: 0.24,
      }),
    )
    layers.push(
      createTitleLayer({
        type: 'subtitle',
        x: 124,
        y: 625,
        width: 620,
        height: 150,
        zIndex: 20,
        fontSize: 75,
        shadowBlur: 8,
        shadowOffsetX: 6,
        shadowOffsetY: 6,
        shadowOpacity: 0.2,
      }),
    )
    return { version: 1, layers }
  }

  if (baseStyle === 'static_4') {
    return {
      version: 1,
      layers: [
        createTitleLayer({
          type: 'main_title',
          x: 260,
          y: 360,
          width: 1400,
          height: 180,
          zIndex: 2,
          fontSize: 190,
          shadowBlur: 18,
          shadowOffsetY: 12,
          shadowOpacity: 0.24,
        }),
        createTitleLayer({
          type: 'subtitle',
          x: 320,
          y: 560,
          width: 1280,
          height: 150,
          zIndex: 2,
          fontSize: 80,
          shadowBlur: 14,
          shadowOffsetY: 8,
          shadowOpacity: 0.2,
        }),
      ],
    }
  }

  return createDefaultLayout()
}

export function getLayerShadowStyle(layer: CustomLayerBase) {
  const shadowBlur = Number(layer.shadowBlur ?? 0)
  const shadowOffsetX = Number(layer.shadowOffsetX ?? 0)
  const shadowOffsetY = Number(layer.shadowOffsetY ?? 0)
  const shadowOpacity = Number(layer.shadowOpacity ?? 0)
  if (shadowBlur <= 0 && shadowOffsetX === 0 && shadowOffsetY === 0) {
    return 'none'
  }
  const alpha = Math.max(0, Math.min(0.9, shadowOpacity || 0.24))
  return `${shadowOffsetX}px ${shadowOffsetY}px ${Math.max(0, shadowBlur)}px ${getThemeRgba('--mcr-cover-shadow-rgb', alpha)}`
}
