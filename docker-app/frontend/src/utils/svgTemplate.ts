import type {
  CustomGroupLayer,
  CustomImageLayer,
  CustomStaticLayout,
  CustomTextLayer,
  CustomTitleLayer,
  PreviewSourcePayload,
  SimulationParams,
  TemplateLayer,
} from '../types/plugin'
import { isCustomTextLayer, isImageLayer, isMainTitleLayer, isTextLayer } from './customLayout'
import { resolveBlendColor } from './renderSimulation'
import { normalizeTemplate } from './templateSchema'
import { getTemplateFontFamilyStack } from '../constants/fonts'
import { getThemeColor } from './themeColors'

interface RenderOptions {
  selectedLayerId?: string | null
  interactive?: boolean
  autoBlendColor?: string
}

function escapeXml(value: unknown) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;')
}

function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value))
}

function getImageHref(source: PreviewSourcePayload | null, slot: number) {
  const image = source?.images.find((item) => item.slot === slot) || source?.images[slot - 1]
  if (!image) return ''
  const src = image.src || (image as any).url || (image as any).href || ''
  return typeof src === 'string' ? src : ''
}

function getImageMeta(source: PreviewSourcePayload | null, slot: number) {
  return source?.images.find((item) => item.slot === slot) || source?.images[slot - 1] || null
}

function isStickerLayerLike(layer: CustomImageLayer) {
  return layer.assetKind === 'sticker' || Boolean(layer.stickerDataUrl || layer.stickerPath || layer.stickerUrl)
}

const dataUrlObjectUrlCache = new Map<string, string>()

function dataUrlToObjectUrl(dataUrl: string) {
  if (!dataUrl.startsWith('data:image/') || typeof window === 'undefined' || typeof Blob === 'undefined' || typeof URL === 'undefined' || typeof atob === 'undefined') {
    return dataUrl
  }
  const cached = dataUrlObjectUrlCache.get(dataUrl)
  if (cached) return cached
  const commaIndex = dataUrl.indexOf(',')
  if (commaIndex <= 0) return dataUrl
  const header = dataUrl.slice(0, commaIndex)
  const encoded = dataUrl.slice(commaIndex + 1)
  const mime = header.match(/^data:([^;]+);base64$/)?.[1] || 'image/png'
  try {
    const binary = atob(encoded)
    const bytes = new Uint8Array(binary.length)
    for (let index = 0; index < binary.length; index += 1) {
      bytes[index] = binary.charCodeAt(index)
    }
    const objectUrl = URL.createObjectURL(new Blob([bytes], { type: mime }))
    dataUrlObjectUrlCache.set(dataUrl, objectUrl)
    return objectUrl
  } catch {
    return dataUrl
  }
}

function getStickerPathUrl(path: string | undefined) {
  const normalized = String(path || '').trim()
  return normalized
    ? `/api/v1/plugin/MediaCoverGenerator/saved_cover_image?file=${encodeURIComponent(normalized)}`
    : ''
}

function normalizePluginImageUrl(url: string | undefined) {
  const normalized = String(url || '').trim()
  if (!normalized) return ''
  if (normalized.startsWith('plugin/')) return `/api/v1/${normalized}`
  if (normalized.startsWith('/plugin/')) return `/api/v1${normalized}`
  return normalized
}

function getLayerImageHref(layer: CustomImageLayer, source: PreviewSourcePayload | null) {
  if (isStickerLayerLike(layer) && layer.stickerDataUrl) {
    return dataUrlToObjectUrl(layer.stickerDataUrl)
  }
  if (isStickerLayerLike(layer) && layer.stickerUrl) {
    return normalizePluginImageUrl(layer.stickerUrl)
  }
  if (isStickerLayerLike(layer) && layer.stickerPath) {
    return getStickerPathUrl(layer.stickerPath)
  }
  const slot = Number(layer.source?.slot ?? layer.sourceIndex ?? 1)
  return getImageHref(source, slot)
}

function getLayerImageMeta(layer: CustomImageLayer, source: PreviewSourcePayload | null) {
  if (isStickerLayerLike(layer)) {
    return {
      width: Number(layer.stickerWidth || layer.width || 0),
      height: Number(layer.stickerHeight || layer.height || 0),
    }
  }
  const slot = Number(layer.source?.slot ?? layer.sourceIndex ?? 1)
  return getImageMeta(source, slot)
}

