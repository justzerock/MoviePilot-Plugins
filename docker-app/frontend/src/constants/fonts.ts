export const BUILTIN_FONT_ITEMS = [
  { title: '潮黑 chaohei', value: 'chaohei' },
  { title: '粗雅宋 yasong', value: 'yasong' },
  { title: 'Emblema One', value: 'EmblemaOne' },
  { title: 'Melete', value: 'Melete' },
  { title: 'Phosphate', value: 'Phosphate' },
  { title: 'Josefin Sans', value: 'JosefinSans' },
  { title: 'Lilita One', value: 'LilitaOne' },
]

export const SEMANTIC_FONT_ITEMS = [
  { title: '主标题字体', value: 'main_title' },
  { title: '副标题字体', value: 'subtitle' },
  { title: '自定义文本字体', value: 'custom_text' },
]

export function getTemplateFontFaceName(fontFamily?: string | null) {
  if (fontFamily === 'subtitle') return 'McrSubtitleFont'
  if (fontFamily === 'custom_text') return 'McrCustomTextFont'
  if (!fontFamily || fontFamily === 'main_title') return 'McrMainTitleFont'
  return `McrFont_${String(fontFamily).replace(/[^a-zA-Z0-9_-]/g, '_')}`
}

export function containsCjkText(value?: string | null) {
  return /[\u3400-\u9fff]/.test(String(value || ''))
}

export function isCjkFontFamily(fontFamily?: string | null) {
  const normalized = String(fontFamily || '').toLowerCase().replace(/[\s_-]+/g, '')
  return [
    'chaohei',
    'yasong',
    'wenquanyi',
    'wqy',
    'notosanscjk',
    'notoserifcjk',
    'sourcehansans',
    'sourcehanserif',
    'sarasa',
    'unifont',
    'ipag',
  ].some((token) => normalized.includes(token))
}

export function getTemplateFontFamilyStack(fontFamily?: string | null, text?: string | null) {
  const primary = getTemplateFontFaceName(fontFamily || 'main_title')
  const systemCjk = '"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans CJK SC", "WenQuanYi Zen Hei"'
  if (containsCjkText(text) && !isCjkFontFamily(fontFamily)) {
    return `McrFont_chaohei, McrFont_yasong, ${primary}, ${systemCjk}, sans-serif`
  }
  return `${primary}, ${systemCjk}, sans-serif`
}
