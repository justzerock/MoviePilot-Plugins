<template>
  <v-app>
    <v-main>
      <Page :api="mockApi" @action="onAction" @switch="onSwitch" @close="onClose" />
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import Page from './components/Page.vue'

const mockApi = {
  get: async (path: string, params?: any) => {
    console.log('mock get', path, params)
    return {}
  },
  post: async (path: string, data?: any) => {
    console.log('mock post', path, data)
    return { code: 0 }
  },
}

function onAction() {
  console.log('action emitted')
}
function onSwitch() {
  console.log('switch emitted')
}
function onClose() {
  console.log('close emitted')
}
</script>
