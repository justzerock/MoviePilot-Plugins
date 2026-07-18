import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const page = readFileSync(new URL('../src/components/Page.vue', import.meta.url), 'utf8')
const config = readFileSync(new URL('../src/components/Config.vue', import.meta.url), 'utf8')
const navigation = readFileSync(new URL('../src/components/SettingsAnchorNav.vue', import.meta.url), 'utf8')
const posterStack = readFileSync(new URL('../src/components/HistoryPosterStack.vue', import.meta.url), 'utf8')
const expansionLayer = readFileSync(new URL('../src/components/HistoryExpansionLayer.vue', import.meta.url), 'utf8')
const dateTime = readFileSync(new URL('../src/utils/dateTime.ts', import.meta.url), 'utf8')
const contentCache = readFileSync(new URL('../src/services/contentCache.ts', import.meta.url), 'utf8')
const pluginBackend = readFileSync(new URL('../../plugins.v2/yahahacoverstudio/__init__.py', import.meta.url), 'utf8')
const pluginRenderer = readFileSync(new URL('../../plugins.v2/yahahacoverstudio/template_renderer.py', import.meta.url), 'utf8')
const layoutEditor = readFileSync(new URL('../src/components/CustomLayoutEditor.vue', import.meta.url), 'utf8')
const svgTemplate = readFileSync(new URL('../src/utils/svgTemplate.ts', import.meta.url), 'utf8')
const customLayout = readFileSync(new URL('../src/utils/customLayout.ts', import.meta.url), 'utf8')
const templateSchema = readFileSync(new URL('../src/utils/templateSchema.ts', import.meta.url), 'utf8')

test('history defaults to the time-machine view and expands in place', () => {
  assert.match(page, /historyGroupMode = ref<'library' \| 'time-machine'>\('time-machine'\)/)
  assert.match(page, /<HistoryPosterStack/)
  assert.doesNotMatch(page, /historySnapshotDialog/)
  assert.doesNotMatch(posterStack, /<v-dialog/)
})

