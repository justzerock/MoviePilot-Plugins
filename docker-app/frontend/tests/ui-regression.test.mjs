import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const page = readFileSync(new URL('../src/components/Page.vue', import.meta.url), 'utf8')
const config = readFileSync(new URL('../src/components/Config.vue', import.meta.url), 'utf8')
const navigation = readFileSync(new URL('../src/components/SettingsAnchorNav.vue', import.meta.url), 'utf8')
const posterStack = readFileSync(new URL('../src/components/HistoryPosterStack.vue', import.meta.url), 'utf8')
const expansionLayer = readFileSync(new URL('../src/components/HistoryExpansionLayer.vue', import.meta.url), 'utf8')
const blueprintSelect = readFileSync(new URL('../src/components/BlueprintSelect.vue', import.meta.url), 'utf8')
const dateTime = readFileSync(new URL('../src/utils/dateTime.ts', import.meta.url), 'utf8')
const contentCache = readFileSync(new URL('../src/services/contentCache.ts', import.meta.url), 'utf8')
const layoutEditor = readFileSync(new URL('../src/components/CustomLayoutEditor.vue', import.meta.url), 'utf8')
const svgTemplate = readFileSync(new URL('../src/utils/svgTemplate.ts', import.meta.url), 'utf8')
const customLayout = readFileSync(new URL('../src/utils/customLayout.ts', import.meta.url), 'utf8')
const app = readFileSync(new URL('../src/App.vue', import.meta.url), 'utf8')
const authGate = readFileSync(new URL('../src/components/AuthGate.vue', import.meta.url), 'utf8')
const dockerApi = readFileSync(new URL('../src/dockerApi.ts', import.meta.url), 'utf8')
const compactHeaderScrollRoot = readFileSync(new URL('../src/utils/compactHeaderScrollRoot.ts', import.meta.url), 'utf8')
const applePolish = readFileSync(new URL('../src/styles/applePolish.css', import.meta.url), 'utf8')

test('history starts in the time-machine view', () => {
  assert.match(page, /historyGroupMode = ref<'library' \| 'time-machine'>\('time-machine'\)/)
})

