export interface YahahaCoverStudioConfig {
  enabled: boolean
  auto_save_config?: boolean
  update_now: boolean
  transfer_monitor: boolean
  monitor_source?: 'transfer' | 'emby'
  lock_latest_sort?: boolean
  cron: string
  delay: number
  selected_servers: string[]
  all_servers?: string[] | { title?: string; name?: string; value?: string }[]
  include_libraries: string[]
  all_libraries?: { name: string; value: string }[] | null
  sort_by: string
  covers_input: string
  covers_output: string
  save_recent_covers: boolean
  history_retention_batches?: number
  covers_history_limit_per_library: number
  covers_page_history_limit: number
  title_config: string
  title_config_strict: boolean
  distinguish_same_name_libraries?: boolean
  cover_style_base: string
  cover_style_variant: 'static' | 'animated'
  main_title_font_preset: string
  subtitle_font_preset: string
  custom_text_font_preset: string
  main_title_font_custom: string
  subtitle_font_custom: string
  custom_text_font_custom: string
  main_title_font_size: number | null
  subtitle_font_size: number | null
  blur_size: number
  color_ratio: number
  title_scale: number
  poster_source?: 'backdrop' | 'poster'
  use_primary?: boolean
  image_count_mode?: 'auto' | 'fixed'
  image_count?: number
  main_title_font_offset: string | number | null
  title_spacing: string | number | null
  subtitle_line_spacing: string | number | null
  resolution: string
  custom_width: number
  custom_height: number
  bg_color_mode: string
  custom_bg_color: string
  animation_duration: number
  animation_scroll: string
  animation_fps: number
  animation_format: 'apng' | 'gif'
  animation_resolution: string
  animation_reduce_colors: 'off' | 'medium' | 'strong'
  animated_2_image_count: number
  animated_2_departure_type: 'fly' | 'fade' | 'crossfade'
  animated_settings?: Partial<Record<AnimatedStyleKey, AnimatedStyleSettings>>
  clean_images: boolean
  clean_fonts: boolean
  backup_enabled: boolean
  backup_cron: string
  backup_path: string
  page_tab: 'generate-tab' | 'custom-tab' | 'history-tab' | 'clean-tab'
  style_naming_v2: boolean
  custom_static_layout?: CustomStaticLayout | null
  custom_static_layouts?: CustomStaticLayoutTemplate[] | null
  custom_static_active_id?: string | null
  preview_font_enabled?: boolean
  font_subset_enabled?: boolean
  font_script_adaptation_enabled?: boolean
  font_script_target?: 'auto' | 'simplified' | 'traditional'
  font_traditional_variant?: 'standard' | 'taiwan' | 'hongkong'
  library_scheme_rules?: LibrarySchemeRule[]
  default_scheme_id?: string
  scheme_catalog?: SchemeCatalogItem[]
}

export interface LibrarySchemeRule {
  id: string
  scheme_id: string
  library_keys: string[]
}

export interface SchemeCatalogItem {
  id: string
  name: string
}

export type CustomLayerType = 'image' | 'main_title' | 'subtitle' | 'title_zh' | 'title_en' | 'text'
export type CustomTextFontFamily = string
export type TemplateLayerType = CustomLayerType | 'group'
export type TemplateImageFit = 'cover' | 'contain' | 'stretch'
export type TemplateTextMaskMode = 'normal' | 'knockout-text' | 'show-text'
export type PreviewMode = 'frontend' | 'backend'
export type PreviewSourceMode = 'custom' | 'cache' | 'media_server'
export type CoverStyleBase = 'static_1' | 'static_2' | 'static_3' | 'static_4' | 'custom_static'
export type CoverStyleVariant = 'static' | 'animated'
export type AnimatedStyleKey = 'animated_1' | 'animated_2' | 'animated_3' | 'animated_4'

