function readCssVariable(name: string): string {
  if (typeof document === 'undefined') return ''
  const rootValue = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  if (rootValue) return rootValue
  return getComputedStyle(document.body).getPropertyValue(name).trim()
}

export function getThemeColor(name: string, fallbackName = '--mcr-color-on-surface'): string {
  return readCssVariable(name) || readCssVariable(fallbackName)
}

export function getThemeRgba(rgbName: string, alpha: number, fallbackRgbName = '--mcr-rgb-on-surface'): string {
  const channels = readCssVariable(rgbName) || readCssVariable(fallbackRgbName)
  return channels ? `rgba(${channels}, ${alpha})` : getThemeColor('--mcr-color-on-surface')
}
