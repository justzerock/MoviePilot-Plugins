import { createApp, h } from 'vue'
import { createPinia } from 'pinia'
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as vuetifyComponents from 'vuetify/components'
import * as vuetifyDirectives from 'vuetify/directives'
import { VIcon, VSvgIcon } from 'vuetify/components'
import * as mdiPaths from '@mdi/js'
import { aliases, mdi } from 'vuetify/iconsets/mdi-svg'
import App from './App.vue'
import './styles/figmaTheme.css'

const mdiPathMap = mdiPaths as Record<string, string>
const iconAliases = aliases as Record<string, unknown>

function mdiNameToExportName(icon: string) {
  return icon
    .replace(/^mdi-/, 'mdi-')
    .split('-')
    .map((part, index) => (index === 0 ? part : `${part.charAt(0).toUpperCase()}${part.slice(1)}`))
    .join('')
}

function resolveMdiIcon(icon: unknown) {
  if (typeof icon !== 'string') return icon
  if (icon.startsWith('$')) {
    const alias = iconAliases[icon.slice(1)]
    return alias || icon
  }
  if (icon.startsWith('mdi-')) {
    return mdiPathMap[mdiNameToExportName(icon)] || icon
  }
  return iconAliases[icon] || mdiPathMap[mdiNameToExportName(`mdi-${icon}`)] || icon
}

const standaloneMdi = {
  ...mdi,
  component: (props: Record<string, unknown>) => h(VSvgIcon, { ...props, icon: resolveMdiIcon(props.icon) }),
}

const vuetify = createVuetify({
  components: vuetifyComponents,
  directives: vuetifyDirectives,
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: { mdi: standaloneMdi },
  },
})

createApp(App)
  .component('VIcon', VIcon)
  .use(createPinia())
  .use(vuetify)
  .mount('#app')
