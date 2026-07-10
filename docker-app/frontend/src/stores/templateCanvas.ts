import { createPinia, defineStore, setActivePinia } from 'pinia'

const pinia = createPinia()
setActivePinia(pinia)

export const useTemplateCanvasStore = defineStore('mcr-template-canvas', {
  state: () => ({
    selectedLayerId: null as string | null,
  }),
  actions: {
    selectLayer(id: string | null) {
      this.selectedLayerId = id
    },
    resetSelection() {
      this.selectedLayerId = null
    },
  },
})