export interface AnimatedStyleSettings {
  animation_duration?: number
  animation_fps?: number
  animation_format?: 'apng' | 'gif'
  animation_scroll?: 'down' | 'up' | 'alternate' | 'alternate_reverse'
  animation_reduce_colors?: 'off' | 'medium' | 'strong'
  animated_2_image_count?: number
  animated_2_departure_type?: 'fly' | 'fade' | 'crossfade'
  main_title_font_preset?: string
  subtitle_font_preset?: string
  custom_text_font_preset?: string
  main_title_font_size?: number
  subtitle_font_size?: number
  blur_size?: number
  color_ratio?: number
  title_scale?: number
}

export interface TemplateTransform {
  rotation?: number
  pivotX?: number
  pivotY?: number
  opacity?: number
}

export interface TemplateShadow {
  blur?: number
  offsetX?: number
  offsetY?: number
  opacity?: number
  color?: string
}

export interface TemplateEffects {
  blur?: number
  shadow?: TemplateShadow
}

export interface TemplateImageSource {
  kind: 'slot'
  slot: number
}

export interface TemplateMaskPolygon {
  units?: 'relative' | 'absolute'
  points: Array<[number, number]>
}

export interface CustomLayerBase {
  id: string
  type: TemplateLayerType
  x: number
  y: number
  width: number
  height: number
  rotation?: number
  radius?: number
  zIndex: number
  pivotX?: number
  pivotY?: number
  opacity?: number
  blur?: number
  shadowBlur?: number
  shadowOffsetX?: number
  shadowOffsetY?: number
  shadowOpacity?: number
  transform?: TemplateTransform
  effects?: TemplateEffects
  children?: TemplateLayer[]
}

export interface CustomImageLayer extends CustomLayerBase {
  type: 'image'
  sourceIndex: number
  source?: TemplateImageSource
  assetKind?: 'source' | 'sticker'
  stickerDataUrl?: string
  stickerPath?: string
  stickerUrl?: string
  stickerName?: string
  stickerWidth?: number
  stickerHeight?: number
  fit?: TemplateImageFit
  cropFocusX?: number
  cropFocusY?: number
  maskPolygon?: TemplateMaskPolygon
  colorSource?: 'none' | 'auto' | 'custom' | 'config'
  color?: string
  colorRatio?: number
}

export interface CustomTitleLayer extends CustomLayerBase {
  type: 'main_title' | 'subtitle' | 'title_zh' | 'title_en'
  fontSize: number
  fontFamily?: CustomTextFontFamily
  colorSource?: 'auto' | 'custom' | 'config'
  color?: string
  textAlign?: 'left' | 'center' | 'right'
  maskMode?: TemplateTextMaskMode
}

export interface CustomTextLayer extends CustomLayerBase {
  type: 'text'
  fontSize: number
  content: string
  contentSource?: 'fixed' | 'library'
  contentKey?: string
  fontFamily?: CustomTextFontFamily
  colorSource?: 'auto' | 'custom' | 'config'
  color?: string
  textAlign?: 'left' | 'center' | 'right'
  maskMode?: TemplateTextMaskMode
}

export interface CustomGroupLayer extends CustomLayerBase {
  type: 'group'
  children: TemplateLayer[]
}

export type TemplateLayer = CustomImageLayer | CustomTitleLayer | CustomTextLayer | CustomGroupLayer

export interface CustomStaticLayout {
  schema?: 'mcr-template/v1'
  version: 1 | string
  canvas?: {
    width: number
    height: number
    unit?: 'px'
  }
  background?: {
    type: 'transparent' | 'blurred-image-color' | 'solid' | 'gradient'
    imageSource?: TemplateImageSource
    colorSource?: 'auto' | 'custom' | 'config'
    color?: string
    color2?: string
    colorRatio?: number
    opacity?: number
    blur?: number
    grain?: number
    zIndex?: number
    maskPolygon?: TemplateMaskPolygon
  }
  document?: {
    width: number
    height: number
    unit?: 'px'
  }
  assets?: Record<string, any>
  layers: TemplateLayer[]
  computed?: {
    textLayout?: Record<string, CustomMeasuredTextLayout>
  }
}

export interface CustomMeasuredTextLine {
  text: string
  x: number
  y: number
  width: number
  height: number
}