function getLayerTransform(layer: TemplateLayer) {
  const rotation = Number(layer.rotation ?? layer.transform?.rotation ?? 0)
  if (!rotation) return ''
  const pivotX = clamp(Number(layer.pivotX ?? layer.transform?.pivotX ?? 0.5), 0, 1)
  const pivotY = clamp(Number(layer.pivotY ?? layer.transform?.pivotY ?? 0.5), 0, 1)
  const cx = Number(layer.x || 0) + Number(layer.width || 0) * pivotX
  const cy = Number(layer.y || 0) + Number(layer.height || 0) * pivotY
  return ` transform="rotate(${rotation} ${cx} ${cy})"`
}

function getPreserveAspectRatio(layer: CustomImageLayer) {
  if (layer.fit === 'contain') return 'xMidYMid meet'
  if (layer.fit === 'stretch') return 'none'
  return 'xMidYMid slice'
}

function getPlaceholderColor(slot: number) {
  const hue = ((Math.max(1, slot) * 47) + 178) % 360
  return {
    fill: `hsl(${hue} 70% 34%)`,
    stroke: `hsl(${hue} 92% 72%)`,
  }
}

function renderImagePlaceholder(layer: CustomImageLayer) {
  const slot = Number(layer.source?.slot ?? layer.sourceIndex ?? 1)
  const colors = getPlaceholderColor(slot)
  const radius = Math.max(0, Number(layer.radius || 0))
  const inset = Math.max(14, Math.min(Number(layer.width || 0), Number(layer.height || 0)) * 0.08)
  const lineOpacity = 0.36
  return [
    `<rect x="${layer.x}" y="${layer.y}" width="${layer.width}" height="${layer.height}" rx="${radius}" ry="${radius}" fill="${colors.fill}" opacity="0.42" stroke="${colors.stroke}" stroke-width="4"/>`,
    `<path d="M ${Number(layer.x) + inset} ${Number(layer.y) + inset} L ${Number(layer.x) + Number(layer.width) - inset} ${Number(layer.y) + Number(layer.height) - inset} M ${Number(layer.x) + Number(layer.width) - inset} ${Number(layer.y) + inset} L ${Number(layer.x) + inset} ${Number(layer.y) + Number(layer.height) - inset}" stroke="${colors.stroke}" stroke-width="3" opacity="${lineOpacity}"/>`,
    `<circle cx="${Number(layer.x) + Number(layer.width) * 0.5}" cy="${Number(layer.y) + Number(layer.height) * 0.5}" r="${Math.max(10, Math.min(Number(layer.width || 0), Number(layer.height || 0)) * 0.075)}" fill="none" stroke="${colors.stroke}" stroke-width="4" opacity="0.5"/>`,
  ].join('')
}

function getFittedImageFrame(layer: CustomImageLayer, source: PreviewSourcePayload | null) {
  const image = getLayerImageMeta(layer, source)
  const sourceWidth = Number(image?.width || 0)
  const sourceHeight = Number(image?.height || 0)
  const targetWidth = Math.max(1, Number(layer.width || 1))
  const targetHeight = Math.max(1, Number(layer.height || 1))
  const fit = layer.fit || 'cover'
  if (!sourceWidth || !sourceHeight || fit === 'stretch') {
    return {
      x: Number(layer.x || 0),
      y: Number(layer.y || 0),
      width: targetWidth,
      height: targetHeight,
      preserveAspectRatio: getPreserveAspectRatio(layer),
      needsClip: Number(layer.radius || 0) > 0,
    }
  }
  const scale = fit === 'contain'
    ? Math.min(targetWidth / sourceWidth, targetHeight / sourceHeight)
    : Math.max(targetWidth / sourceWidth, targetHeight / sourceHeight)
  const drawWidth = sourceWidth * scale
  const drawHeight = sourceHeight * scale
  const focusX = clamp(Number(layer.cropFocusX ?? 0.5), 0, 1)
  const focusY = clamp(Number(layer.cropFocusY ?? 0.5), 0, 1)
  const overflowX = Math.max(0, drawWidth - targetWidth)
  const overflowY = Math.max(0, drawHeight - targetHeight)
  const insetX = Math.max(0, targetWidth - drawWidth) / 2
  const insetY = Math.max(0, targetHeight - drawHeight) / 2
  return {
    x: Number(layer.x || 0) + insetX - overflowX * focusX,
    y: Number(layer.y || 0) + insetY - overflowY * focusY,
    width: drawWidth,
    height: drawHeight,
    preserveAspectRatio: 'none',
    needsClip: fit === 'cover' || Number(layer.radius || 0) > 0,
  }
}

