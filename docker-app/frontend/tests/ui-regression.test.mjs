import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const page = readFileSync(new URL('../src/components/Page.vue', import.meta.url), 'utf8')
const navigation = readFileSync(new URL('../src/components/SettingsAnchorNav.vue', import.meta.url), 'utf8')
const posterStack = readFileSync(new URL('../src/components/HistoryPosterStack.vue', import.meta.url), 'utf8')
const expansionLayer = readFileSync(new URL('../src/components/HistoryExpansionLayer.vue', import.meta.url), 'utf8')
const contentCache = readFileSync(new URL('../src/services/contentCache.ts', import.meta.url), 'utf8')

test('history starts in the time-machine view', () => {
  assert.match(page, /historyGroupMode = ref<'library' \| 'time-machine'>\('time-machine'\)/)
})

test('time-machine uses a central alternating axis with stable sides', () => {
  assert.match(page, /grid-template-areas: "poster axis meta"/)
  assert.match(page, /is-right \{ grid-template-areas: "meta axis poster"/)
  assert.match(page, /historyRecordSides\.has\(group\.key\)/)
  assert.match(page, /neighborSide === 'left' \? 'right' : 'left'/)
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
  assert.match(expansionLayer, /<Teleport to="body">/)
  assert.match(expansionLayer, /position:\s*fixed;\s*inset:\s*0/)
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
  assert.match(navigation, /root: scrollRoot/)
  assert.doesNotMatch(navigation, /scrollIntoView/)
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