export interface CustomMeasuredTextLayout {
  text: string
  font_size: number
  line_height: number
  frame: {
    x: number
    y: number
    width: number
    height: number
  }
  rotation: number
  opacity: number
  blur: number
  pivot: {
    x: number
    y: number
  }
  shadow: {
    blur: number
    offset_x: number
    offset_y: number
    opacity: number
  }
  lines: CustomMeasuredTextLine[]
}

export interface CustomStaticLayoutTemplate {
  id: string
  name: string
  layout: CustomStaticLayout
  baseStyle?: string
  system?: boolean
}

export interface PreviewSourceImage {
  slot: number
  src: string
  kind: PreviewSourceMode
  label: string
  width?: number
  height?: number
}

export interface PreviewTitles {
  zh: string
  en: string
}

export interface PreviewFontFace {
  url: string
  font_id?: string
  font_family?: string
  version?: string
  source_type?: 'subset' | 'original' | 'remote' | 'disabled'
  subset_status?: 'ready' | 'pending' | 'building' | 'failed' | 'disabled'
  charset_hash?: string
}

export interface PreviewSourcePayload {
  server: string
  library: string
  style: string
  cover_style_base: CoverStyleBase
  cover_style_variant: CoverStyleVariant
  source_mode: PreviewSourceMode
  titles: PreviewTitles
  custom_texts?: Record<string, string>
  title_config_version?: string
  images: PreviewSourceImage[]
  custom_static_layout?: CustomStaticLayout | null
  bg_color?: string | null
  font_faces?: Partial<Record<string, PreviewFontFace | string>>
}

export interface BackendPreviewPayload {
  src: string
  server: string
  library: string
  style: string
}

export interface SimulationParams {
  blur: number
  colorRatio: number
  colorSource: 'auto' | 'config' | 'custom'
  customColor: string
}

export interface StatusPayload {
  warnings: string[]
  enabled: boolean
  title_config_version?: string
  auto_save_config?: boolean
  has_selected_servers: boolean
  servers_ready: boolean
  transfer_monitor?: boolean
  lock_latest_sort?: boolean
  is_generating?: boolean
  generation_source?: string | null
  generation_style?: string | null
  generation_current?: number
  generation_total?: number
  generation_label?: string
  all_servers?: string[] | { title?: string; name?: string; value?: string }[]
  selected_servers?: string[]
  include_libraries?: string[]
  all_libraries?: { name: string; value: string }[] | null
  monitor_source?: 'transfer' | 'emby'
  cover_style_base: CoverStyleBase
  cover_style_variant: CoverStyleVariant
  poster_source?: 'backdrop' | 'poster'
  use_primary?: boolean
  sort_by?: string
  image_count_mode?: 'auto' | 'fixed'
  image_count?: number
  auto_image_count?: number
  resolution?: string
  animation_resolution?: string
  custom_width?: number
  custom_height?: number
  animation_duration?: number
  animation_fps?: number
  animation_format?: 'apng' | 'gif'
  animation_scroll?: 'down' | 'up' | 'alternate' | 'alternate_reverse'
  animation_reduce_colors?: 'off' | 'medium' | 'strong'
  animated_2_image_count?: number
  animated_2_departure_type?: 'fly' | 'fade' | 'crossfade'
  main_title_font_preset?: string
  subtitle_font_preset?: string
  custom_text_font_preset?: string
  main_title_font_size?: number
  subtitle_font_size?: number
  blur_size?: number
  color_ratio?: number
  title_scale?: number
  animated_settings?: Partial<Record<AnimatedStyleKey, AnimatedStyleSettings>>
  custom_static_layout?: CustomStaticLayout | null
  custom_static_layouts?: CustomStaticLayoutTemplate[] | null
  custom_static_active_id?: string | null
}

export interface PluginApi {
  get<T = any>(path: string, params?: any): Promise<T>
  post<T = any>(path: string, data?: any): Promise<T>
  delete?<T = any>(path: string, data?: any): Promise<T>
}