function getFilterId(layer: TemplateLayer) {
  const blur = Number(layer.blur ?? layer.effects?.blur ?? 0)
  if (!blur) return ''
  return `fx-${escapeXml(layer.id)}`
}

function renderFilter(layer: TemplateLayer, canvasWidth: number, canvasHeight: number) {
  const id = getFilterId(layer)
  if (!id) return ''
  const blur = Math.max(0, Number(layer.blur ?? layer.effects?.blur ?? 0))
  const nodes = []
  if (blur) {
    nodes.push(`<feGaussianBlur in="SourceGraphic" stdDeviation="${blur}" result="blurred"/>`)
    nodes.push('<feMerge><feMergeNode in="blurred"/></feMerge>')
  }
  return `<filter id="${id}" x="${-canvasWidth}" y="${-canvasHeight}" width="${canvasWidth * 3}" height="${canvasHeight * 3}" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB">${nodes.join('')}</filter>`
}

function getMaskPolygonPoints(maskPolygon: any, x: number, y: number, width: number, height: number) {
  if (!maskPolygon || !Array.isArray(maskPolygon.points)) return ''
  const units = maskPolygon.units || 'relative'
  const points = maskPolygon.points
    .map((point: unknown) => {
      if (!Array.isArray(point) || point.length < 2) return null
      const px = Number(point[0])
      const py = Number(point[1])
      if (!Number.isFinite(px) || !Number.isFinite(py)) return null
      return units === 'relative'
        ? `${x + px * width},${y + py * height}`
        : `${x + px},${y + py}`
    })
    .filter(Boolean)
  return points.length >= 3 ? points.join(' ') : ''
}

function getLayerMaskPolygonPoints(layer: CustomImageLayer) {
  return getMaskPolygonPoints(
    (layer as any).maskPolygon,
    Number(layer.x || 0),
    Number(layer.y || 0),
    Number(layer.width || 0),
    Number(layer.height || 0),
  )
}

function getShadowStyle(layer: TemplateLayer) {
  const shadowBlur = Math.max(0, Number(layer.shadowBlur ?? layer.effects?.shadow?.blur ?? 0))
  const shadowOffsetX = Number(layer.shadowOffsetX ?? layer.effects?.shadow?.offsetX ?? 0)
  const shadowOffsetY = Number(layer.shadowOffsetY ?? layer.effects?.shadow?.offsetY ?? 0)
  const shadowOpacity = clamp(Number(layer.shadowOpacity ?? layer.effects?.shadow?.opacity ?? 0.28), 0, 1)
  if (!shadowBlur && !shadowOffsetX && !shadowOffsetY) return null
  return {
    blur: shadowBlur,
    offsetX: shadowOffsetX,
    offsetY: shadowOffsetY,
    opacity: shadowOpacity,
    color: layer.effects?.shadow?.color || getThemeColor('--mcr-cover-shadow'),
  }
}

function renderDefs(layers: TemplateLayer[], canvasWidth: number, canvasHeight: number) {
  const filterDefs: string[] = []
  const clipDefs: string[] = []
  const visit = (layer: TemplateLayer) => {
    const filter = renderFilter(layer, canvasWidth, canvasHeight)
    if (filter) filterDefs.push(filter)
    if (layer.type === 'image') {
      const image = layer as CustomImageLayer
      const polygonPoints = getLayerMaskPolygonPoints(image)
      if (polygonPoints) {
        clipDefs.push(`<clipPath id="clip-${escapeXml(image.id)}" clipPathUnits="userSpaceOnUse"><polygon points="${polygonPoints}"/></clipPath>`)
      } else if (Number(image.radius || 0) > 0 || (image.fit || 'cover') === 'cover') {
        const radius = Math.max(0, Number(image.radius || 0))
        clipDefs.push(`<clipPath id="clip-${escapeXml(image.id)}" clipPathUnits="userSpaceOnUse"><rect x="${image.x}" y="${image.y}" width="${image.width}" height="${image.height}" rx="${radius}" ry="${radius}"/></clipPath>`)
      }
    }
    if (layer.type === 'group') {
      ;(layer as CustomGroupLayer).children.forEach(visit)
    }
  }
  layers.forEach(visit)
  return `<defs>${filterDefs.join('')}${clipDefs.join('')}</defs>`
}

