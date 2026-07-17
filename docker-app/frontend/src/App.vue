<template>
  <v-app>
    <v-main>
      <div v-if="authState === 'loading'" class="yh-auth-loading" aria-label="正在检查登录状态">
        <v-progress-circular indeterminate color="primary" size="28" width="3" />
      </div>
      <AuthGate
        v-else-if="authState !== 'ready'"
        :mode="authState"
        @authenticated="onAuthenticated"
      />
      <Config
        v-else-if="view === 'config'"
        :api="dockerApi"
        :initial-config="initialConfig"
        @switch="view = 'page'"
        @save="onConfigSaved"
      />
      <Page
        v-else
        :api="dockerApi"
        @switch="showConfig"
        @action="onGenerated"
      />
      <v-btn
        v-if="authState === 'ready'"
        class="yh-logout-button"
        icon
        size="small"
        title="退出登录"
        aria-label="退出登录"
        @click="signOut"
      >
        <v-icon icon="mdi-logout" size="19" />
      </v-btn>
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import Config from './components/Config.vue'
import Page from './components/Page.vue'
import AuthGate from './components/AuthGate.vue'
import type { MediaCoverGeneratorConfig } from './types/plugin'
import { dockerApi, loadAuthStatus, loadDockerConfig, logoutDocker } from './dockerApi'

const view = ref<'page' | 'config'>('page')
const initialConfig = ref<Partial<MediaCoverGeneratorConfig>>({})
const authState = ref<'loading' | 'setup' | 'login' | 'ready'>('loading')

async function refreshConfig() {
  initialConfig.value = await loadDockerConfig()
}

async function onConfigSaved(config: MediaCoverGeneratorConfig) {
  initialConfig.value = config
}

async function onGenerated() {
  await refreshConfig()
}

async function showConfig() {
  await refreshConfig()
  view.value = 'config'
}

async function onAuthenticated() {
  authState.value = 'ready'
  await refreshConfig()
}

async function bootstrapAuth() {
  try {
    const status = await loadAuthStatus()
    authState.value = status.authenticated ? 'ready' : (status.configured ? 'login' : 'setup')
    if (status.authenticated) await refreshConfig()
  } catch {
    authState.value = 'login'
  }
}

function requireLogin() {
  authState.value = 'login'
  initialConfig.value = {}
}

async function signOut() {
  await logoutDocker()
  requireLogin()
}

onMounted(() => {
  window.addEventListener('yahaha-auth-required', requireLogin)
  void bootstrapAuth()
})

onBeforeUnmount(() => window.removeEventListener('yahaha-auth-required', requireLogin))
</script>

<style scoped>
.yh-auth-loading { min-height: 100dvh; display: grid; place-items: center; background: var(--color-bg, #f7f9fc); }
.yh-logout-button {
  position: fixed; right: 14px; bottom: 14px; z-index: 80;
  color: var(--color-text-secondary, #53627d) !important;
  background: color-mix(in srgb, var(--color-surface, #fff) 90%, transparent) !important;
  border: 1px solid var(--color-border, #dfe8f6) !important;
  box-shadow: 0 5px 16px var(--color-shadow, rgba(47, 76, 128, 0.1)) !important;
  backdrop-filter: blur(12px);
}
</style>
