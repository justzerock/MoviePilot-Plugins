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
  assert.match(config, /class="yh-scheme-assignment__fields"/)
  assert.match(config, /class="yh-scheme-assignment__remove"/)
  assert.match(config, /class="mcr-font-switch-card"/)
  assert.match(config, /configGenerationProgressCount/)
  assert.match(page, /generationProgressCount/)
  assert.doesNotMatch(page, /backendBusyLabel/)
  assert.doesNotMatch(page, /<AsyncStatusDots v-if="backendBusy"/)
})

test('history cache persists an explicit plain-data snapshot', () => {
  assert.match(contentCache, /HISTORY_CACHE_SCHEMA = 2/)
  assert.match(contentCache, /const persistedPayload = toJsonValue\(payload\)/)
  assert.doesNotMatch(contentCache, /lastUsedAt: now, payload \}/)
})

test('preview cache never pins a font while its subset is still building', () => {
  assert.match(contentCache, /PREVIEW_CACHE_SCHEMA = 7/)
  assert.match(contentCache, /face\.subsetStatus === 'pending' \|\| face\.subsetStatus === 'building'/)
})