function wrapText(text: string, fontSize: number, maxWidth: number) {
  const chars = Array.from(text || '')
  const lines: string[] = []
  let current = ''
  for (const char of chars) {
    const next = current + char
    if (!current || next.length * fontSize * 0.56 <= maxWidth) {
      current = next
    } else {
      lines.push(current)
      current = char
    }
  }
  if (current) lines.push(current)
  return lines.length ? lines : ['']
}

function getTextContent(layer: CustomTitleLayer | CustomTextLayer, source: PreviewSourcePayload | null) {
  if (isCustomTextLayer(layer)) {
    const fallback = layer.content || ''
    if ((layer.contentSource || 'fixed') !== 'library') return fallback
    const customTexts = source?.custom_texts || {}
    const key = String(layer.contentKey || '').trim()
    if (key && customTexts[key]) return customTexts[key]
    for (const defaultKey of ['default', 'text', 'custom_text', 'content']) {
      if (customTexts[defaultKey]) return customTexts[defaultKey]
    }
    return fallback
  }
  if (isMainTitleLayer(layer)) return source?.titles.zh || source?.library || ''
  return source?.titles.en || ''
}

function getFontFamily(layer: CustomTitleLayer | CustomTextLayer, text: string) {
  return getTemplateFontFamilyStack(layer.fontFamily || 'main_title', text)
}

function getTextMaskMode(layer: CustomTitleLayer | CustomTextLayer) {
  return layer.maskMode === 'knockout-text' || layer.maskMode === 'show-text'
    ? layer.maskMode
    : 'normal'
}

function renderTextShape(
  layer: CustomTitleLayer | CustomTextLayer,
  source: PreviewSourcePayload | null,
  fill: string,
  fillOpacity = 1,
) {
  const text = getTextContent(layer, source)
  if (!text) return ''
  const fontSize = Math.max(1, Number(layer.fontSize || 60))
  const lines = wrapText(text, fontSize, Math.max(1, Number(layer.width || 1)))
  const lineHeight = fontSize * 1.1
  const totalHeight = lines.length * lineHeight
  const startY = Number(layer.y || 0) + (Number(layer.height || 0) - totalHeight) / 2 + fontSize
  const align = layer.textAlign === 'left' || layer.textAlign === 'right' ? layer.textAlign : 'center'
  const x = align === 'left'
    ? Number(layer.x || 0)
    : align === 'right'
      ? Number(layer.x || 0) + Number(layer.width || 0)
      : Number(layer.x || 0) + Number(layer.width || 0) / 2
  const textAnchor = align === 'left' ? 'start' : align === 'right' ? 'end' : 'middle'
  const tspans = lines.map((line, index) =>
    `<tspan x="${x}" y="${startY + index * lineHeight}">${escapeXml(line)}</tspan>`,
  ).join('')
  const family = getFontFamily(layer, text)
  const opacity = clamp(Number(layer.opacity ?? layer.transform?.opacity ?? 1), 0, 1) * clamp(fillOpacity, 0, 1)
  return `<text font-family="${escapeXml(family)}" font-size="${fontSize}" font-weight="700" fill="${fill}" fill-opacity="${opacity}" text-anchor="${textAnchor}"${getLayerTransform(layer)}>${tspans}</text>`
}

function hasTextMaskLayer(layers: TemplateLayer[], mode?: 'knockout-text' | 'show-text'): boolean {
  return layers.some((layer) => {
    if (layer.type === 'group') return hasTextMaskLayer((layer as CustomGroupLayer).children || [], mode)
    if (!isTextLayer(layer)) return false
    const nextMode = getTextMaskMode(layer)
    return mode ? nextMode === mode : nextMode !== 'normal'
  })
}

