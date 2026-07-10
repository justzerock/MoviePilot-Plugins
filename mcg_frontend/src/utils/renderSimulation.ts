import type {
  CustomImageLayer,
  CustomStaticLayout,
  CustomTextFontFamily,
  CustomTextLayer,
  CustomTitleLayer,
  PreviewSourcePayload,
  SimulationParams,
} from '../types/plugin'
import { getTemplateFontFamilyStack } from '../constants/fonts'
import { EDITOR_BASE_HEIGHT, EDITOR_BASE_WIDTH, getTextLayerFontFamily, normalizeLayerEffects } from './customLayout'
import { getThemeColor } from './themeColors'

export type RenderLayer = CustomImageLayer | CustomTitleLayer | CustomTextLayer

const getDefaultBlendColor = () => getThemeColor('--mcr-cover-auto-blend')
const loadedImages = new Map<string, Promise<HTMLImageElement>>()

export function getDocumentSize(layout?: CustomStaticLayout | null) {
  return {
    width: Math.max(1, Number(layout?.document?.width || EDITOR_BASE_WIDTH)),
    height: Math.max(1, Number(layout?.document?.height || EDITOR_BASE_HEIGHT)),
  }
}

export function normalizeHexColor(value?: string | null) {
  const raw = String(value || '').trim()
  if (!raw) return ''
  const hex = raw.startsWith('#') ? raw : `#${raw}`
  if (/^#[0-9a-fA-F]{6}$/.test(hex)) return hex.toLowerCase()
  return ''
}

export function hexToRgb(hex: string) {
  const normalized = normalizeHexColor(hex) || normalizeHexColor(getDefaultBlendColor())
  return {
    r: parseInt(normalized.slice(1, 3), 16),
    g: parseInt(normalized.slice(3, 5), 16),
    b: parseInt(normalized.slice(5, 7), 16),
  }
}

export function rgbToHex(r: number, g: number, b: number) {
  const toHex = (value: number) => Math.max(0, Math.min(255, Math.round(value))).toString(16).padStart(2, '0')
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`
}

export function hexToRgba(hex: string, alpha: number) {
  const { r, g, b } = hexToRgb(hex)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

export function rgbToHsl(r: number, g: number, b: number) {
  const rn = r / 255
  const gn = g / 255
  const bn = b / 255
  const max = Math.max(rn, gn, bn)
  const min = Math.min(rn, gn, bn)
  let h = 0
  let s = 0
  const l = (max + min) / 2

  if (max !== min) {
    const d = max - min
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min)
    switch (max) {
      case rn:
        h = (gn - bn) / d + (gn < bn ? 6 : 0)
        break
      case gn:
        h = (bn - rn) / d + 2
        break
      default:
        h = (rn - gn) / d + 4
        break
    }
    h /= 6
  }

  return { h, s, l }
}

export function hslToRgb(h: number, s: number, l: number) {
  if (s === 0) {
    const gray = l * 255
    return { r: gray, g: gray, b: gray }
  }

  const hue2rgb = (p: number, q: number, t: number) => {
    let tt = t
    if (tt < 0) tt += 1
    if (tt > 1) tt -= 1
    if (tt < 1 / 6) return p + (q - p) * 6 * tt
    if (tt < 1 / 2) return q
    if (tt < 2 / 3) return p + (q - p) * (2 / 3 - tt) * 6
    return p
  }

  const q = l < 0.5 ? l * (1 + s) : l + s - l * s
  const p = 2 * l - q
  return {
    r: hue2rgb(p, q, h + 1 / 3) * 255,
    g: hue2rgb(p, q, h) * 255,
    b: hue2rgb(p, q, h - 1 / 3) * 255,
  }
}

export function adjustHexColor(hex: string, lightnessOffset: number) {
  const { r, g, b } = hexToRgb(hex)
  const { h, s, l } = rgbToHsl(r, g, b)
  const nextL = Math.min(0.84, Math.max(0.18, l + lightnessOffset))
  const nextS = Math.min(0.72, Math.max(0.24, s))
  const next = hslToRgb(h, nextS, nextL)
  return rgbToHex(next.r, next.g, next.b)
}

export function darkenHexColor(hex: string, amount: number) {
  return adjustHexColor(hex, -Math.abs(amount))
}

export function lightenHexColor(hex: string, amount: number) {
  return adjustHexColor(hex, Math.abs(amount))
}

export function loadImage(src: string) {
  const cached = loadedImages.get(src)
  if (cached) return cached
  const pending = new Promise<HTMLImageElement>((resolve, reject) => {
    const image = new Image()
    image.decoding = 'async'
    image.onload = () => resolve(image)
    image.onerror = reject
    image.src = src
  })
  loadedImages.set(src, pending)
  return pending
}

export async function extractComfortableColor(src: string) {
  try {
    const image = await loadImage(src)
    const canvas = document.createElement('canvas')
    canvas.width = 48
    canvas.height = 48
    const context = canvas.getContext('2d', { willReadFrequently: true })
    if (!context) return ''
    context.drawImage(image, 0, 0, canvas.width, canvas.height)
    const { data } = context.getImageData(0, 0, canvas.width, canvas.height)

    let totalR = 0
    let totalG = 0
    let totalB = 0
    let totalWeight = 0

    for (let index = 0; index < data.length; index += 4) {
      const alpha = data[index + 3]
      if (alpha < 160) continue
      const r = data[index]
      const g = data[index + 1]
      const b = data[index + 2]
      const { s, l } = rgbToHsl(r, g, b)
      if (l < 0.16 || l > 0.86) continue
      const weight = 0.55 + Math.min(0.45, s)
      totalR += r * weight
      totalG += g * weight
      totalB += b * weight
      totalWeight += weight
    }

    if (!totalWeight) return ''
    const base = rgbToHex(totalR / totalWeight, totalG / totalWeight, totalB / totalWeight)
    return adjustHexColor(base, -0.06)
  } catch (error) {
    console.error('extractComfortableColor failed', error)
    return ''
  }
}

export function resolveBlendColor(source: PreviewSourcePayload | null, params: SimulationParams, autoColor = DEFAULT_BLEND_COLOR) {
  if (params.colorSource === 'custom') {
    return normalizeHexColor(params.customColor) || autoColor
  }
  if (params.colorSource === 'config') {
    return normalizeHexColor(source?.bg_color || '') || autoColor
  }
  return autoColor
}

export function buildBackgroundStyle(imageSrc: string | undefined, blur: number, strong = false) {
  return {
    backgroundImage: imageSrc ? `url(${imageSrc})` : 'none',
    backgroundPosition: 'center',
    backgroundSize: 'cover',
    filter: `blur(${Math.max(0, blur) / (strong ? 10 : 8)}px)${strong ? ' brightness(0.82)' : ''}`,
    transform: `scale(${strong ? 1.04 : 1.08})`,
  }
}

export function buildOverlayStyle(color: string, colorRatio: number) {
  return {
    background: hexToRgba(color, 1),
    opacity: String(Math.min(0.9, Math.max(0.08, colorRatio))),
  }
}

export function getLayerFrameStyle(layer: RenderLayer) {
  const normalized = normalizeLayerEffects(layer)
  return {
    left: `${normalized.x}px`,
    top: `${normalized.y}px`,
    width: `${normalized.width}px`,
    height: `${normalized.height}px`,
    zIndex: String(normalized.zIndex || 0),
  }
}

export function getLayerTransformStyle(layer: RenderLayer) {
  const normalized = normalizeLayerEffects(layer)
  return {
    transform: `rotate(${normalized.rotation || 0}deg)`,
    transformOrigin: `${(normalized.pivotX ?? 0.5) * 100}% ${(normalized.pivotY ?? 0.5) * 100}%`,
  }
}

export function getPreviewFontFamily(fontFamily?: CustomTextFontFamily, text?: string) {
  return getTemplateFontFamilyStack(fontFamily, text)
}

export function getKonvaFontFamily(fontFamily?: CustomTextFontFamily, text?: string) {
  return getTemplateFontFamilyStack(fontFamily || 'main_title', text)
}

export function getTextFamilyFromLayer(layer: CustomTitleLayer | CustomTextLayer) {
  return getTextLayerFontFamily(normalizeLayerEffects(layer))
}