test('time-machine uses a central alternating axis with stable sides', () => {
  assert.match(page, /grid-template-areas: "poster axis meta"/)
  assert.match(page, /is-right \{ grid-template-areas: "meta axis poster"/)
  assert.match(page, /historyRecordSides\.has\(group\.key\)/)
  assert.match(page, /neighborSide === 'left' \? 'right' : 'left'/)
  assert.match(page, /formatTimelineDate\(timestamp\)/)
  assert.match(page, /formatTimelineClock\(timestamp\)/)
  assert.match(dateTime, /export function formatTimelineClock/)
  assert.match(page, /border-top: 1px dashed/)
  assert.doesNotMatch(page, /historySortMode/)
  assert.doesNotMatch(page, /mcr-history-sort/)
  assert.match(posterStack, /v-if="mode !== 'time-machine' \|\| expanded"/)
})

test('real cover count is not limited by the stack preview depth', () => {
  assert.match(posterStack, /\{\{ items\.length \}\} 张/)
  assert.match(posterStack, /index >= stackLimit/)
  assert.match(posterStack, /\+\{\{ items\.length - stackLimit \}\}/)
  assert.doesNotMatch(posterStack, /Math\.min\([^)]*3/)
})

test('history expansion is one fixed page layer and not a dialog', () => {
  assert.match(page, /<HistoryExpansionLayer/)
  assert.match(page, /:expanded="false"/)
  assert.match(page, /v-if="expandedHistoryGroupId && selectedHistoryPaths\.length"/)
  assert.match(page, /\.mcr-history-floating-actions \{\s*z-index: 2147483200 !important;/)
  assert.match(expansionLayer, /<Teleport to="body">/)
  assert.match(expansionLayer, /position:\s*fixed;\s*inset:\s*0/)
  assert.match(expansionLayer, /canRestore/)
  assert.match(expansionLayer, /emit\('restore'\)/)
  assert.match(page, /:can-restore="historyGroupMode === 'time-machine'"/)
  assert.doesNotMatch(expansionLayer, /<v-dialog/)
  assert.doesNotMatch(expansionLayer, /grid-column:\s*1\s*\/\s*-1/)
})

test('library grid is centered and remains two columns on mobile', () => {
  assert.match(page, /justify-content: center !important/)
  assert.match(page, /flex-wrap: wrap/)
  assert.match(page, /flex-basis: calc\(\(100% - 9px\) \/ 2\)/)
})

test('settings navigation resolves the actual scroll root and is disabled on mobile', () => {
  assert.match(navigation, /v-if="navigationEnabled"/)
  assert.match(navigation, /function resolveScrollRoot\(\)/)
  assert.match(navigation, /closest<HTMLElement>\('\.mcr-config-app, \.mcr-frame'\)/)
  assert.match(navigation, /const minLeft = Math\.max\(viewportPadding, \(hostRect\?\.left \?\? 0\) \+ 8\)/)
  assert.match(navigation, /root: scrollRoot/)
  assert.match(navigation, /props\.contentElement\?\.querySelector<HTMLElement>/)
  assert.match(navigation, /@pointerdown\.prevent/)
  const scrollHandler = navigation.match(/function scrollToSection\(id: string\) \{([\s\S]*?)\n\}/)?.[1] || ''
  assert.match(scrollHandler, /if \(scrollRoot && !scrollRoot\.isConnected\)/)
  assert.doesNotMatch(navigation, /scrollIntoView/)
})

test('loading title breathes with opacity only', () => {
  const keyframes = page.match(/@keyframes yh-title-breathe \{([\s\S]*?)\n\}/)?.[1] || ''
  assert.match(keyframes, /opacity/)
  assert.doesNotMatch(keyframes, /scale|transform/)
  assert.match(page, /will-change: opacity/)
})

test('configuration controls stay compact and generation progress belongs to the run button', () => {
  assert.match(config, /class="yh-scheme-assignment-toolbar"/)
  assert.match(config, /class="yh-scheme-assignment__fields"/)
  assert.match(config, /class="yh-scheme-assignment__remove"/)
  assert.match(config, /class="mcr-font-switch-card"/)
  assert.match(config, /configGenerationProgressCount/)
  assert.match(page, /generationProgressCount/)
  assert.doesNotMatch(page, /backendBusyLabel/)
  assert.doesNotMatch(page, /<AsyncStatusDots v-if="backendBusy"/)
})

test('history, headers, scheme rules, and teleported selects share neutral themed materials', () => {
  assert.match(expansionLayer, /--yh-history-panel: rgba\(250, 250, 252, 0\.62\)/)
  assert.match(expansionLayer, /backdrop-filter: blur\(32px\) saturate\(140%\)/)
  assert.match(expansionLayer, /prefers-reduced-transparency: reduce/)
  assert.match(expansionLayer, /--yh-history-selection: rgba\(22, 119, 255, 0\.055\)/)
  assert.match(expansionLayer, /scale\(\.94\)/)
  assert.match(expansionLayer, /prefers-reduced-motion: reduce/)
  assert.match(page, /class="yh-compact-page-header__avatar"/)
  assert.match(page, /yh-icon-btn yh-header-control/)
  assert.match(config, /class="yh-settings-title-glyph"/)
  assert.match(config, /class="yh-compact-config-header__identity"/)
  assert.match(config, /font-size: clamp\(42px, 4vw, 66px\)/)
  assert.match(applePolish, /\.mcr-config-shell \.yh-scheme-assignment-toolbar/)
  assert.match(applePolish, /\.yh-header-control\.yh-header-control/)
  assert.match(applePolish, /border-radius: 12px !important/)
  assert.match(applePolish, /\.yh-settings-title-glyph,\s*\.yh-compact-config-header__glyph \{[\s\S]*?background: transparent/)
  assert.match(applePolish, /\.yh-scheme-assignment \{[\s\S]*?background: var\(--color-surface-soft\)/)
  assert.match(applePolish, /\.mcr-blueprint-select__popover\[data-mcr-theme="dark"\][\s\S]*?--yh-popover-bg: rgba\(28, 28, 30, 0\.90\)/)
  assert.match(applePolish, /\.yh-scheme-assignment__fields[\s\S]*?grid-template-rows: 15px 42px/)
  assert.match(applePolish, /\.mcr-config-top-actions \.yh-header-control\.yh-header-control:not\(\.is-running\)/)
  assert.match(blueprintSelect, /popover\[data-mcr-theme="dark"\][\s\S]*?background: rgba\(28, 28, 30, 0\.98\)/)
  assert.match(blueprintSelect, /background: rgba\(10, 132, 255, 0\.18\)/)
})

test('history cache persists an explicit plain-data snapshot', () => {
  assert.match(contentCache, /HISTORY_CACHE_SCHEMA = 2/)
  assert.match(contentCache, /const persistedPayload = toJsonValue\(payload\)/)
  assert.doesNotMatch(contentCache, /lastUsedAt: now, payload \}/)
})

test('preview cache never pins a font while its subset is still building', () => {
  assert.match(contentCache, /PREVIEW_CACHE_SCHEMA = 9/)
  assert.match(contentCache, /face\.subsetStatus === 'pending' \|\| face\.subsetStatus === 'building'/)
})

test('scheme actions support multi-select sharing and bundle imports', () => {
  assert.match(page, /分享 \{\{ selectedSchemeShareIds\.length \}\} 个方案/)
  assert.match(page, /mcr-custom-static-template-bundle\/v1/)
  assert.match(page, /Array\.isArray\(parsed\?\.templates\)/)
  assert.match(page, /复制当前方案/)
  assert.doesNotMatch(page, />\s*导入方案\s*</)
  assert.match(page, /if \(schemeShareMode\.value\) return false/)
})

test('scheme menus and multi-select cards keep explicit contrast in both themes', () => {
  assert.match(page, /mcr-template-action-menu\[data-mcr-theme="light"\]/)
  assert.match(page, /color: #182033 !important/)
  assert.match(page, /mcr-scheme-row--share-selected::after/)
  assert.match(page, /background: #1677ff !important/)
  assert.match(page, /data-mcr-theme="dark"\] \.mcr-scheme-row--share-selected/)
})

test('docker app gates destructive APIs behind a persistent login', () => {
  assert.match(app, /authState === 'loading'/)
  assert.match(app, /<AuthGate/)
  assert.match(app, /logoutDocker/)
  assert.match(authGate, /设置管理员账号/)
  assert.match(authGate, /登录状态会安全保存在当前浏览器/)
  assert.match(dockerApi, /Authorization = `Bearer \$\{token\}`/)
  assert.match(dockerApi, /credentials: 'same-origin'/)
})

test('donation overview uses backend statistics and the default scheme indicator', () => {
  assert.match(page, /data\.history_cover_count/)
  assert.match(page, /data\.execution_count/)
  assert.match(page, /defaultSchemeIsAnimated/)
  assert.doesNotMatch(page, /<small>Active<\/small>/)
})

test('time-machine restore follows the metadata side and expanded cards keep a stable size', () => {
  assert.match(page, /historyRecordSide\(group\.key\) === 'right'[\s\S]*?mcr-time-machine-restore[\s\S]*?mcr-time-machine-time/)
  assert.match(page, /mcr-time-machine-time[\s\S]*?historyRecordSide\(group\.key\) === 'left'/)
  assert.match(expansionLayer, /width:236px/)
  assert.match(page, /mcr-history-mode-button--active[\s\S]*?background: var\(--color-primary\)/)
})

test('image and text layers expose film grain and clip blur to the source alpha', () => {
  assert.match(layoutEditor, /label="胶片颗粒"/)
  assert.match(svgTemplate, /feComposite in="blurred" in2="SourceAlpha" operator="in"/)
  assert.match(svgTemplate, /feTurbulence/)
})

test('background participates in z-order and gradients support transparent endpoints', () => {
  assert.match(layoutEditor, /label="背景层级"/)
  assert.match(layoutEditor, /label="渐变起点透明度"/)
  assert.match(layoutEditor, /label="渐变终点透明度"/)
  assert.match(layoutEditor, /label="渐变方向"/)
  assert.match(svgTemplate, /gradientStartOpacity/)
  assert.match(svgTemplate, /gradientEndOpacity/)
  assert.match(svgTemplate, /reverse-diagonal/)
})

test('mobile timeline alternates around the axis and selected covers expose a draggable toolbar', () => {
  assert.match(page, /grid-template-areas:\s*"poster axis meta"/)
  assert.match(page, /is-right \{ grid-template-areas: "meta axis poster"; \}/)
  assert.match(page, /startHistoryToolbarDrag/)
  assert.match(page, /setPointerCapture/)
  assert.match(page, /safe-area-inset-bottom/)
  assert.match(page, /top: 'auto',[\s\S]*?safe-area-inset-bottom/)
  assert.match(page, /mcr-history-floating-header[\s\S]*?mcr-history-floating-drag-handle/)
  assert.match(page, /mcr-history-floating-row--actions[\s\S]*?>应用<[\s\S]*?mcr-history-floating-row--downloads/)
  assert.match(page, /grid-template-columns: repeat\(3, minmax\(0, 1fr\)\)/)
  assert.match(page, /mcr-history-floating-row--downloads[\s\S]*?grid-template-columns: repeat\(2, minmax\(0, 1fr\)\)/)
  assert.match(page, /plugin\/MediaCoverGenerator\/restore_history_covers/)
})

test('media count badge is available in the persistent layout editor', () => {
  assert.match(layoutEditor, /添加角标/)
  assert.match(layoutEditor, /媒体数量角标/)
  assert.match(customLayout, /createBadgeLayer/)
  assert.match(svgTemplate, /library_item_count/)
  assert.match(layoutEditor, /统计口径/)
  assert.match(layoutEditor, /集数（剧集按集，电影按部）/)
  assert.match(layoutEditor, /整部影视（剧集整部，电影按部）/)
  assert.match(layoutEditor, /按季影视（剧集按季，电影按部）/)
  assert.match(svgTemplate, /library_item_counts/)
  assert.match(contentCache, /libraryItemCount/)
  assert.match(contentCache, /libraryItemCounts/)
  assert.match(contentCache, /library_item_count: record\.libraryItemCount/)
  assert.match(contentCache, /library_item_counts: record\.libraryItemCounts/)
})

test('application chrome uses the shared subsetted chaohei face with a compact scroll header', () => {
  assert.match(page, /getTemplateFontFaceName\('app_chaohei'\)/)
  assert.doesNotMatch(page, /getTemplateFontFaceName\('app_impact'\)/)
  assert.match(page, /loadPageHeaderFonts\(\)/)
  assert.match(page, /\/api\/fonts\/faces/)
  assert.match(page, /<Teleport to="body">/)
  assert.match(page, /yh-compact-page-header/)
  assert.match(page, /updateCompactHeader\(\)/)
  assert.match(config, /\/api\/fonts\/faces/)
  assert.match(config, /getTemplateFontFaceName\('app_chaohei'\)/)
  assert.doesNotMatch(config, /getTemplateFontFaceName\('app_impact'\)/)
  assert.match(config, /yh-compact-config-header/)
})

test('mobile wordmark keeps readable chaohei tracking and line boxes', () => {
  assert.match(page, /letter-spacing: -0\.018em !important/)
  assert.match(page, /line-height: 1\.04 !important/)
  assert.match(page, /font-kerning: normal/)
})

test('header title contrast stays crisp while mobile English remains decorative', () => {
  assert.match(page, /color: #495267 !important;/)
  assert.match(page, /color: #c5c9cc !important;/)
  assert.match(page, /rgba\(83, 125, 198, 0\.065\)/)
  assert.match(page, /rgba\(244, 247, 251, 0\.025\)/)
  assert.match(config, /color: #495267 !important;/)
  assert.match(config, /color: #c5c9cc !important;/)
  assert.match(config, /mcr-config-switch-col[\s\S]*?align-items: center/)
})

test('compact headers bind to their real scroll root and use shared motion tokens', () => {
  assert.match(compactHeaderScrollRoot, /resolveCompactHeaderScrollRoot/)
  assert.match(compactHeaderScrollRoot, /scrollRoot\.addEventListener\('scroll', scheduleUpdate/)
  assert.match(compactHeaderScrollRoot, /window\.addEventListener\('scroll', scheduleUpdate, \{ passive: true \}\)/)
  assert.match(compactHeaderScrollRoot, /window\.addEventListener\('scroll', scheduleUpdate, \{ capture: true, passive: true \}\)/)
  assert.match(compactHeaderScrollRoot, /new ResizeObserver\(scheduleUpdate\)/)
  assert.match(page, /createCompactHeaderScrollController\(\(\) => pageHeroEl\.value, updateCompactHeader\)/)
  assert.match(config, /createCompactHeaderScrollController\(\(\) => configTopbarEl\.value, updateConfigHeaderCompact\)/)
  assert.match(applePolish, /--yh-motion-enter: cubic-bezier\(0\.23, 1, 0\.32, 1\)/)
  assert.match(applePolish, /--yh-motion-standard: 220ms/)
  assert.match(page, /width: 88px !important;[\s\S]*?--yh-motion-enter/)
  assert.match(config, /width: 88px;[\s\S]*?--yh-motion-enter/)
})

test('generation action morphs between a bordered play control and progress stop control', () => {
  assert.match(page, /isGenerating \? 'mdi-stop' : 'mdi-play'/)
  assert.match(page, /width: 112px !important/)
  assert.match(page, /border: 1px solid var\(--yahaha-border\) !important/)
  assert.match(config, /isGenerating \? 'mdi-stop' : 'mdi-play'/)
  assert.match(config, /width: 112px !important/)
  assert.match(config, /border: 1px solid var\(--yahaha-border\) !important/)
})