function renderTextMaskNodes(
  layers: TemplateLayer[],
  source: PreviewSourcePayload | null,
  mode: 'knockout-text' | 'show-text',
) {
  return layers.map((layer) => {
    if (layer.type === 'group') {
      const children = renderTextMaskNodes((layer as CustomGroupLayer).children || [], source, mode)
      if (!children) return ''
      const opacity = clamp(Number(layer.opacity ?? layer.transform?.opacity ?? 1), 0, 1)
      return `<g${getLayerTransform(layer)} opacity="${opacity}">${children}</g>`
    }
    if (!isTextLayer(layer) || getTextMaskMode(layer) !== mode) return ''
    return renderTextShape(layer, source, mode === 'show-text' ? '#ffffff' : '#000000')
  }).join('')
}

function renderTextMaskDef(layers: TemplateLayer[], source: PreviewSourcePayload | null, width: number, height: number) {
  if (!hasTextMaskLayer(layers)) return ''
  const hasShowText = hasTextMaskLayer(layers, 'show-text')
  const base = hasShowText
    ? `<rect x="0" y="0" width="${width}" height="${height}" fill="#000000"/>`
    : `<rect x="0" y="0" width="${width}" height="${height}" fill="#ffffff"/>`
  const showNodes = renderTextMaskNodes(layers, source, 'show-text')
  const knockoutNodes = renderTextMaskNodes(layers, source, 'knockout-text')
  return `<mask id="mcr-text-mask" maskUnits="userSpaceOnUse" x="0" y="0" width="${width}" height="${height}">${base}${showNodes}${knockoutNodes}</mask>`
}

function resolveTemplateColor(
  colorSource: 'auto' | 'custom' | 'config' | 'none' | undefined,
  customColor: string | undefined,
  source: PreviewSourcePayload | null,
  params: SimulationParams,
  autoBlendColor?: string,
) {
  if (colorSource === 'none') return ''
  if (colorSource === 'custom') {
    return customColor || params.customColor || autoBlendColor || getThemeColor('--mcr-cover-auto-blend')
  }
  if (colorSource === 'config') {
    return source?.bg_color || customColor || autoBlendColor || getThemeColor('--mcr-cover-auto-blend')
  }
  return autoBlendColor || resolveBlendColor(source, { ...params, colorSource: 'auto' }, autoBlendColor || getThemeColor('--mcr-cover-auto-blend'))
}

function getBackgroundColor(template: CustomStaticLayout, source: PreviewSourcePayload | null, params: SimulationParams, autoBlendColor?: string) {
  const background = template.background
  return resolveTemplateColor(
    background?.colorSource || params.colorSource || 'auto',
    background?.color,
    source,
    params,
    autoBlendColor,
  )
}

function renderGrainOverlay(width: number, height: number, grain: number) {
  const opacity = clamp(Number(grain || 0), 0, 1)
  if (!opacity) return ''
  return `<rect x="0" y="0" width="${width}" height="${height}" fill="${escapeXml(getThemeColor('--mcr-cover-grain'))}" filter="url(#mcr-film-grain)" opacity="${Math.min(0.45, opacity * 0.72)}" style="mix-blend-mode:overlay"/>`
}