test('history posters use stable keys and preserve a two-column mobile grid', () => {
  assert.match(posterStack, /item\.cover_id \|\| item\.history_record_id \|\| item\.library_key \|\| item\.path/)
  assert.doesNotMatch(posterStack, /:key="index"/)
  assert.match(posterStack, /grid-template-columns: repeat\(2, minmax\(0, 1fr\)\)/)
  assert.match(page, /\.mcr-history-groups--library \{[\s\S]*?flex-wrap: wrap/)
  assert.match(page, /flex-basis: calc\(\(100% - 9px\) \/ 2\)/)
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

test('collapsed preview count is independent from the real cover total', () => {
  assert.match(posterStack, /\{\{ items\.length \}\} 张/)
  assert.match(posterStack, /index >= stackLimit/)
  assert.match(posterStack, /\+\{\{ items\.length - stackLimit \}\}/)
  assert.doesNotMatch(posterStack, /Math\.min\([^)]*3/)
})

test('history expansion is one fixed page layer and never a dialog or grid reflow', () => {
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

test('settings navigation resolves one real scroll root and is not mounted on mobile', () => {
  assert.match(navigation, /v-if="navigationEnabled"/)
  assert.match(navigation, /function resolveScrollRoot\(\)/)
  assert.match(navigation, /closest<HTMLElement>\('\.mcr-config-app, \.mcr-frame'\)/)
  assert.match(navigation, /const minLeft = Math\.max\(viewportPadding, \(hostRect\?\.left \?\? 0\) \+ 8\)/)
  assert.match(navigation, /scrollRoot \? scrollRoot\.scrollTop : window\.scrollY/)
  assert.match(navigation, /root: scrollRoot/)
  assert.match(navigation, /props\.contentElement\?\.querySelector<HTMLElement>/)
  assert.match(navigation, /@pointerdown\.prevent/)
  const scrollHandler = navigation.match(/function scrollToSection\(id: string\) \{([\s\S]*?)\n\}/)?.[1] || ''
  assert.match(scrollHandler, /if \(scrollRoot && !scrollRoot\.isConnected\)/)
  assert.doesNotMatch(navigation, /scrollIntoView/)
  assert.doesNotMatch(navigation, /window\.scrollY \+ scrollRoot\.scrollTop/)
})

test('loading title breathes with opacity only', () => {
  const keyframes = page.match(/@keyframes yh-title-breathe \{([\s\S]*?)\n\}/)?.[1] || ''
  assert.match(keyframes, /opacity/)
  assert.doesNotMatch(keyframes, /scale|transform/)
  assert.match(page, /will-change: opacity/)
})

test('configuration controls stay compact and generation progress belongs to the run button', () => {
  assert.match(config, /class="mcr-config-scheme-rule__fields"/)
  assert.match(config, /class="mcr-config-scheme-rule__remove"/)
  assert.match(config, /class="mcr-font-switch-card"/)
  assert.match(config, /configGenerationProgressCount/)
  assert.match(page, /generationProgressCount/)
  assert.doesNotMatch(page, /backendBusyLabel/)
  assert.doesNotMatch(page, /<AsyncStatusDots v-if="backendBusy"/)
})

test('plugin status exposes all libraries while selected servers still limit generation', () => {
  assert.match(pluginBackend, /all_servers = self\.mediaserver_helper\.get_services\(\) or \{\}/)
  assert.match(pluginBackend, /for server, service in all_servers\.items\(\):/)
  assert.match(pluginBackend, /self\._servers = servers/)
  assert.match(pluginBackend, /self\._all_libraries = all_libraries/)
})

test('history cache strips Vue proxies before IndexedDB persistence', () => {
  assert.match(contentCache, /HISTORY_CACHE_SCHEMA = 2/)
  assert.match(contentCache, /const persistedPayload = toJsonValue\(payload\)/)
  assert.doesNotMatch(contentCache, /lastUsedAt: now, payload \}/)
})

test('preview cache refreshes font metadata after subset generation', () => {
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
  assert.match(pluginBackend, /"grain": normalized\.get\("grain", 0\)/)
})

test('background participates in z-order and gradients support transparent endpoints', () => {
  assert.match(layoutEditor, /label="背景层级"/)
  assert.match(layoutEditor, /label="渐变起点透明度"/)
  assert.match(layoutEditor, /label="渐变终点透明度"/)
  assert.match(layoutEditor, /label="渐变方向"/)
  assert.match(svgTemplate, /gradientStartOpacity/)
  assert.match(svgTemplate, /gradientEndOpacity/)
  assert.match(svgTemplate, /reverse-diagonal/)
  assert.match(svgTemplate, /underBackgroundLayers[\s\S]*?\$\{background\}[\s\S]*?overBackgroundLayers/)
  assert.match(pluginRenderer, /gradientStartOpacity/)
  assert.match(pluginRenderer, /gradientEndOpacity/)
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
  assert.match(page, /plugin\/YahahaCoverStudio\/restore_history_covers/)
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

test('badge layers retain their semantic type and count controls through persistence', () => {
  assert.match(customLayout, /type: 'badge'/)
  assert.match(customLayout, /countMode: \(layer as CustomBadgeLayer\)\.countMode \?\? 'episodes'/)
  assert.match(templateSchema, /normalizedType === 'image'[\s\S]*?assetKind:/)
  assert.match(templateSchema, /normalizedType === 'badge'[\s\S]*?countMode:/)
  assert.match(layoutEditor, /角标: \$\{getLayerPreviewText\(layer\)/)
  assert.match(layoutEditor, /if \(isBadgeLayer\(layer\)\) \{\s*return 'mdi-label-percent-outline'/)
  assert.match(pluginBackend, /A badge is text with count metadata, never an image slot\./)
  assert.match(pluginBackend, /normalized\["countMode"\] = count_mode if count_mode in \("episodes", "titles", "seasons"\) else "episodes"/)
})

test('application chrome uses subsetted chaohei and impact fonts with a compact scroll header', () => {
  assert.match(page, /getTemplateFontFaceName\('app_chaohei'\)/)
  assert.match(page, /getTemplateFontFaceName\('app_impact'\)/)
  assert.match(page, /loadPageHeaderFonts\(\)/)
  assert.match(page, /plugin\/YahahaCoverStudio\/fonts\/faces/)
  assert.match(page, /<Teleport to="body">/)
  assert.match(page, /yh-compact-page-header/)
  assert.match(page, /updateCompactHeader\(\)/)
  assert.match(config, /plugin\/YahahaCoverStudio\/fonts\/faces/)
  assert.match(config, /getTemplateFontFaceName\('app_chaohei'\)/)
  assert.match(config, /getTemplateFontFaceName\('app_impact'\)/)
  assert.match(config, /yh-compact-config-header/)
})

test('generation action morphs between a bordered play control and progress stop control', () => {
  assert.match(page, /isGenerating \? 'mdi-stop' : 'mdi-play'/)
  assert.match(page, /width: 112px !important/)
  assert.match(page, /border: 1px solid var\(--yahaha-border\) !important/)
  assert.match(config, /isGenerating \? 'mdi-stop' : 'mdi-play'/)
  assert.match(config, /width: 112px !important/)
  assert.match(config, /border: 1px solid var\(--yahaha-border\) !important/)
})
