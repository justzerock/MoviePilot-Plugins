import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const page = readFileSync(new URL('../src/components/Page.vue', import.meta.url), 'utf8')
const navigation = readFileSync(new URL('../src/components/SettingsAnchorNav.vue', import.meta.url), 'utf8')
const posterStack = readFileSync(new URL('../src/components/HistoryPosterStack.vue', import.meta.url), 'utf8')
const expansionLayer = readFileSync(new URL('../src/components/HistoryExpansionLayer.vue', import.meta.url), 'utf8')
const contentCache = readFileSync(new URL('../src/services/contentCache.ts', import.meta.url), 'utf8')

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
  assert.match(expansionLayer, /<Teleport to="body">/)
  assert.match(expansionLayer, /position:\s*fixed;\s*inset:\s*0/)
  assert.doesNotMatch(expansionLayer, /<v-dialog/)
  assert.doesNotMatch(expansionLayer, /grid-column:\s*1\s*\/\s*-1/)
})

test('settings navigation resolves one real scroll root and is not mounted on mobile', () => {
  assert.match(navigation, /v-if="navigationEnabled"/)
  assert.match(navigation, /function resolveScrollRoot\(\)/)
  assert.match(navigation, /scrollRoot \? scrollRoot\.scrollTop : window\.scrollY/)
  assert.match(navigation, /root: scrollRoot/)
  assert.doesNotMatch(navigation, /scrollIntoView/)
  assert.doesNotMatch(navigation, /window\.scrollY \+ scrollRoot\.scrollTop/)
})

test('history cache strips Vue proxies before IndexedDB persistence', () => {
  assert.match(contentCache, /HISTORY_CACHE_SCHEMA = 2/)
  assert.match(contentCache, /const persistedPayload = toJsonValue\(payload\)/)
  assert.doesNotMatch(contentCache, /lastUsedAt: now, payload \}/)
})

test('preview cache refreshes font metadata after subset generation', () => {
  assert.match(contentCache, /PREVIEW_CACHE_SCHEMA = 7/)
  assert.match(contentCache, /face\.subsetStatus === 'pending' \|\| face\.subsetStatus === 'building'/)
})