function renderBackground(
  template: CustomStaticLayout,
  source: PreviewSourcePayload | null,
  params: SimulationParams,
  width: number,
  height: number,
  options: RenderOptions,
) {
  const backgroundConfig = template.background || { type: 'blurred-image-color' as const }
  const baseColor = getBackgroundColor(template, source, params, options.autoBlendColor)
  const wrapBackground = (content: string) => (
    backgroundConfig.maskPolygon ? `<g clip-path="url(#mcr-bg-mask)">${content}</g>` : content
  )
  const backgroundOpacity = clamp(Number(backgroundConfig.opacity ?? (backgroundConfig as any).colorOpacity ?? 1), 0, 1)
  const wrapBackgroundLayer = (content: string) => {
    const maskedContent = wrapBackground(content)
    if (!maskedContent || backgroundOpacity <= 0) return ''
    if (backgroundOpacity >= 1) return maskedContent
    return `<g opacity="${backgroundOpacity}">${maskedContent}</g>`
  }
  if (backgroundConfig.type === 'transparent') {
    return ''
  }
  if (backgroundConfig.type === 'solid') {
    return wrapBackgroundLayer(`<rect x="0" y="0" width="${width}" height="${height}" fill="${escapeXml(baseColor)}"/>${renderGrainOverlay(width, height, Number(backgroundConfig.grain ?? 0))}`)
  }
  if (backgroundConfig.type === 'gradient') {
    return wrapBackgroundLayer(`<rect x="0" y="0" width="${width}" height="${height}" fill="url(#mcr-bg-gradient)"/>${renderGrainOverlay(width, height, Number(backgroundConfig.grain ?? 0))}`)
  }

  const firstImage = getImageHref(source, Number(backgroundConfig.imageSource?.slot || 1))
  const overlayOpacity = clamp(Number(backgroundConfig.colorRatio ?? params.colorRatio ?? 0.8), 0, 1)
  const blur = Math.max(0, Number(backgroundConfig.blur ?? params.blur ?? 0))
  const pad = Math.max(width, height) * 0.06
  return wrapBackgroundLayer([
    `<rect x="0" y="0" width="${width}" height="${height}" fill="${escapeXml(baseColor)}"/>`,
    firstImage
      ? `<g filter="url(#mcr-bg-blur)" style="filter: blur(${blur}px);"><image href="${escapeXml(firstImage)}" xlink:href="${escapeXml(firstImage)}" x="${-pad}" y="${-pad}" width="${width + pad * 2}" height="${height + pad * 2}" preserveAspectRatio="xMidYMid slice" opacity="0.72"/></g>`
      : '',
    `<rect x="0" y="0" width="${width}" height="${height}" fill="${escapeXml(baseColor)}" opacity="${overlayOpacity}"/>`,
    renderGrainOverlay(width, height, Number(backgroundConfig.grain ?? 0)),
  ].join(''))
}

function renderImageLayer(layer: CustomImageLayer, source: PreviewSourcePayload | null, options: RenderOptions) {
  const href = getLayerImageHref(layer, source)
  const filterId = getFilterId(layer)
  const hasPolygonMask = Boolean(getLayerMaskPolygonPoints(layer))
  const hasClip = hasPolygonMask || Number(layer.radius || 0) > 0 || (layer.fit || 'cover') === 'cover'
  const clipPath = hasClip ? ` clip-path="url(#clip-${escapeXml(layer.id)})"` : ''
  const filter = filterId ? ` filter="url(#${filterId})"` : ''
  const opacity = clamp(Number(layer.opacity ?? layer.transform?.opacity ?? 1), 0, 1)
  const pointer = options.interactive ? ` data-layer-id="${escapeXml(layer.id)}" style="cursor:pointer"` : ''
  const escapedHref = escapeXml(href)
  const fitted = getFittedImageFrame(layer, source)
  const shadow = getShadowStyle(layer)
  const shadowClipPath = hasPolygonMask ? ` clip-path="url(#clip-${escapeXml(layer.id)})"` : ''
  const shadowNode = shadow
    ? `<rect x="${Number(layer.x) + shadow.offsetX}" y="${Number(layer.y) + shadow.offsetY}" width="${layer.width}" height="${layer.height}" rx="${Math.max(0, Number(layer.radius || 0))}" ry="${Math.max(0, Number(layer.radius || 0))}" fill="${escapeXml(shadow.color)}" opacity="${shadow.opacity}" style="filter: blur(${shadow.blur}px);"${shadowClipPath}/>`
    : ''
  const fittedClipPath = fitted.needsClip || hasPolygonMask ? ` clip-path="url(#clip-${escapeXml(layer.id)})"` : clipPath
  const placeholderNode = href ? '' : renderImagePlaceholder(layer)
  const imageNode = href
    ? `<image href="${escapedHref}" xlink:href="${escapedHref}" x="${fitted.x}" y="${fitted.y}" width="${fitted.width}" height="${fitted.height}" preserveAspectRatio="${fitted.preserveAspectRatio}"${fittedClipPath}/>`
    : ''
  const colorRatio = clamp(Number(layer.colorRatio ?? 0), 0, 1)
  const blendColor = resolveTemplateColor(
    layer.colorSource || 'none',
    layer.color,
    source,
    { blur: 50, colorRatio: 0.8, colorSource: 'auto', customColor: getThemeColor('--mcr-cover-auto-blend') },
    options.autoBlendColor,
  )
  const blendNode = blendColor && colorRatio > 0
    ? `<rect x="${layer.x}" y="${layer.y}" width="${layer.width}" height="${layer.height}" rx="${Math.max(0, Number(layer.radius || 0))}" ry="${Math.max(0, Number(layer.radius || 0))}" fill="${escapeXml(blendColor)}" opacity="${colorRatio}"${hasClip ? ` clip-path="url(#clip-${escapeXml(layer.id)})"` : ''}/>`
    : ''
  return `<g${pointer}${getLayerTransform(layer)} opacity="${opacity}"${filter}>${shadowNode}${placeholderNode}${imageNode}${blendNode}</g>`
}

