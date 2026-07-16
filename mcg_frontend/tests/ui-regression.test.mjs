import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const page = readFileSync(new URL('../src/components/Page.vue', import.meta.url), 'utf8')
const navigation = readFileSync(new URL('../src/components/SettingsAnchorNav.vue', import.meta.url), 'utf8')
const posterStack = readFileSync(new URL('../src/components/HistoryPosterStack.vue', import.meta.url), 'utf8')

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
  assert.match(page, /\.mcr-history-groups--library \{[\s\S]*?grid-template-columns: repeat\(2, minmax\(0, 1fr\)\)/)
})

test('settings navigation resolves one real scroll root and is not mounted on mobile', () => {
  assert.match(navigation, /v-if="navigationEnabled"/)
  assert.match(navigation, /function resolveScrollRoot\(\)/)
  assert.match(navigation, /scrollRoot \? scrollRoot\.scrollTop : window\.scrollY/)
  assert.match(navigation, /root: scrollRoot/)
  assert.doesNotMatch(navigation, /scrollIntoView/)
  assert.doesNotMatch(navigation, /window\.scrollY \+ scrollRoot\.scrollTop/)
})
