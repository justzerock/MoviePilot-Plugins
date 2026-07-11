<template>
  <v-app>
    <v-main>
      <Config
        v-if="view === 'config'"
        :api="dockerApi"
        :initial-config="initialConfig"
        @switch="view = 'page'"
        @save="onConfigSaved"
      />
      <Page
        v-else
        :api="dockerApi"
        @switch="view = 'config'"
        @action="onGenerated"
      />
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Config from './components/Config.vue'
import Page from './components/Page.vue'
import type { MediaCoverGeneratorConfig } from './types/plugin'
import { dockerApi, loadDockerConfig } from './dockerApi'

const view = ref<'page' | 'config'>('page')
const initialConfig = ref<Partial<MediaCoverGeneratorConfig>>({})

async function refreshConfig() {
  initialConfig.value = await loadDockerConfig()
}

async function onConfigSaved(config: MediaCoverGeneratorConfig) {
  initialConfig.value = config
}

async function onGenerated() {
  await refreshConfig()
}

onMounted(() => {
  void refreshConfig()
})
</script>