function renderTextLayer(layer: CustomTitleLayer | CustomTextLayer, source: PreviewSourcePayload | null, options: RenderOptions) {
  if (getTextMaskMode(layer) !== 'normal') {
    return options.interactive
      ? `<rect data-layer-id="${escapeXml(layer.id)}" x="${layer.x}" y="${layer.y}" width="${layer.width}" height="${layer.height}" fill="transparent" style="cursor:pointer"${getLayerTransform(layer)}/>`
      : ''
  }
  const text = getTextContent(layer, source)
  const fontSize = Math.max(1, Number(layer.fontSize || 60))
  const lines = wrapText(text, fontSize, Math.max(1, Number(layer.width || 1)))
  const lineHeight = fontSize * 1.1
  const totalHeight = lines.length * lineHeight
  const startY = Number(layer.y || 0) + (Number(layer.height || 0) - totalHeight) / 2 + fontSize
  const align = layer.textAlign === 'left' || layer.textAlign === 'right' ? layer.textAlign : 'center'
  const x = align === 'left'
    ? Number(layer.x || 0)
    : align === 'right'
      ? Number(layer.x || 0) + Number(layer.width || 0)
      : Number(layer.x || 0) + Number(layer.width || 0) / 2
  const textAnchor = align === 'left' ? 'start' : align === 'right' ? 'end' : 'middle'
  const filterId = getFilterId(layer)
  const filter = filterId ? ` filter="url(#${filterId})"` : ''
  const opacity = clamp(Number(layer.opacity ?? layer.transform?.opacity ?? 1), 0, 1)
  const pointer = options.interactive ? ` data-layer-id="${escapeXml(layer.id)}" style="cursor:pointer"` : ''
  const tspans = lines.map((line, index) =>
    `<tspan x="${x}" y="${startY + index * lineHeight}">${escapeXml(line)}</tspan>`,
  ).join('')
  const shadow = getShadowStyle(layer)
  const shadowTspans = lines.map((line, index) =>
    `<tspan x="${x + (shadow?.offsetX || 0)}" y="${startY + index * lineHeight + (shadow?.offsetY || 0)}">${escapeXml(line)}</tspan>`,
  ).join('')
  const family = getFontFamily(layer, text)
  const shadowNode = shadow
    ? `<text font-family="${escapeXml(family)}" font-size="${fontSize}" font-weight="700" fill="${escapeXml(shadow.color)}" opacity="${shadow.opacity}" text-anchor="${textAnchor}" style="filter: blur(${shadow.blur}px);">${shadowTspans}</text>`
    : ''
  const textColor = resolveTemplateColor(
    layer.colorSource || 'custom',
    layer.color || getThemeColor('--mcr-cover-text'),
    source,
    { blur: 50, colorRatio: 0.8, colorSource: 'custom', customColor: getThemeColor('--mcr-cover-text') },
    getThemeColor('--mcr-cover-text'),
  ) || getThemeColor('--mcr-cover-text')
  return `<g${pointer}${getLayerTransform(layer)} opacity="${opacity}"${filter}>${shadowNode}<text font-family="${escapeXml(family)}" font-size="${fontSize}" font-weight="700" fill="${escapeXml(textColor)}" text-anchor="${textAnchor}">${tspans}</text></g>`
}

function renderSelection(layer: TemplateLayer | undefined) {
  if (!layer) return ''
  return `<rect x="${layer.x}" y="${layer.y}" width="${layer.width}" height="${layer.height}" fill="none" stroke="${escapeXml(getThemeColor('--mcr-cover-selection-stroke'))}" stroke-width="4" stroke-dasharray="16 10" pointer-events="none"${getLayerTransform(layer)}/>`
}

function renderLayer(layer: TemplateLayer, source: PreviewSourcePayload | null, options: RenderOptions): string {
  if (layer.type === 'group') {
    const group = layer as CustomGroupLayer
    const opacity = clamp(Number(group.opacity ?? group.transform?.opacity ?? 1), 0, 1)
    const pointer = options.interactive ? ` data-layer-id="${escapeXml(group.id)}" style="cursor:pointer"` : ''
    return `<g${pointer}${getLayerTransform(group)} opacity="${opacity}">${[...(group.children || [])].sort((a, b) => (a.zIndex || 0) - (b.zIndex || 0)).map((child) => renderLayer(child, source, options)).join('')}</g>`
  }
  if (isImageLayer(layer)) return renderImageLayer(layer, source, options)
  if (isTextLayer(layer)) return renderTextLayer(layer, source, options)
  return ''
}

function findLayer(layers: TemplateLayer[], id?: string | null): TemplateLayer | undefined {
  if (!id) return undefined
  for (const layer of layers) {
    if (layer.id === id) return layer
    if (layer.type === 'group') {
      const child = findLayer((layer as CustomGroupLayer).children || [], id)
      if (child) return child
    }
  }
  return undefined
}

export function renderTemplateSvg(
  layout: CustomStaticLayout | null | undefined,
  source: PreviewSourcePayload | null,
  params: SimulationParams,
  options: RenderOptions = {},
) {
  const template = normalizeTemplate(layout)
  const width = template.canvas?.width || 1920
  const height = template.canvas?.height || 1080
  const background = renderBackground(template, source, params, width, height, options)
  const bgBlur = Math.max(0, Number(template.background?.blur ?? params.blur ?? 0))
  const gradientColor = getBackgroundColor(template, source, params, options.autoBlendColor)
  const gradientColor2 = template.background?.color2 || getThemeColor('--mcr-cover-deep-gradient')
  const filmGrainFilter = '<filter id="mcr-film-grain" x="0" y="0" width="100%" height="100%" color-interpolation-filters="sRGB"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3" seed="17" result="noise"/><feColorMatrix in="noise" type="matrix" values="0.33 0.33 0.33 0 0 0.33 0.33 0.33 0 0 0.33 0.33 0.33 0 0 0 0 0 0.48 0" result="monoNoise"/><feComponentTransfer in="monoNoise"><feFuncR type="linear" slope="1.8" intercept="-0.38"/><feFuncG type="linear" slope="1.8" intercept="-0.38"/><feFuncB type="linear" slope="1.8" intercept="-0.38"/></feComponentTransfer></filter>'
  const backgroundMaskPoints = getMaskPolygonPoints(template.background?.maskPolygon, 0, 0, width, height)
  const backgroundMaskDef = backgroundMaskPoints
    ? `<clipPath id="mcr-bg-mask" clipPathUnits="userSpaceOnUse"><polygon points="${backgroundMaskPoints}"/></clipPath>`
    : ''
  const textMaskDef = renderTextMaskDef(template.layers, source, width, height)
  const defs = `<defs><linearGradient id="mcr-bg-gradient" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="${escapeXml(gradientColor)}"/><stop offset="100%" stop-color="${escapeXml(gradientColor2)}"/></linearGradient>${backgroundMaskDef}${textMaskDef}${filmGrainFilter}<filter id="mcr-bg-blur" x="${-width}" y="${-height}" width="${width * 3}" height="${height * 3}" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB"><feGaussianBlur in="SourceGraphic" stdDeviation="${bgBlur}"/></filter></defs>${renderDefs(template.layers, width, height)}`
  const layers = [...template.layers].sort((a, b) => (a.zIndex || 0) - (b.zIndex || 0))
  const backgroundZIndex = Number(template.background?.zIndex ?? 0)
  const underBackgroundLayers = layers.filter((layer) => Number(layer.zIndex || 0) < backgroundZIndex)
  const overBackgroundLayers = layers.filter((layer) => Number(layer.zIndex || 0) >= backgroundZIndex)
  const selectedLayer = findLayer(layers, options.selectedLayerId)
  const body = `${underBackgroundLayers.map((layer) => renderLayer(layer, source, options)).join('')}${background}${overBackgroundLayers.map((layer) => renderLayer(layer, source, options)).join('')}`
  const maskedBody = textMaskDef ? `<g mask="url(#mcr-text-mask)">${body}</g>` : body
  return `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 ${width} ${height}" width="100%" height="100%" overflow="hidden" role="img" data-template-schema="mcr-template/v1">${defs}${maskedBody}${renderSelection(selectedLayer)}</svg>`
}
